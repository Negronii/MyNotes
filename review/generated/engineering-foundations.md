# Engineering Foundations

> Generated from the [engineering-foundations reading map](../../engineering-foundations/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. 两个请求争夺最后一件库存时，怎样保证只预留一次？

**案例：** 账户 acct-17 的请求要预留商品 SKU-7。数据库中 available = 1。浏览器携带稳定操作键 reserve-demo-208 发出请求；网络超时后，客户端不知道事务是否提交。正确边界是在数据库里同时检查库存、扣减一件并写入可查询的操作结果，让并发请求无法把数量扣成负数，也让同一操作键重放时能查回同一结果。

~~~mermaid
sequenceDiagram
    participant C as 调用方
    participant A as API
    participant D as 数据库
    C->>A: 预留 SKU-7，操作键 reserve-demo-208
    A->>A: 验证当前账户/主体与参数指纹
    A->>D: 快速查询同一作用域的操作键
    alt 已有记录且参数指纹相同
        D-->>A: 已提交预留结果
        A-->>C: 返回同一预留记录，不扣库存
    else 已有同键但参数指纹不同
        A-->>C: 返回操作键冲突
    else 当前快照没有可见记录，结果仍可能未知
        A->>D: 条件扣减，available 必须大于 0
        alt 条件更新恰好 1 行且插入键成功
            D-->>A: available = 0
            A->>D: 插入唯一的账户/主体/操作键记录
            A->>D: COMMIT
            D-->>A: 提交完成
            A--xC: 响应丢失，客户端结果未知
        else 更新 0 行或插入时作用域键唯一冲突
            A->>D: ROLLBACK 整个尝试
            A->>D: 新事务再次查询操作键与指纹
            alt 找到同键同指纹的已提交结果
                D-->>A: 返回已存在结果
                A-->>C: 返回同一预留记录，不扣库存
            else 找到同键但指纹不同
                A-->>C: 返回操作键冲突
            else 确认没有可重放记录
                A-->>C: SKU 不存在或已售罄
            end
        end
    end
~~~

### 为什么先读再无条件写会超卖？

如果应用先 SELECT available，再根据返回值计算 available - 1 并无条件更新，两个请求可能都读到 1，再分别把值写成 0；数据库最终只有一件被扣减，但两条业务记录都可能显示预留成功。读到的旧值没有保护写入条件。

把条件放进同一个更新语句，数据库才会在写入发生处判断库存是否仍大于零。先用小型数据库模式表示每个 SKU 的可用量，以及每个成功操作的唯一记录：

~~~sql
-- PostgreSQL 18 DDL
CREATE TABLE inventory (
    sku TEXT PRIMARY KEY NOT NULL,
    available INTEGER NOT NULL CHECK (available >= 0)
);

CREATE TABLE reservations (
    account_id TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    sku TEXT NOT NULL REFERENCES inventory(sku),
    status TEXT NOT NULL CHECK (status IN ('reserved', 'cancelled')),
    PRIMARY KEY (account_id, principal_id, idempotency_key)
);

INSERT INTO inventory VALUES ('SKU-7', 1);
~~~

复合主键保证同一账户、主体和幂等键最多一条操作记录；外键保证预留指向存在的 SKU；CHECK 与 NOT NULL 一起禁止负库存和未知库存。数据库约束如何对所有写入方生效，见[如何用约束保护业务规则并为读取建立索引？](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F)。

### 条件更新怎样让两个并发请求竞争？

以 PostgreSQL 18 的 Read Committed（读已提交）行为为例。请求 A 执行条件更新时拿到该行的写锁，把库存从 1 改为 0，但尚未提交；请求 B 在同一行上等待。A 提交后，B 会针对新版本重新判断 available > 0，条件不再成立，更新行数为 0。**这时不能立刻把 B 判成售罄：**它可能正是重放 reserve-demo-208 的同一逻辑操作。B 必须先回滚这次尝试，再在新事务中按当前账户和主体查询键、比较请求指纹：找到已提交的相同意图就返回同一预留记录及当前状态；同键不同指纹就返回冲突；确实没有该键时，零行才表示 SKU 不存在或已售罄。

同键请求即使先查过仍可能同时进入事务；查不到只表示当前快照没有已提交记录，不证明原请求已回滚。PostgreSQL Read Committed 下，同一 SKU 的条件更新会等待持锁者结束：前者提交后，后者若因库存变为 0 得到零行，就先回滚，再用新事务查结果；前者回滚时，后者可重新判断并继续。若库存大于 1，两笔同键请求都可能扣减成功，后插入的一方会撞上作用域唯一约束；PostgreSQL 中该错误使当前事务失败，必须回滚整笔扣减，再在新的事务读取胜者结果。只有确认没有同键可重放记录时，零行才表示 SKU 不存在或已售罄；请求指纹不同则返回冲突。不能只回滚 INSERT 后保留扣减。

以下 SQL 按 PostgreSQL 18 写法，$1 到 $5 是由驱动绑定的参数；它不是 SQLite 的问号占位符语法。应用先授权并核验/生成参数指纹，只有条件更新返回一行后才执行 INSERT：

~~~sql
BEGIN;

UPDATE inventory
SET available = available - 1
WHERE sku = $1 AND available > 0
RETURNING available;
-- 仅一行（本例 available = 0）才继续。

INSERT INTO reservations
    (account_id, principal_id, idempotency_key, request_fingerprint, sku, status)
VALUES ($2, $3, $4, $5, $1, 'reserved');

COMMIT;
~~~

**中间状态：** 初值是 SKU-7 → 1。A 更新一行，得到 available=0，插入 (acct-17, user-17, reserve-demo-208, fingerprint-A) 并提交。若 B 是同键同指纹的重放，A 提交后 B 得到更新零行，回滚并读取这条已提交记录，因此返回同一预留记录且不再扣库存。若 B 是不同操作键，它回滚后查不到自己的键，才报告售罄。若 B 同键却携带另一参数指纹，应返回冲突，不复用 A 的结果。

> [!info] 更新行数为什么是业务判断
> PostgreSQL 的 UPDATE ... WHERE available > 0 将“仍有库存”的条件放在扣减发生处。恰好一行才说明此次扣减成功；零行需要再检查幂等结果后才能确定是同键重放还是售罄；多行则表示 schema 没保证 SKU 唯一，数据模型应修正。本章 DDL 与占位符以 PostgreSQL 18 为准；若在 SQLite 另建对照表，需考虑其动态类型，并在每条连接启用 PRAGMA foreign_keys = ON；需要强类型约束时使用 STRICT 表或等效检查。

### 提交成功但响应超时，怎样认出原操作？

超时只代表调用方没有收到响应；它无法区分请求未到达、事务回滚、事务仍在进行，或提交后只有响应丢失。每次查询或重放前，服务都要再次校验当前账户和主体有权读取这条操作结果。事务提交后，数据库中库存为 0，且存在 reserve-demo-208 与请求指纹 fingerprint-A 绑定的预留记录。客户端使用同一个操作键查记录或按明确的幂等契约重放；API 比较账户、主体与请求指纹后返回已记录结果而不再次扣减。不能为重试生成新键，否则服务端会把它当成另一次购买。键的作用域、保留窗口与未知结果重试规则由[请求超时后如何确认结果并安全重试？](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)专门解释。

操作键记录必须和库存效果处于同一事务；若先扣库存并提交，之后再单独写操作键，二者之间崩溃仍可能造成“效果已发生但重试认不出”。支付服务或消息队列不在这个本地事务中，不能靠 SQL COMMIT 宣称远端副作用也完成。账户报表的数据库到队列边界会用 transactional outbox（事务型发件箱）延伸这一问题，见[怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 同一库存不变量怎样用于抽奖？

抽奖服务对外提供公开只读的 GET /draws/{campaignId}，返回活动规则、时间与可见状态；已认证参与者以 POST /draws/{campaignId}/entries 提交自己的请求。服务端按当前主体检查活动仍开放、资格和一次参与规则，并使用 (campaign_id, principal_id) 唯一约束及作用域幂等键阻止重复参与。活动已关闭应返回明确 campaign-closed 状态；已有参与记录或其他规则冲突应返回明确 conflict，不让浏览器从通用错误猜结果。抽奖随机性和审计规则须符合活动承诺；统计事件不能决定资格或权威中奖结果。

有限奖品应在同一事务里条件扣减并保存参与、抽取结果与待领取状态；若扣减零行，要按活动规则明确返回库存已用完/未中奖等业务结果，不能假定数据库自动替用户重新抽取。GET /draws/{campaignId}/entries/{entryId} 只能向当前结果所有者返回本人结果与领取状态；单独的 POST /prizes/{prizeId}/claims 再验证中奖记录所有者，只收集履约所需资料并写入履约状态。后台活动管理权限应比公开读取和本人参与更严格。抽奖提交也需使用稳定操作键，并按幂等契约定义保留窗口与重放结果，避免超时后重复参与；通用规则见[请求超时后如何确认结果并安全重试？](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。原档案的独特接口流、显式关闭/冲突结果和权限分层已迁入本节；旧入口保留导航，见[归档抽奖 API 规则入口](../../archive/front-end/Deprecated_Interview_Notes/prize-draw-api-invariants.md)。

**接下来：** 此处只说明原子库存写入及本地约束。NULL、连接和分组改变报表查询的方式见[NULL、连接与分组如何改变报表 42 的结果？](#7.%20SQL%20%E7%A9%BA%E5%80%BC%E3%80%81%E8%BF%9E%E6%8E%A5%E4%B8%8E%E5%88%86%E7%BB%84%E4%BC%9A%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E6%8A%A5%E8%A1%A8%2042%20%E7%9A%84%E7%BB%93%E6%9E%9C%EF%BC%9F)；事务隔离、WAL 和崩溃恢复的保证见[事务隔离与 WAL 能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - 条件扣减的并发重检与事务隔离行为：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1，核对于 2026-11-06；此处并发时序明确标为 PostgreSQL 行为。
> - 主键、唯一、外键、CHECK 和 NOT NULL 的持久约束：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)，§5.5，核对于 2026-11-06。
> - SQLite 事务和外键约束：[SQLite Transactions](https://www.sqlite.org/lang_transaction.html) 与 [Foreign Key Support](https://www.sqlite.org/foreignkeys.html)，核对于 2026-11-06。
## 2. 浏览器请求如何到达 HTTP 响应？

Hypertext Transfer Protocol (HTTP，超文本传输协议) 规定调用方怎样描述操作、服务端怎样返回状态与表示；Transmission Control Protocol (TCP，传输控制协议) 或 QUIC 负责承载字节流，Transport Layer Security (TLS，传输层安全协议) 在安全连接上保护通信。看同一个报表请求，应先认清 HTTP 语义，再按是否有可复用缓存、地址和连接追踪网络阶段。HTTP 版本会改变连接复用和多路复用方式，但不会替 application programming interface (API，应用程序接口) 验证身份、授权资源、允许跨源读取或确认超时操作结果。

**案例：** 查看者已登录并获准读取报表 42。此前浏览器收到 `200` JSON、`ETag: "report-42-v8"` 和 `Cache-Control: private, no-cache`，并把该表示保存在自己的私有缓存。用户再次打开页面时，浏览器用旧验证值询问当前表示。图中的某些阶段会因 Service Worker、缓存、DNS 地址或已有连接而跳过；持续更新则需要独立的消息与恢复契约，见[何时选择轮询、SSE、流式 Fetch 或 WebSocket？](#15.%20%E4%BD%95%E6%97%B6%E9%80%89%E6%8B%A9%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)。

~~~mermaid
flowchart LR
    Click[打开报表 42] --> Browser[浏览器构造请求]
    Browser --> Cache{缓存可直接回答且无需源站验证？}
    Cache -->|是| Cached[交付缓存表示]
    Cache -->|否| Conn{有可复用连接？}
    Conn -->|有| HTTP[发送 HTTP 请求]
    Conn -->|没有| Address[使用地址缓存，或按需解析域名]
    Address --> Handshake[建立 TCP/TLS 或 QUIC 连接]
    Handshake --> HTTP
    HTTP --> App[路由、认证、授权与处理]
    App -->|权限拒绝| Deny[返回约定的 401、403 或隐藏式 404]
    App -->|权限允许| Result[返回 304 或新的 200 表示]
    Cached --> UI[浏览器交付表示给页面]
    Deny --> UI
    Result --> UI
~~~

### 一次请求和响应如何描述报表？

Uniform Resource Identifier (URI，统一资源标识符) 定位目标资源；方法表达操作；请求还可以有路径、查询参数、字段和消息体。响应给出状态、字段和表示（representation）。这里的“表示”是服务端选择的一种媒体类型与编码，不必等于数据库中的单行。

本次条件读取可写成：

~~~http
GET /api/reports/42 HTTP/1.1
Host: reports.example
Accept: application/json
Accept-Language: zh-CN, en;q=0.8
Cookie: __Host-session=<opaque-session-id>
If-None-Match: "report-42-v8"
~~~

浏览器曾缓存的响应是：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Language: zh-CN
ETag: "report-42-v8"
Cache-Control: private, no-cache

{"id":42,"title":"Service health","status":"ready","version":8}
~~~

`ETag` 是服务端为选中表示提供的验证值。当前权限仍允许读取、表示也未变化时，服务端可以只回答：

~~~http
HTTP/1.1 304 Not Modified
ETag: "report-42-v8"
Cache-Control: private, no-cache
~~~

若权限已撤销，服务端应按 API 的隐私政策返回 403 或隐藏式 404；若权限仍允许但表示变化，则返回新的 `200`、正文和 ETag。浏览器管理的 HTTP 缓存收到 304 后会把先前保存的正文与新验证信息组合；页面通常得到可用的 200 表示，而不是把空的 304 正文当报表内容。缓存验证不绕过认证与授权。

各字段职责不同：`Accept` 表示调用方偏好的响应媒体类型，`Content-Type` 描述消息体的媒体类型，`Content-Encoding` 描述表示经过的压缩等编码，`Accept-Language` 表示语言偏好而不保证服务一定有该语言，`Content-Language` 描述返回表示面向的语言。Cookie 与 `Authorization` 携带认证凭据；浏览器会自行管理 Cookie，脚本不能任意手设 `Cookie`。缓存验证器则由 `ETag` 与条件字段 `If-None-Match` 配合。

safe method (安全方法) 的预期语义是不要求改变目标资源状态；这不禁止日志、计数等附带效果。idempotent (幂等) 表示重复执行的预期效果等同执行一次，不要求响应字节相同：第一次 DELETE 可回 204，后续回 404，但资源仍保持不存在。PUT 让目标资源成为请求描述的状态，不必然表示没写的字段都会清空；PATCH 是否幂等取决于补丁操作和接口约定；POST 通常不具幂等性。方法语义不能独自说明连接中断后副作用是否已经提交；未知结果需用业务请求标识确认，见[请求超时后如何确认结果并安全重试？](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info] HTTP 与 REST 的关系
> Representational State Transfer (REST，表述性状态转移) 是一种架构风格，约束包括客户端与服务端分离、无状态交互、可缓存、统一接口和分层系统；代码按需下发是可选约束。统一接口进一步要求资源标识、以表示操纵资源、自描述消息及超媒体控制。使用 HTTP 方法和 JSON 不会自动满足所有 REST 约束；检查请求是否无状态、缓存是否遵循策略、表示和链接是否足以驱动交互，才是在讨论 REST 风格。参见 Fielding 的架构定义。

### 缓存策略怎样决定能否复用？

以下指令表达不同选择：`private` 允许浏览器私有缓存保存，但禁止共享缓存复用该响应；`max-age=60` 给出新鲜期，未过期时缓存可能直接复用而不联系源站；`no-cache` 允许存储，却要求每次复用前先向源站验证；`no-store` 要求缓存不要存储该交换。它们不替代访问控制，也不自动让私有响应与用户隔离。若权限可能在 60 秒内撤销，只靠 `private, max-age=60` 会允许浏览器在新鲜期内直接复用旧正文；要求再次确认授权时，可使用 revalidation（重新验证）策略，敏感内容也可用 `no-store`。

API 自己仍须为缓存键和验证器划定租户、主体、表示协商及语言范围。浏览器中的私有表示缓存与服务器端对象/租户授权是两层不同控制；见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

### 状态码说明什么？

HTTP 状态描述当前请求的处理结果类别，不描述调用方全部业务状态，也不表示中间每个网络环节都成功。

| 范围或状态 | 报表示例 | 含义边界 |
| --- | --- | --- |
| 1xx | 100 Continue | 继续处理的中间信息 |
| 2xx | 200 当前表示；201 已创建资源记录；202 已受理异步作业 | 202 不表示作业已完成 |
| 3xx | 304 Not Modified | 浏览器可复用已有的已验证表示 |
| 4xx | 400 格式错误；401 缺少有效凭据；403 拒绝；404 不存在或按政策隐藏；409 冲突；429 超过额度 | 发出 401 时必须包含适用的 `WWW-Authenticate` challenge；超时发生在客户端，不自动成为 HTTP 状态 |
| 5xx | 502 上游响应无效；503 暂时不能处理；504 等待上游超时 | 说明服务端/网关未完成当前请求 |

浏览器 `fetch()` 的 Promise 在收到 HTTP 响应后会兑现，即使状态是 404 或 500；脚本应检查 `response.ok` 或 `status`。响应头已到达不代表正文已经完整读完：`response.json()` 或流读取仍可能因连接断开、解码或读取错误而失败。Fetch 与其他客户端对 HTTP 错误的呈现也不同：Fetch 默认不会因为非 2xx 拒绝 Promise；Axios 默认把非 2xx 放入拒绝分支并把响应放在错误对象中，`validateStatus` 可改变该规则；XMLHttpRequest 的 `load` 表示收到响应，需自行检查状态，`error` 表示网络级失败，`upload.onprogress` 仍适合需要浏览器上传进度事件的界面。Axios 的 adapter 和版本会影响细节，旧项目可参考[归档 Axios 说明](../../archive/front-end/0-1_Learning_Notes/react_typescript/axios-in-react.md)。

### HTTP/1.1、HTTP/2 与 HTTP/3 如何共享连接？

HTTP 语义由 RFC 9110 定义，不同版本用不同线格式和传输承载。HTTP/1.1 报文可见起始行、字段、空行和可选消息体；HTTP/2、HTTP/3 把方法、字段和内容编码为帧及字段块，但调用方仍表达相同方法、目标与状态。

| 版本 | 连接和并发方式 | 丢包影响及边界 |
| --- | --- | --- |
| HTTP/1.1 | 默认可持久复用连接，浏览器也可并行打开多个连接；同一连接上的流水线响应仍按请求顺序返回 | 一个连接上前面的慢响应可能让后续响应等待；持久连接不表示服务器能在无请求时任意推送 HTTP 响应 |
| HTTP/2 | 多个 HTTP 流在一个 TCP 连接上以帧交错传输，并压缩字段 | TCP 提供有序字节流；早期 TCP 段丢失会暂缓该连接后续字节交付，因此多个流可能一起等候 |
| HTTP/3 | HTTP 流运行在 QUIC 上；QUIC 使用 UDP 承载，但自己提供可靠流、流控、拥塞控制和 TLS 1.3 握手 | 某个 QUIC 流缺失的数据通常不会阻止其他已齐全流的数据交付；它们仍共享连接级拥塞、流控和路径资源 |

例如图片所在 TCP 段丢失时，即使报表 JSON 的 HTTP/2 流后续字节已到，也要等待字节流缺口补齐；在 QUIC 下，若 JSON 流数据本身齐全且仍有连接资源，它可能先交付。HTTP/3 隔离了部分跨流传输等待，但并不消除共享拥塞造成的延迟，因此不能只从版本号推出固定性能收益。

TCP 是有序可靠字节流，不保留一次应用 `write` 对应一次 `read` 的消息边界。应用协议需另定长度前缀、分隔符或固定长度。所谓“粘包”通常是把字节流误当消息队列造成的解析错误。正常关闭还可分别结束两个方向；FIN/ACK 交换可能合并，不能说每次都固定四个报文。

### 域名解析、TCP 与 TLS 按什么顺序检查？

浏览器首次访问 `reports.example` 时，若缺少可复用连接，会先使用仍有效的本地 DNS 地址缓存；没有可用地址才向解析器查询。即使连接已关闭，DNS 地址仍可能在缓存有效期内。递归解析器也可能从缓存返回记录或沿域名委派查询。记录 TTL 限定缓存可保留时间；错误回答也可能被缓存。Service Worker、HTTP 缓存、地址缓存和连接复用是不同快路径。

TCP 建连常见三次握手：客户端发送 SYN 请求同步序号；服务端回 SYN-ACK 同意并给出自己的序号；客户端再回 ACK。它只描述 TCP 建连；QUIC 在 UDP 上进行自己的连接和 TLS 握手，不执行这组三报文交换。完整、普通的 TLS/QUIC 新连接会在应用数据前建立必要密钥与身份验证；TLS 1.3 会话恢复还可能启用 0-RTT early data，让客户端在握手完成前发送早期数据。早期数据可被重放，所以不能把它用于依赖“只执行一次”的副作用，除非应用有与重放边界相配的幂等或反重放设计。

因此排障时要分开确认：是否有地址缓存或 DNS 查询、TCP 三次握手或 QUIC 建连、常规 TLS 握手或恢复、证书与主机名验证、最后的 HTTP 请求和响应。网络连接或 TLS 错误不是 API 的 500。

> [!info] 预连接与预取提示
> `preload` 提示浏览器提前取当前页面已经确定要用的关键资源；`prefetch` 提示低优先级准备未来导航可能使用的资源；`preconnect` 可为很快要访问的可信来源准备连接；`dns-prefetch` 只预解析主机名。浏览器可以依据资源和连接条件忽略或调整这些提示。对当前已复用的主机，预连接通常没有额外效果；提前准备新的第三方来源会占用连接资源，须按实际需要选择。

~~~html
<link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>
<link rel="prefetch" href="/next-page.js">
<link rel="preconnect" href="https://reports-cdn.example">
~~~

**接下来：** 若页面与 API 不同源，浏览器何时允许脚本读取响应由[浏览器安全边界](#6.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AE%89%E5%85%A8%E6%8E%A7%E5%88%B6%E5%88%86%E5%88%AB%E4%BF%9D%E6%8A%A4%E4%BB%80%E4%B9%88%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C%EF%BC%9F)说明；若要连续接收报表更新，则选取[实时传输与恢复方式](#15.%20%E4%BD%95%E6%97%B6%E9%80%89%E6%8B%A9%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)。

> [!info]- 来源
> - HTTP 字段、方法安全性与幂等、状态码、URI、表示协商：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§6–§12、§15，2022-06；401 challenge 见 §15.5.2，核对于 2026-11-06。
> - 缓存新鲜度、`max-age`、`no-cache`、`no-store`、`private` 和条件请求：[IETF RFC 9111, HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)，§4–§5，2022-06；核对于 2026-11-06。
> - HTTP/1.1 报文与连接：[RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html)，§2、§9；HTTP/2 帧与流：[RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html)，§2、§5、§8；HTTP/3 映射：[RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)，§1–§4。均为 2022-06 标准，核对于 2026-11-06。
> - TCP 三次握手与连接状态：[RFC 9293, Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc9293.html)，§3、§3.5，2022-08；QUIC 流与拥塞：[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)，§2、§3、§13，2021-05；QUIC TLS：[RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html)，§4、§5、§9.2，2021-05；TLS 1.3：[RFC 8446](https://www.rfc-editor.org/rfc/rfc8446.html)，§2–§4，2018-08。均核对于 2026-11-06。
> - DNS 委派与缓存：[RFC 1034](https://www.rfc-editor.org/rfc/rfc1034.html)，§4–§5，1987-11；DNS 负缓存：[RFC 2308](https://www.rfc-editor.org/rfc/rfc2308.html)，§3–§5，1998-03。核对于 2026-11-06。
> - REST 架构风格的客户端-服务端、无状态、缓存、统一接口和分层约束：[Roy T. Fielding, Architectural Styles and the Design of Network-based Software Architectures](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，§5，2000。
> - Fetch 对脚本可设置请求字段和可见响应字段的限制：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/#forbidden-request-header)，Living Standard，核对于 2026-11-06；XHR 事件模型：[WHATWG XMLHttpRequest Standard](https://xhr.spec.whatwg.org/)，§3.5，核对于 2026-11-06；Axios 默认错误处理：[Axios error handling](https://axios-http.com/docs/handling_errors)，核对于 2026-11-06。
> - 资源提示类型：[WHATWG HTML Living Standard, Link types](https://html.spec.whatwg.org/multipage/links.html#linkTypes)，核对于 2026-11-06。
## 3. 如何设计可预期的 HTTP API 契约？

API 契约说明调用方怎样构造请求、怎样识别成功和失败、怎样继续读取集合。HTTP 提供通用方法和状态语义；API 定义领域输入、返回结构、错误类别、分页规则与兼容政策。文档、类型注解、OpenAPI 描述和运行中的实现是不同层：写出 schema（结构模式）不证明已部署行为符合它。

**案例：** 浏览器请求 `GET /api/reports/42`。报表存在且当前主体获准读取时，API 返回稳定 JSON；编号格式错误、报表不存在、认证缺失或访问被拒，各有调用方能识别的结果。列表按 ID 排序并显式给出下一页游标。

~~~http
GET /api/reports/42 HTTP/1.1
Host: reports.example
Accept: application/json, application/problem+json
~~~

一个合法的成功表示是：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json

{"id":42,"title":"Service health","status":"ready"}
~~~

路径里的 `42` 是 API 的资源标识，不是访问授权。边界先解析和校验输入，再由服务确认当前身份、租户和对象权限；之后才读取资源。资源归属见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

### 错误契约怎样保留机器可判定的含义？

API 可以用 RFC 9457 Problem Details 表示错误，媒体类型为 `application/problem+json`。例如 ID 不存在或按隐私政策不可见时返回统一错误：

~~~http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{"type":"https://api.example/problems/not-found","title":"Report not found","status":404,"detail":"No report is visible under this identifier."}
~~~

客户端可依赖稳定的 `type` 或扩展错误码，而不应解析供人阅读的 `title`、`detail`。若正文含 `status`，它须与实际 HTTP 状态相同。不要回显秘密、内部异常栈或 SQL 文本。

| 条件 | 本例的结果 | 补充约定 |
| --- | --- | --- |
| 报表 42 存在、身份和资源权限都通过 | 200 + JSON | 定义成功表示中的稳定字段 |
| 缺少有效凭据 | 401 + Problem Details | 发出 401 时提供适用的 `WWW-Authenticate` challenge；例如 Bearer API 返回 `Bearer realm="reports"` |
| 已认证但无权访问 | 403，或按隐藏政策返回与不存在相同的 404 | 隐藏策略下错误详情不能泄漏对象存在性 |
| JSON 语法无效，例如正文 `{` | 400 + Problem Details | 指明内容无法解析 |
| 语法有效但字段、路径参数或范围不符合契约 | 422 + Problem Details | 指出字段路径和稳定错误代码 |
| 与当前状态冲突，例如重复标题 | 409 + Problem Details | 告诉调用方怎样刷新或解决冲突 |
| 超过适用调用额度 | 429 + Problem Details | 定义额度作用域和可重试时机 |
| 报表 999 不存在或被隐藏 | 404 + Problem Details | 与成功表示结构不同 |

这是本 API 的映射政策，不是所有服务都必须采用的唯一表。`422 Unprocessable Content` 表示内容语法可理解但指令不能处理，因此本例把畸形 JSON 归为 400，把结构有效但字段不合规归为 422。认证/授权、结构校验和数据库并发不变量分别由不同边界负责。

### 201 创建资源和 202 接受作业有什么区别？

`POST /api/reports` 可创建一条报表资源记录，返回 `201 Created` 和 `Location: /api/reports/44`。如果新资源的 `status` 是 `queued`，201 表示资源记录已经建立，不表示报表成品已生成。若请求创建的是独立长作业而不是资源记录，API 可以返回 `202 Accepted` 与稳定的作业状态 URL；202 表示受理处理，不表示成功完成。客户端在连接断开后查状态资源，而不是从原响应推断完成。账户报表的持久 job、outbox 和队列确认见[怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 分页怎样给出明确结束条件？

集合可能很大或持续变化，契约须规定页大小、确定性排序和结束信号。本例默认 `limit=2`、最大 100，按 ID 升序；`next_cursor` 是必返回字段，最后一页明确返回 JSON `null`。

~~~http
GET /api/reports?limit=2 HTTP/1.1
Host: reports.example
Accept: application/json
~~~

~~~json
{"items":[{"id":41,"title":"Monthly overview","status":"ready"},{"id":42,"title":"Service health","status":"ready"}],"next_cursor":"opaque-token-A"}
~~~

客户端原样传回不透明游标：

~~~http
GET /api/reports?limit=2&cursor=opaque-token-A HTTP/1.1
Host: reports.example
Accept: application/json
~~~

~~~json
{"items":[{"id":43,"title":"Usage summary","status":"queued"}],"next_cursor":null}
~~~

第一页的 `[41, 42]` 续到 ID 42 之后，第二页的 `[43]` 以 `null` 明确结束；只有客户端看见该结束标记才停止。短页不总表示没有后续数据。游标不应暴露可篡改的数据库偏移量；生产集合可把游标绑定筛选条件、排序、授权范围和过期时间，并按 `(created_at, id)` 之类的稳定复合键续读。每页重新授权。并列时间戳时游标要同时保存两个排序键，数据变化时还要说明读者看到移动集合还是固定快照。

> [!example] 读完三条报表的分页回放
> 排序为 ID 升序、页大小为 2：第一批是 `[41, 42]`，游标代表“从 42 之后继续”；第二批是 `[43]`，返回 `next_cursor: null` 后停止。若服务器因资源上限只返回 1 项但仍有后续数据，只凭短页就停止会漏项。示例游标是占位显示；运行代码会生成不可预测的不透明 token。

### OpenAPI 怎样描述实际运行契约？

OpenAPI 记录操作路径、参数、媒体类型、成功与错误响应及 schema，使人和工具可据此调用服务。框架可从请求/响应模型生成结构；自定义异常处理器也要在相应操作里声明错误响应。只有运行时错误和 OpenAPI 都匹配，客户端才不会按一份服务实际不返回的契约生成分支。检查时要按操作核对真实路径、状态码、媒体类型、Problem `type`、分页字段是否必填以及 schema 是否允许 `null`。

下面的 FastAPI 复现定义裸应用前缀 `/api`，与本章请求路径一致。它用三条合成报表演示 200、404、字段验证、畸形 JSON、冲突、分页和 OpenAPI。为集中讲契约，它没有实现身份认证、租户授权或数据库并发唯一性；它不是可直接部署的安全报表服务。正常请求和失败的输入输出已在正文展示，无需运行这段代码才能理解契约。

> [!example]- 可运行的 FastAPI 契约复现
> 运行环境已核验：FastAPI 0.128.0、Pydantic 2.11.7、Starlette 0.47.2、httpx 0.28.1；本环境的 `app.openapi()` 生成 OpenAPI 3.1.0。OpenAPI 文档版本以运行时字段为准。
>
> ~~~python
> import secrets
> from typing import Any
>
> from fastapi import APIRouter, FastAPI, Query, Request, Response
> from fastapi.exceptions import RequestValidationError
> from fastapi.responses import JSONResponse
> from fastapi.testclient import TestClient
> from pydantic import BaseModel, Field, field_validator
>
> PROBLEM_BASE = "https://api.example/problems/"
>
>
> class CreateReport(BaseModel):
>     title: str = Field(min_length=1, max_length=60)
>
>     @field_validator("title", mode="before")
>     @classmethod
>     def normalize_title(cls, value: Any) -> Any:
>         if isinstance(value, str):
>             if len(value) > 60:  # 上限检查原始输入，再去除首尾空格
>                 raise ValueError("title must be at most 60 characters before trimming")
>             if not value.strip():
>                 raise ValueError("title must contain a non-whitespace character")
>             return value.strip()
>         return value
>
>
> class Report(BaseModel):
>     id: int
>     title: str
>     status: str
>
>
> class Page(BaseModel):
>     items: list[Report]
>     next_cursor: str | None  # required, but null on the last page
>
>
> class Problem(BaseModel):
>     type: str
>     title: str
>     status: int
>     detail: str
>     errors: list[dict[str, str]] | None = None
>
>
> class ApiProblem(Exception):
>     def __init__(self, status: int, kind: str, title: str, detail: str):
>         self.status, self.kind, self.title, self.detail = status, kind, title, detail
>
>
> def problem_content(description: str):
>     return {
>         "description": description,
>         "content": {
>             "application/problem+json": {"schema": Problem.model_json_schema()}
>         },
>     }
>
>
> LIST_ERRORS = {
>     400: problem_content("Unknown cursor"),
>     422: problem_content("Invalid query parameter"),
> }
> READ_ERRORS = {
>     404: problem_content("Report does not exist"),
>     422: problem_content("Report ID is not an integer"),
> }
> CREATE_ERRORS = {
>     400: problem_content("Malformed JSON body"),
>     409: problem_content("Report title already exists"),
>     422: problem_content("Invalid title fields"),
> }
>
> reports = {
>     41: Report(id=41, title="Monthly overview", status="ready"),
>     42: Report(id=42, title="Service health", status="ready"),
>     43: Report(id=43, title="Usage summary", status="queued"),
> }
> cursor_offsets: dict[str, int] = {}
> next_id = 44
> app = FastAPI()
> router = APIRouter(prefix="/api")
>
>
> def problem_response(status, kind, title, detail, **extensions):
>     return JSONResponse(
>         status_code=status,
>         media_type="application/problem+json",
>         content={
>             "type": PROBLEM_BASE + kind,
>             "title": title,
>             "status": status,
>             "detail": detail,
>             **extensions,
>         },
>     )
>
>
> @app.exception_handler(ApiProblem)
> async def api_problem_handler(request: Request, exc: ApiProblem):
>     return problem_response(exc.status, exc.kind, exc.title, exc.detail)
>
>
> @app.exception_handler(RequestValidationError)
> async def validation_handler(request: Request, exc: RequestValidationError):
>     errors = exc.errors()
>     if any(error.get("type") == "json_invalid" for error in errors):
>         return problem_response(
>             400, "malformed-json", "Malformed JSON", "Send a syntactically valid JSON body."
>         )
>     fields = [
>         {"field": ".".join(str(part) for part in error["loc"]), "code": "invalid_value"}
>         for error in errors
>     ]
>     return problem_response(
>         422, "validation", "Request validation failed",
>         "Correct the fields listed in errors and resubmit.", errors=fields,
>     )
>
>
> @router.get("/reports", response_model=Page, responses=LIST_ERRORS)
> async def list_reports(
>     limit: int = Query(default=2, ge=1, le=100), cursor: str | None = None
> ):
>     if cursor is None:
>         offset = 0
>     elif cursor in cursor_offsets:
>         offset = cursor_offsets[cursor]
>     else:
>         raise ApiProblem(400, "invalid-cursor", "Invalid cursor", "Start a new listing.")
>
>     ordered = [reports[key] for key in sorted(reports)]
>     page = ordered[offset : offset + limit]
>     next_cursor = None
>     if offset + len(page) < len(ordered):
>         next_cursor = secrets.token_urlsafe(12)
>         cursor_offsets[next_cursor] = offset + len(page)
>     return Page(items=page, next_cursor=next_cursor)
>
>
> @router.get("/reports/{report_id}", response_model=Report, responses=READ_ERRORS)
> async def get_report(report_id: int):
>     if report_id not in reports:
>         raise ApiProblem(
>             404, "not-found", "Report not found",
>             "No report is visible under this identifier.",
>         )
>     return reports[report_id]
>
>
> @router.post(
>     "/reports", status_code=201, response_model=Report, responses=CREATE_ERRORS
> )
> async def create_report(payload: CreateReport, response: Response):
>     global next_id
>     title = payload.title
>     if any(report.title.casefold() == title.casefold() for report in reports.values()):
>         raise ApiProblem(409, "duplicate-title", "Title already exists", "Choose another title.")
>     report = Report(id=next_id, title=title, status="queued")
>     reports[next_id] = report
>     response.headers["Location"] = f"/api/reports/{next_id}"
>     next_id += 1
>     return report
>
>
> app.include_router(router)
>
>
> def check():
>     client = TestClient(app)
>     good = client.get("/api/reports/42", headers={"Accept": "application/json"})
>     assert good.status_code == 200
>     assert good.json() == {"id": 42, "title": "Service health", "status": "ready"}
>
>     missing = client.get("/api/reports/999")
>     assert missing.status_code == 404
>     assert missing.headers["content-type"].startswith("application/problem+json")
>     assert missing.json()["type"] == PROBLEM_BASE + "not-found"
>     invalid_id = client.get("/api/reports/not-an-integer")
>     assert invalid_id.status_code == 422
>
>     first = client.get("/api/reports?limit=2")
>     assert [row["id"] for row in first.json()["items"]] == [41, 42]
>     assert first.json()["next_cursor"] is not None
>     cursor = first.json()["next_cursor"]
>     second = client.get("/api/reports", params={"limit": 2, "cursor": cursor})
>     assert [row["id"] for row in second.json()["items"]] == [43]
>     assert "next_cursor" in second.json() and second.json()["next_cursor"] is None
>     assert client.get("/api/reports?limit=101").status_code == 422
>     assert client.get("/api/reports?cursor=unknown-token").status_code == 400
>
>     malformed = client.post(
>         "/api/reports", content="{", headers={"Content-Type": "application/json"}
>     )
>     assert malformed.status_code == 400
>     assert malformed.json()["type"] == PROBLEM_BASE + "malformed-json"
>     assert malformed.headers["content-type"].startswith("application/problem+json")
>     whitespace = client.post("/api/reports", json={"title": "   "})
>     assert whitespace.status_code == 422
>     overlong_raw = client.post("/api/reports", json={"title": " " * 61 + "Padded"})
>     assert overlong_raw.status_code == 422
>
>     created = client.post("/api/reports", json={"title": " Weekly detail "})
>     assert created.status_code == 201 and created.json()["id"] == 44
>     assert created.json()["title"] == "Weekly detail"
>     assert created.headers["location"] == "/api/reports/44"
>     duplicate = client.post("/api/reports", json={"title": "weekly detail"})
>     assert duplicate.status_code == 409
>     assert duplicate.json()["type"] == PROBLEM_BASE + "duplicate-title"
>
>     spec = app.openapi()
>     paths = spec["paths"]
>     assert "/api/reports/42" not in paths  # path template is used in OpenAPI
>     get_one = paths["/api/reports/{report_id}"]["get"]
>     get_list = paths["/api/reports"]["get"]
>     post = paths["/api/reports"]["post"]
>     assert "404" in get_one["responses"] and "422" in get_one["responses"]
>     assert "400" not in get_one["responses"] and "409" not in get_one["responses"]
>     assert "400" in get_list["responses"] and "422" in get_list["responses"]
>     assert "404" not in get_list["responses"] and "409" not in get_list["responses"]
>     assert {"400", "409", "422"} <= set(post["responses"])
>     assert "404" not in post["responses"]
>     page_schema = spec["components"]["schemas"]["Page"]
>     assert "next_cursor" in page_schema["required"]
>     assert page_schema["properties"]["next_cursor"]["anyOf"]
>     print("GET /api/reports/42 -> 200; missing -> 404; invalid ID -> 422")
>     print("malformed JSON -> 400; blank/overlong title -> 422; duplicate -> 409")
>     print("page [41, 42] -> [43]; required next_cursor=null ends the listing")
>     print("OpenAPI routes and per-operation responses match the demonstrated paths")
>
>
> check()
> ~~~
>
> This code uses an in-memory offset map to teach the cursor boundary; the token expires on process restart and is not bound to filters, sort order or identity. A production collection can use an index-backed keyset cursor and reauthorize each page. The page contents are computed from these three records; they are not performance measurements.

### 兼容演进需要显式规则

新增可选响应字段通常可兼容会忽略未知字段的客户端，但严格解码器或生成代码可能拒绝它。删除字段、改变字段类型或含义、把可选请求字段改为必填、改变 Problem `type`、调整分页结束标志，都可能破坏调用方。应公开兼容政策，检查重要调用方，并为不兼容变更安排版本切换或迁移窗口；不存在唯一强制的版本化方案。

**接下来：** 本章描述调用方可观察的接口结构；HTTP 方法、缓存与状态码的通用语义见[浏览器请求如何到达 HTTP 响应？](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F)，副作用未知后的结果查询和重试见[请求超时后如何确认结果并安全重试？](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - 错误正文的类别标识、状态、标题、详情和扩展字段：[IETF RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)，§3–§4，2023-07；核对于 2026-11-06。
> - 400、401 challenge、403、404、409、422、429、201 与 202 的 HTTP 语义：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§9、§15，2022-06；核对于 2026-11-06。
> - 操作、参数、媒体类型、响应和 schema 的接口描述：[OpenAPI Specification v3.2.1](https://spec.openapis.org/oas/v3.2.1.html)，2026-09-10，§4–§5；核对于 2026-11-06。代码环境当前生成 3.1.0；运行时版本由 `app.openapi()['openapi']` 决定，规范文件描述契约但不保证实现遵循它。
> - 页大小、请求间参数一致、不透明 page token 和结束信号：[Google AIP-158, Pagination](https://google.aip.dev/158)，2019-02-18，Guidance；核对于 2026-11-06。
> - FastAPI 请求模型、响应模型和自定义错误处理：[FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)、[Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)、[Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)，官方文档核对于 2026-11-06；错误类型映射已在列明版本的本地运行环境核对。
## 4. Cookie 会话与 OIDC 令牌怎样建立身份？

浏览器每次读取报表 42 时，服务端要先辨认请求携带的凭据、签发者和可确认的身份。Cookie 可以承载不透明会话标识，应用再由标识查询服务器端会话；bearer token（持有者令牌）本身就是可重放的凭据，由资源服务验证。OpenID Connect (OIDC，基于 OAuth 2.0 的身份层) 让应用验证身份提供方的认证结果。应用随后仍要建立自己的会话；独立的报表 API 则需要面向该 API 签发的 Access Token（访问令牌）。这些凭据只建立调用者身份或调用资格，不决定用户能否读取报表 42。

### 登录后，Cookie 会话怎样识别请求？

一种常见架构是在浏览器保存随机、不透明的会话 ID（标识），服务器把会话状态保存在共享存储或应用数据库。登录后，服务器创建新会话记录并以 `Set-Cookie` 返回：

~~~http
Set-Cookie: __Host-session=<random-opaque-id>; Path=/; Secure; HttpOnly; SameSite=Lax
~~~

后续请求只有在目标主机、路径、安全连接和 SameSite 规则都匹配时才会附带 Cookie。`__Host-session` 是由 `reports.example` 设置的 host-only Cookie：它随发往该主机的合适请求发送，不会自动发送给 `api.reports.example`、`console.example.com` 或其他主机。服务端收到标识后查询会话，再把经验证的主体映射到本地账户，例如用签发者 `iss`（issuer，签发身份提供方）与该签发者范围内的用户编号 `sub`（subject，主体）共同标识账户。Cookie 字段只运送值；同一个字段也能存偏好等非身份数据，“有 Cookie”本身不表示已经认证。

会话 ID 是可重放凭据。认证成功或权限等级变化时轮换它，可以降低会话固定风险；空闲过期、绝对过期、退出、密码重置和管理员撤销的处理共同决定失效速度。`__Host-` 要求安全连接、无 `Domain` 属性且 `Path=/`，从而收紧 Cookie 主机范围。`Secure` 限制只在安全连接上传送；`HttpOnly` 阻止页面脚本直接读取 Cookie 值；`SameSite` 限制部分跨站上下文中的自动发送。它们各有边界：`HttpOnly` 不能阻止已执行的恶意脚本代替用户发请求；`SameSite` 按 site（站点）判断，不等同 origin（源）或资源授权。若确实需要跨站上下文附带 Cookie，需设置 `SameSite=None; Secure`，并保留适用的 CSRF 防护；见[浏览器安全控制保护什么边界？](#6.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AE%89%E5%85%A8%E6%8E%A7%E5%88%B6%E5%88%86%E5%88%AB%E4%BF%9D%E6%8A%A4%E4%BB%80%E4%B9%88%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C%EF%BC%9F)。

### Cookie 会话和 Bearer 令牌各保留什么状态？

| 设计 | 浏览器或调用方携带 | 验证点与状态 | 撤销和权限变化的取舍 |
| --- | --- | --- | --- |
| 服务端 Cookie 会话 | Cookie 中的不透明会话 ID | 应用按 ID 取服务器端会话；受保护操作再逐次检查授权 | 可即时使服务器端记录失效；请求需要会话存储或共享会话服务 |
| 不透明 Bearer Access Token | 常见形式是 `Authorization: Bearer …` | 资源服务器查询签发方或调用 token introspection（令牌状态查询）服务 | 可集中撤销；请求可能依赖查询服务或其缓存 |
| 自包含 JWT Bearer Token | 常见形式是同一 Authorization 字段 | 资源服务器验签并检查 `iss`、`aud`（audience，令牌原本面向的受众）、有效期和用途 | 不必每次查询用户会话；已签发权限可能在到期前仍有效，及时撤销需要额外机制 |

JSON Web Token (JWT，JSON Web 令牌) 是令牌格式，不是身份已验证的证明。典型签名 JWT 的声明可被读取；签名证明内容来自受信签发者且未被修改，不提供保密性。验证方要按目标协议检查允许的算法、准确签发者、目标受众、令牌类型、过期时间和适用的授权范围；只解码 JWT 不等于验证 JWT。若资源服务器必须及时获知撤销，短有效期、introspection 或请求期会话检查都可能适用，取舍取决于延迟、故障和部署成本。

单页应用若把访问令牌放在脚本可读的存储中，XSS 可能将其读出；换成 HttpOnly Cookie 后，脚本不易直接读凭据，但浏览器会自动附带 Cookie，仍须防 CSRF。由后端代理浏览器请求的架构可以把访问令牌留在服务端，并给浏览器较短作用域的应用会话。选择存储位置不能修复 XSS、错误授权或身份映射问题。

### 授权码流程如何确认身份并建立应用会话？

OAuth 2.0 是授权框架，本身不定义客户端如何确认终端用户身份；OIDC 在其上增加身份层和 ID Token（身份令牌）。ID Token 面向 OIDC 客户端，说明身份提供方完成了怎样的认证事件；Access Token 面向资源服务器。把发给登录客户端的 ID Token 当成报表 API 凭据会混淆两个受众。

**案例：** 查看者在报表应用选择“使用身份提供方登录”。本例选择授权码流程和顶层 GET callback：

1. 应用生成高熵、一次性的 PKCE `code_verifier`，计算 `code_challenge = BASE64URL(SHA-256(ASCII(code_verifier)))`；再生成随机事务句柄，把 `{state, verifier, expected_issuer}` 按句柄保存在短期服务端记录中。
2. 应用用 `__Host-login-tx` Cookie 把事务句柄交给浏览器，属性为 `Path=/; Secure; HttpOnly; SameSite=Lax`，且不设置 `Domain`；再把浏览器导向已注册的身份提供方，并发送 `response_type=code`、`client_id`、精确登记的 `redirect_uri`、`scope=openid`、`code_challenge`、`code_challenge_method=S256` 和随机 `state`。短期事务记录和 Cookie 都应设置有限寿命。本例的顶层 GET 回调可携带 Lax Cookie；若选择其他回调方式，应重新核对 SameSite 发送条件。
3. 身份提供方认证用户后，将浏览器导回已登记的 callback，附上短期授权码与原 `state`。回调请求还须携带先前设置的登录事务 Cookie；应用先用它定位本浏览器发起的事务，再核对并消费其中的 state，取回 verifier 和预期签发者。不能只凭 callback 自带的 state 查一个全局事务记录。配置多个授权服务器时，还须按协议防范授权服务器混淆并校验 issuer。
4. 应用后端向 Token Endpoint 提交 `grant_type=authorization_code`、授权码、原 `redirect_uri`、私有 `code_verifier`；按客户端类型还要认证客户端。身份提供方重新计算 challenge，匹配后才兑换授权码。截获授权码的第三方通常没有 verifier，不能代替发起客户端完成交换。
5. 成功兑换的 Token Endpoint 响应返回 ID Token 和 Access Token。OIDC 客户端验证 ID Token，再把 `(issuer, subject)` 映射到本地账户并建立自己的应用会话。`scope=openid` 建立 OIDC 身份请求，但不会自动授予自定义报表 API 的受众或权限；Access Token 只有在身份提供方按资源服务器配置签发了该 API 所需的 audience 与权限时，才可用于报表 API。其他配置下它可能面向 UserInfo 等资源，不能仅凭它与 ID Token 一起返回就当作报表 API 凭据。

`state` 把回调与发起登录的浏览器事务绑定；`nonce`（若发送）把 ID Token 与一次认证请求关联；PKCE 把授权码与持有 verifier 的客户端绑定。RFC 9700 允许客户端在确认授权服务器支持 PKCE 时依 PKCE 防护回调 CSRF；若不确认支持，或本身发送了 state/nonce，就要把相应值绑定原事务并验证，不能信任回调自带值。授权服务器必须支持 PKCE；客户端应显式发送 `code_challenge_method=S256`，因为省略时 RFC 7636 默认 `plain`。

~~~mermaid
sequenceDiagram
    participant App as 报表应用
    participant Browser as 浏览器
    participant IdP as 身份提供方
    participant API as 报表 API
    App->>App: 保存 {state, verifier, expected_issuer}
    App->>Browser: 登录事务 Cookie + redirect_uri、scope=openid、challenge、method=S256、state
    Browser->>IdP: 请求授权码
    IdP->>Browser: 顶层 GET 回调 code + state
    Browser->>App: 事务 Cookie + code + state
    App->>App: 用 Cookie 找事务并消费 state
    App->>IdP: grant_type=authorization_code、code、redirect_uri、verifier
    IdP-->>App: ID Token 和 Access Token
    App->>App: 验证 ID Token，创建本地应用会话
    opt 独立 API 且签发方配置了该资源
        App->>API: API audience 的 Access Token
        API->>API: 验证令牌后逐次检查资源授权
    end
~~~

验证 ID Token 时，客户端至少要匹配预期 `iss`，验证 `aud` 包含客户端 ID、按规则检查 `azp`（authorized party，获授权的客户端），核验 `exp`、本次事务发送的 `nonce`（如有），并依据协议验证签名、可信算法和密钥。报表 API 若是独立资源，身份提供方须配置相应资源受众与权限；客户端可以按 RFC 8707 使用 `resource` 参数请求特定资源（是否支持仍由提供方决定），API 再独立验证该专用 Access Token 的 issuer、audience、有效期和范围。OAuth scope 不会替应用判断报表 42 的本地所有权。

> [!info] 单点登录不共享各应用的本地会话
> Single Sign-On (SSO，单点登录) 可以让同一身份提供方的登录会话支持用户进入多个已注册应用，减少重复输入凭据的需要；同意页面、策略和认证强度仍可能要求再次交互。每个应用仍须验证自己的授权回调并创建自己的本地会话。退出一个应用的本地会话，不一定结束身份提供方会话，也不会自动退出其他应用。报表应用使用的会话 Cookie 仍由各自主机设置和验证。

> [!info] Token Endpoint 的限定验证方式
> OIDC Core 对直接经已验证 TLS 连接从 Token Endpoint 收到的 Authorization Code Flow ID Token 允许一种窄例外：在验证 Token Endpoint 的 TLS 服务器身份后，可用它验证 issuer 来代替 ID Token 签名检查。该例外只适用于这条受限路径；其他 ID Token 仍须按规范验证签名。

Refresh Token 只发给 Token Endpoint 用于换取新 Access Token，不应发给报表 API。它是高价值凭据；RFC 9700 要求公共客户端使用令牌轮换或 sender-constraining 检测 Refresh Token 重放。若签发方提供撤销端点，客户端可请求撤销；自包含 Access Token 是否立即停止被资源服务器接受，还取决于资源服务器是否查撤销状态。退出本地应用会话、退出身份提供方会话、撤销令牌是三种相关但不同的操作。

### 本地密码验证后，应用还要做什么？

本地密码数据库保存带随机盐的专用密码哈希及其算法和成本参数，而不是明文或快速通用散列。被盗数据库会让攻击者离线尝试猜测；内存困难的 Argon2id 会使每次猜测消耗内存和计算，仍需由服务根据并发和硬件调优成本，并独立限制在线尝试。OWASP 当前列出的 19 MiB 内存、2 次迭代、并行度 1 是一个最低 Argon2id 配置示例，不是所有服务的性能目标。盐不需要保密；可选 Pepper 是数据库外的服务器秘密，要先设计轮换与恢复。

密码验证或联邦身份验证得到的是已经验证的主体和认证上下文。之后，账户映射、会话生命周期和具体资源授权仍由应用负责。报表编号 42 是否允许当前主体读取，见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

> [!info]- 来源
> - Cookie 与服务器状态关联：[IETF RFC 6265, HTTP State Management Mechanism](https://www.rfc-editor.org/rfc/rfc6265.html)，§4–§5，2011-04；属性与 Cookie 发送限制同时核对 WHATWG [Fetch Standard, Cookies](https://fetch.spec.whatwg.org/#cookies)，Living Standard，核对于 2026-11-06。
> - Cookie 前缀、host-only 作用域与 SameSite 属性：[HTTPWG RFC6265bis 草案](https://httpwg.org/http-extensions/draft-ietf-httpbis-rfc6265bis.html)，§4.1.3.2、§5.6.7，核对于 2026-11-06；草案仍在演进。
> - 会话 ID 与安全配置：[OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)，Session ID、Cookie 属性和过期章节，按 2026-11-06 版本核对。
> - OAuth 2.0 安全最佳实践：[IETF RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)，§2、§4.7、§4.10、§4.14，2025-01；核对于 2026-11-06。
> - OIDC 身份层、Code Flow、ID Token 和访问令牌验证：[OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html)，§2、§3.1.2–§3.1.3，2023-12-15；Token Endpoint/TLS 例外见 §3.1.3.7(6)。核对于 2026-11-06。
> - PKCE verifier、challenge 与默认方法：[IETF RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html)，§4.3；授权码交换参数：[RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html)，§4.1.3；资源指示参数：[RFC 8707](https://www.rfc-editor.org/rfc/rfc8707.html)，§2。均核对于 2026-11-06。
> - Token 撤销：[RFC 7009](https://www.rfc-editor.org/rfc/rfc7009.html)，§2，2013-08；JWT 验签与防算法混淆：[RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html)，§3，2020-02。均核对于 2026-11-06。
> - 密码哈希 Argon2id 参数：[OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)，Argon2id 与升级章节，按 2026-11-06 版本核对；身份验证器要求：[NIST SP 800-63B-4](https://csrc.nist.gov/pubs/sp/800/63/b/4/final)，2025-07，核对于 2026-11-06。
## 5. 如何逐次授权租户内的报表资源？

authentication (身份认证) 确认请求由哪个主体发出；authorization (授权) 逐项判断该主体此刻能否对指定资源执行指定动作。请求里的用户 ID、租户 ID、角色名或报表编号可由调用方选择，不能因它们出现在 URL、JSON 或队列消息里就视为可信事实。

**案例设定：** 浏览器请求 `/tenants/tenant-a/reports/42`。身份层已验证用户 `user-17`，数据库里 `user-17` 是租户甲的 `reader`；报表 42 的所有者固定为租户甲。`reader` 可以读取现有报表，但不能因此发起高成本重算或导出。为简化例子，报表归属不可变，授权只由当前成员角色决定，没有单报表分享规则。示例结果如下：

| 请求 | 数据库状态 | 对外结果 |
| --- | --- | --- |
| `user-17` 在 `tenant-a` 读报表 42 | 当前成员角色允许，复合键 `(tenant-a, 42)` 存在 | 200，返回报表 |
| `user-29` 在 `tenant-b` 读报表 42 | 用户是乙的 reader，但 `(tenant-b, 42)` 不存在 | 404，隐藏其他租户资源 |
| 没有租户成员身份的用户读报表 42 | 无当前租户主体 | 404，按本 API 的隐藏政策与资源不存在统一 |
| 任务创建后 `user-17` 被移出租户甲 | 当前成员关系已撤销 | API 读为 404；需要当前权限的 worker 拒绝任务 |

~~~mermaid
flowchart LR
    Credential[验证 Cookie 会话或 API 凭据] --> Subject[得到可信主体]
    Subject --> Tenant[从请求取租户上下文并查当前成员]
    Tenant -->|无成员或无 report:read| Deny[统一按政策返回 404]
    Tenant -->|允许读取| Key[构造 tenant、subject、report 缓存键]
    Key --> Cache{缓存命中？}
    Cache -->|是| Hit[返回曾在正确租户范围内填充的副本]
    Cache -->|否| Query[按 tenant_id + report_id 查询]
    Query -->|存在| Fill[填充对应范围的缓存并返回]
    Query -->|不存在| Missing[返回 404]
    Export[独立导出/重算请求] --> ExportAuth[另查 report:export 等动作权限]
    ExportAuth -->|通过| Job[持久化可信任务记录]
    Job --> Worker[worker 读 job_id 并复验当前策略]
~~~

图中的缓存命中以固定报表归属、按租户和主体隔离的缓存键为前提；未命中时，查询再以 `(tenant_id, report_id)` 证明行属于该租户。若所有权、分享关系或可见策略能改变，缓存命中也必须校验当前对象授权，并可靠更新或失效旧范围的缓存。缓存不应跳过本次请求的成员授权。

### 从可信主体到报表 42 的读取，需要经过哪些检查？

1. 认证层验证 Cookie 会话或访问令牌，得出稳定主体。不要把请求头或请求体里的 `user_id` 当成登录结果。凭据和联邦登录见[Cookie 会话与 OIDC 令牌怎样建立身份？](#4.%20Cookie%20%E4%BC%9A%E8%AF%9D%E4%B8%8E%20OIDC%20%E4%BB%A4%E7%89%8C%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E8%BA%AB%E4%BB%BD%EF%BC%9F)。
2. 将路径中的 `tenant-a` 当作用户希望选择的上下文；服务器查当前主体在租户甲的成员关系，之后才把它用于权限判断。多租户应用要明确用户在不同租户各自拥有的角色。
3. 把动作与对象一起判断。`reader` 可以允许若干读取动作，但不能自动证明对象归属，也不能推导出导出、刷新或管理权限。
4. 查询时同时绑定租户与编号，不能先用全局编号取出私有报表，再假设隐藏链接、不可猜 ID 或 UI 检查已经完成授权。
5. 对 API、附件、缓存和后台工作等每条数据路径重复正确的检查。最小权限的服务账号定义 worker 能做什么，不替最终用户完成授权。

#### 角色能授予什么动作，资源检查还要做什么？

Role-Based Access Control (RBAC，基于角色的访问控制) 用 `reader`、`admin` 等角色归纳一组动作，适合表达租户成员的常见权限。资源属性或关系可能还需额外条件，例如某份报表只分享给指定主体，或其部门标签不匹配。角色说明“通常可做哪类动作”，不能证明报表 42 属于当前租户或用户。新端点默认拒绝，并对每个受保护操作重新检查当前策略，可以减少遗漏。

### 数据库与缓存怎样保持同一授权范围？

把租户和报表编号分别作为绑定值传入 SQL：

~~~sql
SELECT id, title, body
FROM reports
WHERE tenant_id = ? AND id = ?;
~~~

参数绑定防止输入改写 SQL 语法；授权检查决定当前主体能否读取绑定后的对象。两者解决不同问题：绑定参数后读取 `report_id=73` 仍可能越权；完成授权但拼接 SQL 仍可能被注入。动态排序字段通常不能作为一般参数绑定，应从固定允许列表里选择。

本例的数据库用复合主键 `(tenant_id, id)` 标识租户内报表；这使每个租户的编号空间明确。查询仍须保留两个谓词，因为主键约束数据形状，并不判断当前用户是否有权读该行。队列里的任务引用也应按同一复合身份解析。

缓存命中会绕过数据库谓词，因此先查当前成员资格，再访问带范围的缓存。此例缓存键是 `(tenant_id, subject, report_id)`：租户乙不能拿租户甲的缓存副本，且每次 API 请求都会先重查当前成员。固定所有权是这个精简示例的假设；若报表可以迁移租户或分享权限会变，就要在命中路径复验对象访问条件，或确保权限变更同步使缓存失效。参见[如何控制数据库缓存的新鲜度？](#11.%20%E6%80%8E%E6%A0%B7%E7%BC%93%E5%AD%98%E6%95%B0%E6%8D%AE%E5%BA%93%E8%AF%BB%E5%8F%96%E5%B9%B6%E8%AF%B4%E6%98%8E%E9%99%88%E6%97%A7%E7%AA%97%E5%8F%A3%EF%BC%9F)。

### 后台任务如何继续执行相同的访问政策？

排队时先按该任务的实际动作授权，再保存服务端创建的可信任务记录。消息只带不透明 `job_id`；worker 用该 ID 从可信存储读取租户、请求人和资源，不从任意消息载荷接受租户或报表编号。worker 是否要在执行时重新检查成员资格取决于产品定义：若成员移除后应停止工作，就复验当前权限；若已受理任务按提交时权限继续，则把那项授权决定作为可审计状态持久化。

下面的复现仅演示“读取一个已经存在的报表”任务，因此 `enqueue_read_job` 只需要 `report:read`。高成本报表导出或重算必须另查 `report:export` 等独立动作，或者明确定义其权限组合；不能从 `reader` 自然推出。账户报表作业的幂等受理、outbox 发布和队列确认见[怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)；队列确认分别见[发布者确认和消费者确认分别证明什么？](#14.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

输入输出可以直接按上面的状态表理解：甲的成员读取甲的 42 返回 200；乙的成员读取乙命名空间中不存在的 42 返回 404；失去成员关系后，API 仍按隐藏策略返回 404，worker 抛出拒绝异常。完整 SQLite 复现放在折叠示例中。

> [!example]- SQLite 授权、缓存与任务复现
> 示例使用标准库 SQLite 和合成数据；`principal_for` 的主体参数视为认证中间件已经验证，不实现 Cookie 或签名令牌。
>
> ~~~python
> import sqlite3
>
> db = sqlite3.connect(":memory:")
> db.executescript("""
> CREATE TABLE memberships (
>     tenant_id TEXT NOT NULL, subject TEXT NOT NULL, role TEXT NOT NULL,
>     PRIMARY KEY (tenant_id, subject)
> );
> CREATE TABLE reports (
>     tenant_id TEXT NOT NULL, id INTEGER NOT NULL,
>     title TEXT NOT NULL, body TEXT NOT NULL,
>     PRIMARY KEY (tenant_id, id)
> );
> CREATE TABLE jobs (
>     id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL,
>     requester TEXT NOT NULL, report_id INTEGER NOT NULL
> );
> INSERT INTO memberships VALUES ('tenant-a', 'user-17', 'reader');
> INSERT INTO memberships VALUES ('tenant-b', 'user-29', 'reader');
> INSERT INTO reports VALUES
>     ('tenant-a', 42, 'Service health', 'Synthetic private data A');
> INSERT INTO reports VALUES
>     ('tenant-b', 73, 'Usage summary', 'Synthetic private data B');
> """)
>
> def principal_for(tenant_id, subject):
>     row = db.execute(
>         "SELECT role FROM memberships WHERE tenant_id=? AND subject=?",
>         (tenant_id, subject),
>     ).fetchone()
>     if row is None or row[0] not in {"reader", "admin"}:
>         return None
>     return {"tenant_id": tenant_id, "subject": subject, "role": row[0]}
>
> def read_report(principal, report_id, cache):
>     if principal is None or principal["role"] not in {"reader", "admin"}:
>         raise PermissionError("no current report:read permission")
>     key = (principal["tenant_id"], principal["subject"], report_id)
>     if key not in cache:
>         row = db.execute(
>             "SELECT body FROM reports WHERE tenant_id=? AND id=?",
>             (principal["tenant_id"], report_id),
>         ).fetchone()
>         if row is None:
>             return None
>         cache[key] = row[0]
>     return cache[key]
>
> def read_api(tenant_id, subject, report_id, cache):
>     # 隐藏政策把无成员、无角色和资源不存在统一映射为 404。
>     principal = principal_for(tenant_id, subject)
>     if principal is None:
>         return (404, None)
>     body = read_report(principal, report_id, cache)
>     return (404, None) if body is None else (200, body)
>
> def enqueue_read_job(tenant_id, subject, report_id, cache):
>     principal = principal_for(tenant_id, subject)
>     if read_report(principal, report_id, cache) is None:
>         raise PermissionError("cannot enqueue an unreadable report")
>     cursor = db.execute(
>         "INSERT INTO jobs (tenant_id, requester, report_id) VALUES (?, ?, ?)",
>         (principal["tenant_id"], principal["subject"], report_id),
>     )
>     db.commit()
>     return cursor.lastrowid
>
> def run_job(job_id, cache):
>     job = db.execute(
>         "SELECT tenant_id, requester, report_id FROM jobs WHERE id=?", (job_id,)
>     ).fetchone()
>     if job is None:
>         raise PermissionError("unknown job")
>     tenant_id, requester, report_id = job
>     principal = principal_for(tenant_id, requester)  # 执行时重查成员
>     body = read_report(principal, report_id, cache)
>     if body is None:
>         raise PermissionError("job target is outside its tenant or no longer readable")
>     return body
>
> cache = {}
> assert read_api("tenant-a", "user-17", 42, cache) == (
>     200, "Synthetic private data A"
> )
> assert read_api("tenant-b", "user-29", 42, cache) == (404, None)
> assert read_api("tenant-a", "user-29", 42, cache) == (404, None)
> job_id = enqueue_read_job("tenant-a", "user-17", 42, cache)
> assert run_job(job_id, cache) == "Synthetic private data A"
>
> # 即使错误写入了跨租户任务记录，worker 仍按 tenant_id + report_id 查询。
> malicious_job = db.execute(
>     "INSERT INTO jobs (tenant_id, requester, report_id) VALUES (?, ?, ?)",
>     ("tenant-b", "user-29", 42),
> )
> db.commit()
> try:
>     run_job(malicious_job.lastrowid, cache)
> except PermissionError:
>     pass
> else:
>     raise AssertionError("worker exposed a report outside the tenant")
>
> # 已排队任务在成员撤销后不得命中旧缓存。
> db.execute("DELETE FROM memberships WHERE tenant_id=? AND subject=?",
>            ("tenant-a", "user-17"))
> db.commit()
> assert read_api("tenant-a", "user-17", 42, cache) == (404, None)
> try:
>     run_job(job_id, cache)
> except PermissionError:
>     pass
> else:
>     raise AssertionError("worker accepted a revoked member")
> print("tenant-a user-17: report 42 -> 200 before revocation, 404 after")
> print("tenant-b user-29: report 42 -> 404; wrong-scope and revoked jobs denied")
> ~~~

**接下来：** 本章负责服务端把主体、动作和租户内资源联系起来；浏览器跨源读取、Cookie 自动发送和脚本执行见[浏览器安全控制分别保护什么信任边界？](#6.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AE%89%E5%85%A8%E6%8E%A7%E5%88%B6%E5%88%86%E5%88%AB%E4%BF%9D%E6%8A%A4%E4%BB%80%E4%B9%88%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C%EF%BC%9F)。网络入口容量与攻击流量准入见[Web 服务如何限制拒绝服务的影响？](#24.%20Web%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%8B%92%E7%BB%9D%E6%9C%8D%E5%8A%A1%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F)。

> [!info]- 来源
> - 每次受保护操作检查权限、默认拒绝、最小权限和对象级授权：[OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)，Recommendations 与 IDOR 章节，按 2026-11-06 版本核对。
> - 租户所有权与 pooled SaaS 中运行时租户隔离：[AWS Well-Architected SaaS Lens, Preventing cross-tenant access](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/preventing-cross-tenant-access.html)，按 2026-11-06 版本核对。该文是云厂商架构指导，不是通用标准。
> - SQL 参数化与允许列表：[OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)，Primary Defenses，按 2026-11-06 版本核对。
## 6. 浏览器安全控制分别保护什么信任边界？

报表页面会跨过多个不同边界。Transport Layer Security (TLS，传输层安全协议) 保护 HTTP 网络链路；Cross-Site Scripting (XSS，跨站脚本攻击) 防护避免不可信文本变成活动脚本；Cross-Site Request Forgery (CSRF，跨站请求伪造) 防护限制另一页面借用浏览器自动附带的 Cookie 发起变更；Cross-Origin Resource Sharing (CORS，跨源资源共享) 控制浏览器脚本能否读取跨源响应；Content Security Policy (CSP，内容安全策略) 的 `frame-ancestors` 限制哪些来源能嵌入页面。它们都不替代服务端认证和对报表 42 的逐次授权。

| 信任边界 | 控制主要保证什么 | 本身不保证什么 |
| --- | --- | --- |
| 网络链路 | 正确配置的 TLS 加密传输、检测篡改并认证服务端 | 登录用户身份或其可读取的报表 |
| 页面解释数据 | 按上下文输出编码和必要的标记消毒，避免数据成为活动内容 | 已执行脚本不会滥用页面已有权限 |
| Cookie 自动发送 | CSRF token 或经审查的来源校验限制伪造状态变更 | 阻止所有未授权调用 |
| 浏览器跨源读取 | 同源策略与 CORS 控制脚本能否读取响应 | 请求一定未到服务器或用户已经获授权 |
| 页面嵌入 | `frame-ancestors` 限制谁能嵌入报表界面 | 报表数据和操作的服务端权限 |

### 网络连接如何保护数据并认证服务端？

TLS 握手后为连接建立流量保护。浏览器正确验证证书链、主机名和握手时，HTTPS 可以保护传输机密性与完整性，并认证连接到预期的服务器。TLS 不说明当前浏览器用户是谁；即使浏览器验证了报表站点提供的证书，服务仍须验证会话或访问凭据，并授权读取报表 42。证书状态查询和撤销行为受客户端及部署方式影响，不应假设所有浏览器以相同步骤即时检查撤销。

### 不可信报表标题怎样安全显示？

Document Object Model (DOM，文档对象模型) 是页面结构；XSS 指不可信数据被当作活动内容执行。假设报表 42 的标题是 ` <img src=x onerror=alert(1)> `。若把它交给将值设为纯文本的 `textContent`，它仍只是字符；若拼进 `innerHTML`，浏览器会按 HyperText Markup Language (HTML，超文本标记语言) 解析。当图片加载失败且策略允许 inline handler 时，`onerror` 处理器可能执行。

1. 普通文本使用框架默认安全的文本呈现接口。只有需要将数据放入安全属性值等允许上下文时，才用对应的上下文编码。
2. 不把不可信字符串拼进执行位置，例如动态脚本正文、事件处理器代码或 CSS 选择器；这些位置不能靠一种通用转义方式修好。
3. 只有产品确实要呈现用户编写的富文本时，才使用维护良好的 HTML 消毒器过滤允许的标记和属性。
4. 避免把不可信字符串传给 `innerHTML`、`document.write`、事件属性、`eval` 或 `new Function`。框架常规自动转义不保护有意使用的 raw HTML 入口。
5. 为链接和资源 URL 验证 scheme 与目标，例如拒绝不允许的 `javascript:`；HTML 属性编码不会限制 URL 的语义。经测试的 CSP 可限制脚本来源，作为纵深防御，不能代替安全呈现。

如果 XSS 已执行，脚本通常能以页面所属 origin 发起请求并读取脚本可访问的页面数据；即使会话 Cookie 是 `HttpOnly`，恶意脚本仍可能让浏览器替用户调用报表 API。因此要修复注入点并保留服务端授权。`HttpOnly` 减少 Cookie 值被脚本直接窃取的途径，不是 XSS 防护本身。

### Cookie 自动发送时，怎样防止伪造变更？

CSRF 利用浏览器自动附带目标站点 Cookie 的行为。以下场景固定为明确可复现的条件：用户已经登录 `api.example.test`，其当前主体本来就有执行 `reports:refresh` 的权限；另一个同 site 但不可信的旧子域 `legacy.example.test` 可被攻击者控制；API 接受下方表单格式，且目前没有 token 或来源校验。host-only Cookie 仍会发给目标 API 主机；同 site 不等于同 origin。

~~~html
<form action="https://api.example.test/api/reports/42/refresh" method="post">
  <input name="range" value="365-days">
</form>
<script>document.forms[0].submit();</script>
~~~

这次跨源表单 POST 的响应不必可被攻击页面读取，副作用仍可能已经发生。例子中的两个主机使用 HTTPS 且共享可注册域 `example.test`，所以是同 site、不同 origin；若 Cookie 为 `SameSite=Lax`，同 site 的表单 POST 仍可能附带 Cookie。真正跨 site 的普通 POST 通常会被 Lax 限制，但顶层安全方法导航等仍有不同规则，不能把 `Lax` 当成授权或完整 CSRF 防护。

对 Cookie 认证的状态变更，服务端验证与当前会话绑定的 CSRF token，或使用经过审查的等价机制；适用时再校验 Origin/Referer，并用合适的 SameSite 设置纵深防御。使用 GET 等安全方法的路由不应改变状态。加上 token 后，同一请求仍可能抵达 API，但因缺少或无效 token 而被拒绝；token 让服务识别伪造来源，不证明用户操作意图。如果同源 XSS 已执行，它可能读取页面中的 token 或调用合法请求接口，因此还要修复注入并持续执行资源授权。

当某个合法流程确实需要跨 site 附带 Cookie，应设置 `SameSite=None; Secure` 并单独设计 CSRF 防护。不要为了让登录回调或嵌入工作而静默取消请求校验。

### 同源策略如何控制跨源响应读取？

浏览器将 origin 定义为协议、主机和端口。`https://console.example.test` 与 `https://api.example.test` 的 scheme 和可注册域相同，属于 same-site；主机不同，所以是不同 origin。Cookie 的 SameSite 依据 site 判定，不能与 origin 混为一谈。

以下部署变体让控制台脚本直接请求 API；浏览器已通过 `api.example.test` 的登录流程持有 API 自己设置的 host-only `__Host-api-session` Cookie。`console.example.test` 的 Cookie 不会发给 `api.example.test`；`__Host-` Cookie 也不能设置 `Domain` 扩大范围。`credentials: "include"` 允许浏览器按目标 URL、Cookie 属性和 Fetch 凭据模式附带匹配凭据，JavaScript 不读取 Cookie 值。

~~~javascript
const response = await fetch('https://api.example.test/api/reports/42', {
  credentials: 'include',
  headers: { 'X-Report-View': 'compact' },
});
~~~

`X-Report-View` 不在 CORS safelist 中，因此在无可用预检缓存的本例里，浏览器先发送不含用户凭据的预检：

~~~http
OPTIONS /api/reports/42 HTTP/1.1
Host: api.example.test
Origin: https://console.example.test
Access-Control-Request-Method: GET
Access-Control-Request-Headers: x-report-view
~~~

~~~http
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://console.example.test
Access-Control-Allow-Methods: GET
Access-Control-Allow-Headers: X-Report-View
Access-Control-Allow-Credentials: true
Vary: Origin
~~~

预检获准后，浏览器才按 Fetch 凭据模式和 Cookie 规则发送实际 GET。这里假设 API Cookie 匹配目标 URL、已登录且请求的 SameSite 条件允许附带：

~~~http
GET /api/reports/42 HTTP/1.1
Host: api.example.test
Origin: https://console.example.test
Cookie: __Host-api-session=<opaque-session-id>
X-Report-View: compact
~~~

若请求获准读取，实际响应本身也必须带允许来源和凭据字段，脚本才能取得正文：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: https://console.example.test
Access-Control-Allow-Credentials: true
Vary: Origin

{"id":42,"title":"Service health","status":"ready"}
~~~

若预检通过但实际 `200` 漏掉 `Access-Control-Allow-Origin` 或 `Access-Control-Allow-Credentials`，API 仍已收到 GET 并执行处理，浏览器却不把响应暴露给脚本。按隐藏策略返回的 `404` 也必须有匹配的 CORS 响应字段，控制台脚本才可读取该错误。预检失败时浏览器不会发送实际请求；无需预检的请求则可能先到达服务器，即便脚本最后读不到响应。两种时序都要求 API 独立验证身份与权限。

CORS 是浏览器实现的读取协议，不能认证用户、授权报表、约束 curl 等非浏览器客户端，也不是一般网络防火墙。`Vary: Origin` 只让共享缓存按来源区分响应变体，不隔离不同用户的数据；私有响应还须正确设置缓存策略和用户范围。若页面与 API 可通过同一源反向代理到 `/api/`，通常可以省去跨源读取配置，但服务端授权仍需保留。

> [!info] Fetch 对 Cookie 响应字段的边界
> 浏览器脚本不能通过 Fetch/XHR 手动设置 `Cookie` 请求字段；它由浏览器依请求 URL 和 Cookie 政策管理。`Set-Cookie` 是禁止暴露给脚本的响应字段，网页不能靠读取它来取得 HttpOnly 会话值。登录 Cookie 的 host-only 范围见[会话与身份令牌](#4.%20Cookie%20%E4%BC%9A%E8%AF%9D%E4%B8%8E%20OIDC%20%E4%BB%A4%E7%89%8C%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E8%BA%AB%E4%BB%BD%EF%BC%9F)。

### 什么时候限制页面被嵌入？

点击劫持可将真实页面放进攻击者控制的 frame 下方，诱导用户点击错位按钮。CSP 的 `frame-ancestors` 响应指令声明哪些祖先来源可以嵌入页面；例如仅允许同源嵌入：

~~~http
Content-Security-Policy: frame-ancestors 'self'
~~~

旧客户端需要兼容时可设置 `X-Frame-Options`。允许列表应符合实际嵌入场景并在完整流程中测试。这个策略限制哪些页面能嵌入报表 UI，不替代服务端对每份报表或操作的权限判断。

WebSocket 握手也不能用 CORS 响应字段授权。浏览器会发送 Origin；服务端应按允许来源校验握手、认证连接，并对敏感消息继续授权。双向消息和断线恢复见[何时选择轮询、SSE、流式 Fetch 或 WebSocket？](#15.%20%E4%BD%95%E6%97%B6%E9%80%89%E6%8B%A9%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)。

**接下来：** TLS 保护网络连接；安全输出和 CSP 降低脚本注入风险；CSRF 防护检验带 Cookie 的变更请求；CORS 决定浏览器是否暴露跨源响应；`frame-ancestors` 决定页面可由谁嵌入。所有资源读取仍须经过[服务端逐项授权](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

> [!info]- 来源
> - TLS 1.3 握手、服务器认证与流量密钥：[IETF RFC 8446](https://www.rfc-editor.org/rfc/rfc8446.html)，§2–§4，2018-08；核对于 2026-11-06。
> - Same-Origin 与 same-site 判定：[WHATWG HTML, Origins and Sites](https://html.spec.whatwg.org/multipage/browsers.html#origins)，Living Standard，核对于 2026-11-06；`example.test` 属于示例域。
> - origin、Cookie、预检、CORS、credentialed 响应及禁止脚本设置 Cookie/读取 `Set-Cookie`：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，§2、§3.3、§4.2、§4.10，2026-10-19 版本；核对于 2026-11-06。Cookie 属性同时见 [RFC 6265](https://www.rfc-editor.org/rfc/rfc6265.html)，§5，2011-04。
> - 安全上下文输出、HTML 消毒与危险执行上下文：[OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)，Contextual Output Encoding、HTML Sanitization、Dangerous Contexts，按 2026-11-06 版本核对。
> - CSP 的脚本纵深防御：[OWASP Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)，按 2026-11-06 版本核对；`frame-ancestors`：[W3C Content Security Policy Level 3](https://www.w3.org/TR/CSP3/#directive-frame-ancestors)，2026-10-27 Working Draft，§6.4.2；该规范仍是工作草案，浏览器支持应与目标环境核验。
> - Cookie 认证请求的 CSRF token、Origin 和 SameSite 条件：[OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)，Synchronizer Token、SameSite 与 Origin Validation，按 2026-11-06 版本核对；Cookie same-site 规则：[HTTPWG RFC6265bis 草案](https://httpwg.org/http-extensions/draft-ietf-httpbis-rfc6265bis.html)，§5.6.7，核对于 2026-11-06。
## 7. SQL 空值、连接与分组会怎样改变报表 42 的结果？

**案例：** 报表 42 为账户 acct-17 汇总一小组客户订单。为让每一步能手算，下面把四个客户与四条订单当作本次报告的全部输入，不演示读取授权或全量账务规模。Ava 有两笔订单，Ben 的地区和一笔订单金额未知，Cy 有一笔已付款订单，Dia 没有订单。查询看似只是在拼表和相加，但 NULL、LEFT JOIN（左外连接）与 aggregate function（聚合函数）会改变哪些行存在、哪些值被统计。

~~~mermaid
flowchart TD
    Base[客户与订单输入] --> From[FROM / JOIN 生成中间行]
    From --> Where[WHERE 只保留 TRUE]
    Where --> Group[GROUP BY 形成分组]
    Group --> Aggregate[COUNT / SUM 计算]
    Aggregate --> Having[HAVING 筛掉不符合的分组]
    Having --> Output[报表 42 的客户汇总行]
~~~

这条流程中的每一步都作用于一个中间结果：JOIN 先组合行；WHERE 在分组前筛选；聚合函数对分组输入计算；HAVING 再筛选分组。NULL 表示值未知或缺失，不等于数字 0，也不等于空字符串。后面的输出会逐个显示这些状态造成的差异。

### 输入中的空值怎样影响比较？

~~~sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    amount_cents INTEGER,
    status TEXT NOT NULL
);

INSERT INTO customers VALUES
    (1, 'Ava', 'North'),
    (2, 'Ben', NULL),
    (3, 'Cy', 'South'),
    (4, 'Dia', 'North');

INSERT INTO orders VALUES
    (101, 1, 1200, 'paid'),
    (102, 1, 800, 'pending'),
    (103, 2, NULL, 'paid'),
    (104, 3, 500, 'paid');
~~~

SQL 使用 three-valued logic（三值逻辑）：普通比较可能为 TRUE、FALSE 或 UNKNOWN。NULL = NULL 与 NULL <> 'North' 都是 UNKNOWN，不是 TRUE 或 FALSE。WHERE 只保留为 TRUE 的行，所以把 region = NULL 当作空值搜索不会返回 Ben；应写 IS NULL。

~~~sql
SELECT name FROM customers WHERE region = NULL;
-- 空结果：NULL = NULL 得到 UNKNOWN，WHERE 丢弃

SELECT name FROM customers WHERE region IS NULL ORDER BY customer_id;
-- Ben

SELECT name FROM customers WHERE region <> 'North' ORDER BY customer_id;
-- Cy；Ben 的 UNKNOWN 不通过 WHERE

SELECT name FROM customers
WHERE region <> 'North' OR region IS NULL
ORDER BY customer_id;
-- Ben
-- Cy

SELECT name FROM customers
WHERE region IS DISTINCT FROM 'North'
ORDER BY customer_id;
-- Ben
-- Cy；此谓词把 NULL 当作一个可区分值
~~~

IS DISTINCT FROM 是可读的空值安全比较：它把 NULL 当作一个可比较状态，而不是返回 UNKNOWN。PostgreSQL 和当前 SQLite 都支持它；其他数据库可使用自己的等价谓词。若条件是“地区已知且不是 North”，上一条含 OR region IS NULL 的结果就不合语义，因此先明确业务筛选含义再写谓词。

> [!info] 先判断“未知”是否等于“零”
> Ben 的金额缺失可能表示尚未计价、上游未回填或数据质量错误；把它自动当 0 会掩盖不同问题。只有报表定义明确把“没有金额输入”解释成零贡献时，才用 COALESCE。业务解释应与 SQL 表达式一起说明。

### 左外连接的筛选条件放在哪里？

LEFT JOIN 会为每一条左表行寻找满足 ON 的右表行；如果没找到，仍保留左表行，并把右侧列补成 NULL。若“只关联已付款订单，但仍显示没有已付款订单的客户”，过滤条件应参与 ON 匹配：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id AND o.status = 'paid'
ORDER BY c.customer_id;
-- Ava | 101
-- Ben | 103
-- Cy  | 104
-- Dia | NULL
~~~

若先用客户号连接所有订单，再把 o.status = 'paid' 放到 WHERE，筛选在连接结果上执行。Ava 的 pending 订单使条件为 FALSE，不会留下；Dia 的右侧是空扩展行，NULL = 'paid' 为 UNKNOWN，也被移除；结果会像只留有已付款订单的内连接：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
ORDER BY c.customer_id;
-- Ava | 101
-- Ben | 103
-- Cy  | 104
-- Dia 消失
~~~

这两条查询表达不同的问题：第一条保留没有已付款匹配的客户及其空扩展行；第二条只保留客户与每笔已付款订单的匹配行。两条结果都可能让同一客户出现多次，并不等于客户去重清单。把条件移动到 ON 与 WHERE 不是排版差异，而是改变输出行集。

报表 42 的金额总和要包含 paid 与 pending 两种状态，因此下面的分组查询重新连接全部订单，不再加 o.status = 'paid'。连接后 Ava 有两行，其余有订单的客户各一行；随后 GROUP BY 才把每位客户的明细收拢为一个汇总行。只要保留上面的 paid 过滤，就会把 Ava 的 pending 订单 800 分漏在总额之外。

### 计数与求和各自统计什么？

在所有订单行中，COUNT(*) 统计四行；COUNT(amount_cents) 只统计非空金额，所以是三。这里限定讨论的 COUNT(expr) 只计入表达式非空的行，SUM(expr) 对非空输入求和；因此 Ben 虽有一笔订单，金额合计仍没有任何非空输入，SUM 返回 NULL。不要把这概括成每一种聚合函数都删除 NULL：例如 PostgreSQL 的 array_agg 可以把 NULL 放进数组。做左连接时，每个没有子行的客户也会获得一行空扩展记录，所以 COUNT(*) 对 Dia 是 1；要数真实订单，应使用非空主键 COUNT(o.order_id)。

~~~sql
SELECT COUNT(*) AS order_rows,
       COUNT(amount_cents) AS priced_orders,
       SUM(amount_cents) AS total_cents
FROM orders;
-- 4 | 3 | 2500
~~~

先计算单人分组：

~~~sql
SELECT c.name,
       COUNT(*) AS joined_rows,
       COUNT(o.order_id) AS orders,
       COUNT(o.amount_cents) AS priced_orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;
-- Ava | 2 | 2 | 2 | 2000
-- Ben | 1 | 1 | 0 | NULL
-- Cy  | 1 | 1 | 1 | 500
-- Dia | 1 | 0 | 0 | NULL
~~~

每一行都能从输入表复算：Ava 的 1200 + 800 = 2000；Ben 的唯一金额是 NULL，因此金额非空计数为 0、总和为 NULL；Cy 是 500；Dia 没有订单，因左连接仍有一行，所以 COUNT(*)=1，但 order_id 为空让真实订单数为 0。输入中三笔已知金额之和为 1200 + 800 + 500 = 2500，另有一笔金额未知；2500 是已知金额小计，不代表未知金额可视为零。

SUM() 没有非空输入时返回 NULL。若报表合同明确把没有金额的汇总展示为零，可写 COALESCE(SUM(o.amount_cents), 0)；否则保留 NULL 能区分“零金额”与“无有效金额数据”。

### 分组前后两种筛选各在何时执行？

WHERE 在分组前过滤 FROM / JOIN 产生的行；HAVING 在完成 GROUP BY 与聚合后筛选组。下面查询只保留金额合计至少为 500 分的客户。Ben 的 SUM 为 NULL，所以与 500 比较得 UNKNOWN，该组不通过 HAVING。

~~~sql
SELECT c.name,
       COUNT(o.order_id) AS orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING SUM(o.amount_cents) >= 500
ORDER BY c.customer_id;
-- Ava | 2 | 2000
-- Cy  | 1 | 500
~~~

先确定统计粒度是“客户”、再决定空金额的业务含义，最后用 ON、WHERE、GROUP BY、HAVING 将顺序表达出来。数据库实现与数据规模会影响查询计划，但不会把空值语义变成缺失的 0。

**接下来：** 报表 42 的唯一操作键、外键与复合访问索引见[如何用约束保护业务规则并为读取建立索引？](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F)。实际事务隔离和本地提交保证见[事务隔离与 WAL 能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - NULL 比较、IS NULL 与 IS DISTINCT FROM：[PostgreSQL 18, Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html)，§9.2；SQLite [Expressions](https://www.sqlite.org/lang_expr.html)，核对于 2026-11-06。
> - LEFT JOIN 的匹配与空扩展行：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.1；SQLite [SELECT](https://www.sqlite.org/lang_select.html)，核对于 2026-11-06。
> - WHERE、GROUP BY、HAVING 顺序与聚合函数的非空输入规则：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.2–7.2.3 与 [Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html)，§9.21；SQLite [Aggregate Functions](https://www.sqlite.org/lang_aggfunc.html)，核对于 2026-11-06。
## 8. 如何用约束保护业务规则并为读取建立索引？

**案例：** 报表服务接收账户 acct-17 的幂等请求 report-demo-208，生成任务 job-demo-731，并按账户读取最近任务状态。数据库要让每个合法操作最多对应一行、外键有真实目标、库存不能为负；读取路径还需在任务增多后可控。约束是所有写入方共享的正确性规则；索引是为某些查询维护的访问路径，只有当计划器判断成本合适时才会选择。

~~~mermaid
flowchart TD
    Write[API / relay / worker 写入] --> Rules{约束成立？}
    Rules -->|否| Reject[拒绝写入，事务不提交]
    Rules -->|是| Store[提交业务状态]
    Query[读取请求] --> Planner[计划器估算候选路径]
    Planner -->|估计省成本| Index[使用索引]
    Planner -->|扫描更划算| Scan[顺序扫描或其他计划]
    Index --> Rows[按条件返回行]
    Scan --> Rows
~~~

### 先把不变量放在数据库边界

应用输入校验能及时给用户更友好的错误；数据库约束也要校验每一次写入，防止另一个 API、定时任务或人工脚本绕开这次校验后破坏已提交数据。以下业务 schema 以 PostgreSQL 18 为例；后面的 SQLite 计划演示独立建表，不声称同一 DDL 在两个引擎上有相同类型和外键语义。primary key (主键) 唯一标识行；unique constraint (唯一约束) 防止某组键重复；foreign key (外键) 要求被引用的父键存在；NOT NULL constraint (非空约束) 阻止缺值；CHECK constraint (检查约束) 限制每一行必须满足的布尔条件。

~~~sql
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY NOT NULL
);

CREATE TABLE inventory (
    sku TEXT PRIMARY KEY NOT NULL,
    available INTEGER NOT NULL CHECK (available >= 0)
);

CREATE TABLE reservations (
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    sku TEXT NOT NULL REFERENCES inventory(sku),
    status TEXT NOT NULL CHECK (status IN ('reserved', 'cancelled')),
    PRIMARY KEY (account_id, principal_id, idempotency_key)
);

CREATE TABLE report_jobs (
    job_id TEXT PRIMARY KEY NOT NULL,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')
    ),
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (account_id, principal_id, idempotency_key)
);

INSERT INTO accounts (account_id) VALUES ('acct-17');
INSERT INTO inventory (sku, available) VALUES ('SKU-7', 1);
~~~

这里三种规则解决不同问题：available 的 CHECK 禁止负库存；reservation 的外键确保账户和 SKU 存在；report_jobs 的复合唯一键把同一账户、同一主体、同一幂等键限定为同一个逻辑提交。插入 acct-17 账户父行与 SKU-7 后，才有合法值可供 reservation 引用。键列是 NOT NULL，避免缺值绕过该业务比较。创建时间使用 TIMESTAMPTZ 表示绝对时间，不能把不同本地时区格式的任意 TEXT 直接按字典序当作时间顺序。任务 job-demo-731 可以在 queued 到 running 再到 succeeded 等已定义状态间变化，但 CHECK 只限制允许取值，并不单独验证转移顺序；转移需要由带前置状态的 UPDATE 或其他并发控制实现。ON DELETE CASCADE 是另一项独立的生命周期规则，只有业务确实要求删父行时也删掉关联子行才应选择；它不会默认发生。

> [!info] CHECK 不一定拒绝 NULL
> 在 PostgreSQL 中，CHECK 表达式只在结果为 FALSE 时拒绝行；结果为 TRUE 或 NULL 都满足约束。因此 CHECK (available >= 0) 若允许 available 为 NULL，并不能表达“必须有非负库存”。需要 NOT NULL 与 CHECK 一起约束。SQLite 还使用动态类型，普通 INTEGER 列可能存入文本；若要用 SQLite 验证同一强类型不变量，应启用 STRICT 表或加显式类型检查。SQLite 外键也必须在每个连接执行 PRAGMA foreign_keys = ON。

### 复合索引怎样配合任务列表？

报表所有者查询账户 acct-17 最近 20 个任务，按创建时间倒序；同一时间戳时用任务 ID 决定稳定顺序：

~~~
CREATE INDEX report_jobs_by_account_recent
    ON report_jobs (account_id, created_at DESC, job_id DESC);

SELECT job_id, status, created_at
FROM report_jobs
WHERE account_id = $1
ORDER BY created_at DESC, job_id DESC
LIMIT 20;
~~~

B-tree index (B 树索引) 按键列的顺序保存索引项。查询中的 $1 是 PostgreSQL 驱动绑定的账户参数。第一个键 account_id 是等值条件，后两列直接提供稳定排序，因此这个复合索引可能同时缩小扫描范围并避免额外排序。把 account_id 去掉或调到末尾后，索引就不能同样直接定位某账户的那段连续键范围。索引的列序需从真实过滤条件与排序推导；字段多并不自动更快。

UNIQUE (account_id, principal_id, idempotency_key) 通常会让数据库同时维护一条唯一索引来阻止重复键。外键查父表需要主键或唯一键，但在 PostgreSQL 中，创建外键并不会自动为子表引用列建立索引；删除账户或查某账户预留时，是否需要相应的子表索引取决于数据量与访问模式。索引只能缩短查询路径，不能替代业务授权；在服务端依然须先检查调用者是否可见任务或预留。

### 计划器为什么有时不用已建索引？

索引会占用磁盘和缓存，也会增加 INSERT、UPDATE、DELETE 时维护条目的工作。若查询预计读取表的大部分行，顺序扫描可能比逐个索引查找再回表便宜。query planner (查询计划器) 会根据表规模、分布、统计信息、谓词和输出列估算成本；估算和选择会随引擎、版本、数据与统计而变。必须用目标引擎的 EXPLAIN 检查代表性查询，不能以“索引存在”推断性能已提升。

下面在独立 SQLite 教学库保留一个计划复现：它与 NULL 章节同名的 customers、orders 表结构不同，需分别建表。这里创建 1,000 个合成订单，按一个客户筛选并按时间倒序；先检查无索引计划，再加 customer_id、placed_at 复合索引并检查。可见行数、统计信息和版本都会影响输出；本例实测计划只说明这组 SQLite 数据上的选择。

> [!example]- 用 1,000 个合成订单观察索引计划
> ~~~sql
> PRAGMA automatic_index = OFF;
> CREATE TABLE orders (
>     order_id INTEGER PRIMARY KEY,
>     customer_id INTEGER NOT NULL,
>     amount_cents INTEGER NOT NULL,
>     placed_at INTEGER NOT NULL
> );
> WITH RECURSIVE seq(n) AS (
>     VALUES(1)
>     UNION ALL
>     SELECT n + 1 FROM seq WHERE n < 1000
> )
> INSERT INTO orders
> SELECT n, n % 100, n * 25, n FROM seq;
>
> EXPLAIN QUERY PLAN
> SELECT order_id, amount_cents, placed_at
> FROM orders
> WHERE customer_id = 17
> ORDER BY placed_at DESC;
> -- 本地输出：SCAN orders；USE TEMP B-TREE FOR ORDER BY
>
> CREATE INDEX orders_by_customer_and_time
>     ON orders(customer_id, placed_at);
>
> EXPLAIN QUERY PLAN
> SELECT order_id, amount_cents, placed_at
> FROM orders
> WHERE customer_id = 17
> ORDER BY placed_at DESC;
> -- 本地输出：SEARCH orders USING INDEX orders_by_customer_and_time (customer_id=?)
> ~~~
> SQLite 3.51.0 的本地复现用于观察查询计划；不同 SQLite 版本、统计状态及不同规模的数据可能选择其他计划。PostgreSQL 的 EXPLAIN ANALYZE 会实际执行语句并报告观察到的耗时与行数，评估有写入副作用的语句前须先考虑它会真的执行。

本次计划回放观察到的变化是访问路径和排序步骤：从全表 SCAN 加临时 B-tree 排序，变成按 customer_id 的索引 SEARCH。它没有量出端到端耗时，因此只能说明 SQLite 为这组数据选择了不同计划，不能据此声称实际延迟必然下降；amount_cents 不在索引键中，这条读取也不是覆盖索引。

**接下来：** 唯一键为操作结果提供重放边界；具体怎样原子提交与处理并发见[事务隔离与 WAL 能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。SQL 空值、连接与聚合对结果行的影响见[NULL、连接与分组如何改变报表 42 的结果？](#7.%20SQL%20%E7%A9%BA%E5%80%BC%E3%80%81%E8%BF%9E%E6%8E%A5%E4%B8%8E%E5%88%86%E7%BB%84%E4%BC%9A%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E6%8A%A5%E8%A1%A8%2042%20%E7%9A%84%E7%BB%93%E6%9E%9C%EF%BC%9F)。

> [!info]- 来源
> - CHECK、NOT NULL、主键、唯一键与外键：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)，§5.5；特别是 CHECK 的 TRUE/NULL 行为，核对于 2026-11-06。
> - 复合 B-tree 的前导列条件与索引开销：[PostgreSQL 18, Indexes](https://www.postgresql.org/docs/18/indexes.html)，§11.1、§11.3；排序：[Indexes and ORDER BY](https://www.postgresql.org/docs/18/indexes-ordering.html)，§11.4；核对于 2026-11-06。
> - 计划估算与实际执行的区别：[PostgreSQL 18, EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)，核对于 2026-11-06。
> - SQLite 外键与查询计划：[SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html) 与 [EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)，核对于 2026-11-06。
## 9. 事务隔离与预写日志能保证什么？

**案例：** 报表系统中的两条请求同时预留 SKU-7 的最后一件库存，初始 available = 1。事务要把库存扣减和 reserve-demo-208 结果记录一起提交。随后连接超时只会让调用方不知道结果，数据库是否提交仍由持久记录决定。要分析这个过程，需分清一组语句的提交边界、并发事务看到的版本，以及写前日志 (write-ahead log, WAL) 在崩溃后能够恢复的状态。

~~~mermaid
flowchart TD
    Begin[开始事务] --> Predicate[条件更新 available > 0]
    Predicate -->|恰好 1 行| Insert[写入同一作用域的预留操作记录]
    Insert -->|成功| Changes[产生库存与操作记录的 WAL 变更]
    Changes --> CommitRecord[写入提交记录]
    CommitRecord --> CommitFlush[按同步提交配置持久化所需 WAL]
    CommitFlush --> Ack[确认提交]
    Changes --> PageFlush[对应 WAL 持久后，数据页可写回]
    PageFlush -.可发生在提交前或提交后.-> Pages[持久数据页]
    Predicate -->|0 行| Rollback[回滚本事务；按新事务查询操作键]
    Insert -->|作用域键唯一冲突| Rollback
    Insert -->|其他约束错误| Fail[回滚并返回明确失败]
    Crash[进程 / 主机崩溃] --> Recovery[恢复重放 WAL 并按提交状态判定可见性]
    Recovery --> Recovered[读到提交状态所证明的数据库结果]
    Ack -.响应可能丢失.-> Caller[客户端暂时无法确认结果]
~~~

### 事务把哪些写入放在同一边界？

transaction (事务) 把多条数据库语句放进同一次提交或回滚。ACID 是说明该边界的常用词，但每项都受数据库实现、配置和底层存储能力约束：

- **atomicity（原子性）**：同一事务中的写入一起提交，或由回滚一起撤销。
- **consistency（一致性）**：数据库约束和应用规则定义合法状态；事务不会自行发明业务不变量。
- **isolation（隔离性）**：并发事务按所选级别与引擎实现观察或等待其他写入。
- **durability（持久性）**：成功提交能够抵抗配置和存储承诺范围内的故障；异步提交或不可靠存储会改变这个范围。

对 SKU-7，先读 available=1 再无条件写成 0 不安全。条件更新与按账户、主体和键识别的预留结果须在同一事务中。以下使用 PostgreSQL 示例参数；$1 是 SKU-7，$2 是 acct-17，$3 是 user-17，$4 是 reserve-demo-208，$5 是 fingerprint-A，均由驱动绑定。字段与[库存基础页](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)中的 PostgreSQL schema 一致：

~~~sql
BEGIN;

UPDATE inventory
SET available = available - 1
WHERE sku = $1 AND available > 0
RETURNING available;
-- 本例按 Read Committed：成功者得到一行、值为 0；竞争者重检后得到零行。

INSERT INTO reservations
    (account_id, principal_id, idempotency_key, request_fingerprint, sku, status)
VALUES ($2, $3, $4, $5, $1, 'reserved');

COMMIT;
~~~

API 只有在 UPDATE 返回一行后才执行 INSERT；零行、作用域操作键冲突或其他写入错误都要显式 ROLLBACK。零行或作用域键冲突后，先回滚这个尝试，再在新事务按当前授权范围查询键并比较指纹；同键同指纹返回已提交结果，同键异指纹冲突，确认没有该键后才报告 SKU 不存在或售罄。提交之后若客户端连接断开，数据库行仍说明是否存在 reserve-demo-208；不能把“客户端超时”当成数据库自动回滚的信号。若 COMMIT 响应丢失，沿[请求超时后如何确认结果并安全重试？](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)的同键流程查询已提交结果，或以同键安全重放；唯一约束只能帮助裁决并发写入，不能单独给出重放响应。

### 隔离级别限制哪些并发现象？

dirty read（脏读）是读到其他事务尚未提交的写入；non-repeatable read（不可重复读）是同一事务重读一行时看到后来提交的新值；phantom read（幻读）是相同条件查询再次执行时，结果行集合因其他提交而变化；serialization anomaly（序列化异常）是一组成功事务的结果无法解释为某种串行执行顺序。SQL 标准按这些现象描述隔离级别；产品对名称的实现可能更强或采用不同并发控制，需看所选数据库具体文档。

PostgreSQL 18 的对照如下。这是该产品的行为表，不应套用于所有数据库。官方文档版本在 2026-11-06 核对为 PostgreSQL 18；本地双连接并发复现运行于 PostgreSQL 14.24，不将其描述为 18 的实测：

| PostgreSQL 18 级别 | 脏读 | 不可重复读 | 幻读 | 序列化异常 |
| --- | --- | --- | --- | --- |
| Read Uncommitted（读未提交） | 不允许，等同 Read Committed | 可能 | 可能 | 可能 |
| Read Committed（读已提交，默认） | 不允许 | 可能 | 可能 | 可能 |
| Repeatable Read（可重复读） | 不允许 | 不允许 | 不允许 | 仍可能出现写偏差 |
| Serializable（可串行化） | 不允许 | 不允许 | 不允许 | 不允许 |

在 PostgreSQL Read Committed 下，每条语句取得新快照。若两个写入请求同时以 WHERE available > 0 更新同一 SKU，后执行者会等待；前者提交后，数据库会对新行重新检查条件，available 已为 0 就更新零行。因此单条条件更新正好表达此不变量。在 Repeatable Read 下，若当前事务的快照已看见某行旧版本，而另一个事务先提交了该行的新版本，等待中的更新可能以 SQLSTATE 40001 失败；应用必须从最初读取开始重试整笔事务。如果应用把“先查、再从多行推导规则、最后分别更新”分成多个语句，则 Read Committed 每语句新快照可能让后续语句观察不同状态，复杂规则需更强保护。

### 为什么稳定快照仍可能破坏共享规则？

write skew (写偏差) 说明稳定快照不一定维护跨行规则。排班表有两名值班医生，规则要求至少一人值班。事务 A 读到两人都在岗并关闭 A 的排班；事务 B 读到相同快照并关闭 B。两者各写不同的行，因此 PostgreSQL Repeatable Read 下都可能提交，最终没人值班。

可选修法取决于规则形状：用同一行计数与条件更新将规则收敛为单行不变量；或在 PostgreSQL Read Committed 下，让所有写入方先锁定同一排班控制行，再用另一条 SELECT 语句检查状态。以 B 为例，它等 A 释放控制行后，第二条语句取得新快照并看到只剩 B 在岗，于是拒绝关闭 B 的排班。Repeatable Read 事务的快照不会因等待结束而刷新，因此这一两语句方案不能原样套用到 Repeatable Read；也可使用 Serializable 并在 SQLSTATE 40001 序列化失败后从最初读取开始重试整个事务。只重试最后一条 UPDATE 会沿用过期决策。事务中不应执行无法撤销的远端支付或直接发布消息；先写本地 outbox，提交后再投递。

> [!info] MVCC 和“无锁读取”不是同一句话
> multi-version concurrency control (多版本并发控制, MVCC) 让读取者按快照看见可见版本，同时并发写入可产生新版本，减少部分读写等待。它不取消写写冲突、显式锁或所有等待；不同引擎保留与清理版本的方式也不同。PostgreSQL 通过 VACUUM 清理不再可见的旧版本，长事务持有的旧快照可能延迟清理。

### 预写日志如何把提交与数据页写回分开？

write-ahead log (预写日志, WAL) 先记录数据更改，再允许对应数据页写回持久存储。PostgreSQL 确认同步提交前，会先持久化提交所需的 WAL；相应数据页可能已经写回，也可能仍留待稍后写回。无论何时写页，都必须先持久化足以恢复该页的 WAL。崩溃后启动恢复会重放已持久日志；若日志没有提交记录，事务写入仍不会作为已提交结果被查询到。这样可以避免每个事务提交都同步刷新所有被修改的数据页，但承诺依赖同步提交策略、文件系统、设备 flush 语义和配置。WAL 的存在本身不意味着抵御存储设备谎报写入或失去整个故障域。

WAL 与崩溃恢复不是时间点恢复的全部材料。要恢复到某个过去时点，还需要适用的基础备份和从该备份起点到目标时刻连续、完整的 WAL 归档；缺失任一段日志都会造成时间范围断裂。SQLite 采用自己的回滚日志或 WAL 模式和配置规则，不能把 PostgreSQL 的文件布局与恢复步骤直接套过去。

> [!example] 一次提交后立即崩溃时检查什么
> 对 reserve-demo-208，若数据库已按持久策略确认 COMMIT，即使数据页尚未写回，崩溃恢复也能重做已提交的库存扣减与预留记录；恢复后查询得到 available=0 和该操作记录。相反，若库存与预留的变更日志已写出但事务没有持久提交记录，即使脏页曾写回，恢复后查询仍看见 available=1 且没有该预留。若 API 在提交确认前失联，客户端只能查询权威记录来区分这两种结果。具体断电保证取决于所选引擎与存储兑现配置，而不是 HTTP 响应有没有到达。

### 哪些课程细节继续留在归档？

课程中的 ARIES 恢复推演仍保留在[WAL 与 ARIES 的逐步恢复例题](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md)：analysis（分析）阶段用 dirty page table（脏页表）记录恢复时涉及的脏页；每页的 recLSN 表示该页自上次干净后可能需要 REDO（重做）的最早日志位置，最小 recLSN 是 REDO 起点，不是分析阶段要扫描的最早日志范围。CAP 的边界是在网络分区期间，系统不能同时保证线性一致性，并保证每个非故障节点收到的请求最终都得到响应；two-phase commit (两阶段提交, 2PC) 协调多个参与者的提交决定，已进入 prepared 并投 YES 的参与者，在尚不知道协调者全局决定时可能等待。两者都不能替代单库库存原子更新、隔离级别或日志恢复。

**接下来：** SQL 约束与索引决定哪些业务状态可写、哪些访问路径可用，见[如何用约束保护业务规则并为读取建立索引？](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F)。当服务用 ORM 请求数据库时，session、事务与连接的持有时间见[如何限定 ORM Session 并诊断连接池耗尽？](#10.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。

> [!info]- 来源
> - 隔离级别异常定义、PostgreSQL 18 每语句快照、更新等待重检与 Serializable 重试：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1–13.2.3，核对于 2026-11-06；本地双连接并发实跑版本为 PostgreSQL 14.24，未在 PostgreSQL 18 实跑。
> - MVCC 版本可见性与 VACUUM：[PostgreSQL 18, Introduction to MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html)，§13.1，核对于 2026-11-06。
> - WAL 先持久日志再写数据页、提交确认不依赖所有数据页已写回、崩溃重做与基础备份加日志的时间点恢复：[PostgreSQL 18, WAL Introduction](https://www.postgresql.org/docs/18/wal-intro.html)，§28.3，[WAL Configuration](https://www.postgresql.org/docs/18/wal-configuration.html)、[Asynchronous Commit](https://www.postgresql.org/docs/18/wal-async-commit.html) 及 [Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/18/continuous-archiving.html)，核对于 2026-11-06。
> - SQLite 的本地事务与日志模式：[SQLite Transactions](https://www.sqlite.org/lang_transaction.html) 与 [Write-Ahead Logging](https://www.sqlite.org/wal.html)，核对于 2026-11-06。
> - 课程 ARIES 推导：[Mohan et al., ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging)；关联原始课程页[WAL 与 ARIES 的逐步恢复例题](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md)。
> - CAP 的网络分区边界：[Gilbert and Lynch, Brewer’s conjecture and the feasibility of consistent, available, partition-tolerant web services](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf)；两阶段提交的预备状态限制：[PostgreSQL 18, PREPARE TRANSACTION](https://www.postgresql.org/docs/18/sql-prepare-transaction.html)，核对于 2026-11-06。
## 10. 怎样限定对象关系映射会话并排查连接池耗尽？

**案例：** 请求读取报表 42，或 worker 为 job-demo-731 读取 acct-17 的报表输入。每次工作都需要一段有限的数据访问生命周期。object-relational mapper（ORM，对象关系映射器）把关系表行映射为程序对象；Session（会话）、数据库事务、单条连接和连接池是四种不同边界。连接池耗尽通常不是“数据库慢”的同义词；要顺着连接借出、事务结束和归还时间定位。

~~~mermaid
flowchart TD
    Request[请求或一个 worker attempt 开始] --> Session[创建独立 ORM Session]
    Session -->|第一次 SQL| Checkout[从进程内连接池借连接]
    Checkout --> Query[读取 / flush SQL]
    Query -->|成功| Commit[提交事务]
    Query -->|异常| Rollback[回滚事务]
    Commit --> Return[连接归还池]
    Rollback --> Return
    Return --> Close[关闭 Session]
~~~

### 会话、事务和连接各自保存什么状态？

ORM Session（ORM 会话）是一段短期工作单元：它保留本次加载或新建的映射对象、identity map（身份映射）以及待同步的更改。它不是跨请求可共享的对象缓存，也不等于一条数据库连接。修改映射对象后，Session 在查询或提交前可能 flush（刷新）这些更改为 SQL；flush 只是把语句交给当前事务执行，不等于提交已持久化。例如 `add()` 一个新对象后 `flush()`，本事务可以读取数据库生成的 ID；若随后在 `commit()` 前异常并回滚，新增行不会留下。

transaction（事务）划定一组 SQL 的 commit / rollback 边界。Session 可以在不同事务间继续存在，因此“每请求一个 Session”不会自动说明这一请求中哪几条语句必须原子提交。connection（连接）是数据库驱动通信资源；Session 通常等到第一次真正执行 SQL 时才向 Engine 借出。pool（连接池）由进程内 Engine 管理可复用连接和并发借出上限，归还连接一般是把资源放回池中重用，而不是关闭底层 TCP socket。

仓库的 [ASP.NET Core 与 EF Core 例子](../../archive/back-end/ASP.NET-Core.md) 展示了同一组生命周期在另一套 ORM 中的写法：DbSet<T> 表示实体集合；DbContext 模型决定实体怎样映射到表；默认依赖注入作用域通常为一次 Web 请求创建 DbContext，请求结束后 dispose。换成其他框架时，仍要分清对象跟踪、事务提交和驱动连接归还，不要把一种 ORM 的默认作用域当成数据库本身的规则。

### 怎样让每个请求有界地访问数据库？

以下同步 SQLAlchemy 2.0 写法假设 Report 和 AccountEvent 是已经映射的模型，示例数据库使用 PostgreSQL。认证层先用当前主体验证账户范围，并返回可信 `account_id`；URL 中的账户号不能直接充当授权凭据。读取报表、导出或重算是不同动作，读取权限不能自动推出导出权限。

~~~python
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=8,
    max_overflow=2,
    pool_timeout=2,
)

def load_report(principal_id: str, requested_account_id: str, report_id: int):
    account_id = require_account_permission(
        principal_id, requested_account_id, action="report:read"
    )
    with Session(engine) as session:
        with session.begin():
            report = session.scalar(
                select(Report).where(
                    Report.account_id == account_id,
                    Report.id == report_id,
                )
            )
            if report is None:
                return None
            return {
                "id": report.id,
                "status": report.status,
                "version": report.version,
            }

def load_account_page(account_id, start_at, end_at, after=None):
    # `account_id` and the Q2 bounds come from the authorized, persisted job.
    cursor_filter = ""
    params = {
        "account_id": account_id,
        "start_at": start_at,
        "end_at": end_at,
        "limit": 100,
    }
    if after is not None:
        cursor_filter = "AND (occurred_at, event_id) > (:after_time, :after_id) "
        params.update(after_time=after[0], after_id=after[1])

    with Session(engine) as session, session.begin():
        return session.execute(
            text(
                "SELECT event_id, occurred_at "
                "FROM account_events "
                "WHERE account_id = :account_id "
                "AND occurred_at >= :start_at AND occurred_at < :end_at "
                + cursor_filter
                + "ORDER BY occurred_at, event_id LIMIT :limit"
            ),
            params,
        ).all()
~~~

第一个函数先校验当前主体对账户的 `report:read` 权限，再用账户范围和报表 ID 定位资源；组合条件确保不会只凭 `report_id` 跨账户取行。worker 对 job-demo-731 只使用经授权并持久化的账户和时间范围，不能从队列正文接受新范围。第二个函数是 Q2 的一页：例如 `start_at=2026-04-01T00:00:00Z`、`end_at=2026-07-01T00:00:00Z`，使用左闭右开区间，并以 `(occurred_at, event_id)` 的唯一顺序分页。下一页使用 `after=(last.occurred_at, last.event_id)`；返回列的排列顺序与游标元组不同，不能直接把整行当作游标。游标值和范围都绑定为参数。worker 最多顺序读取 12 页；不足 100 行时结束，若第 12 页仍有 100 行则以范围超限失败，不能静默截断成成功报表。

每页在各自短事务中读取，所以这个例子表达的是逐页查询时可见的数据，不承诺所有页来自同一数据库快照。若产品要求报表对应一个精确时点，应在有界 `REPEATABLE READ` 事务或版本化快照中实现，并把长事务占用连接的代价纳入容量预算。不要把一次 Session 共享给并行协程、线程、另一个 HTTP 请求或整个 worker 生命周期。

使用 ORM 处理常见实体读写、关系装载和变更跟踪，前提是生成的查询形态清楚。批量更新、数据库特有语法或需要明确计划时，直接写参数化 SQL 也合适；无论由哪一层生成，主键、事务、约束与查询成本都由数据库语义决定。参见[两个请求争夺最后一件库存时，怎样保证只预留一次？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。

### 长时间持有连接怎样变成池耗尽？

典型路径是：请求创建 Session；第一次 SELECT 或 flush 才借连接并开始事务；事务执行查询或写入；提交或回滚后驱动连接归还；工作结束后 Session 关闭。SQLAlchemy 默认 autobegin（自动开始事务）：第一次访问数据库会开启事务，即使随后只是读。若在连接仍借出时等待第三方 HTTP API、流式发送长正文、排队或执行与事务无关的 CPU 工作，慢环节会占住一个连接，让后续请求等待空闲槽位。

当所有连接都被借出时，新请求在 pool_timeout 设定时间内等待；无连接归还就会超时。漏关 Session、遗留结果游标或事务、锁等待、每次请求做 N+1 查询、把慢远端调用放在事务内，都可能拉长 checkout 时长。排查时分别看 checked-out 数量、借出等待时间、池超时、事务持续时间和 SQL 耗时。直接加大池可能把等待从应用池转移到数据库，也可能突破数据库总连接预算。

对明确配置的 SQLAlchemy `QueuePool`，单进程可同时借出的连接上限为 `pool_size + max_overflow`，通常按需建立而非启动时全部打开。作为一个独立部署估算，假设 4 个副本、每个副本 3 个工作进程，每进程设置 8 个池连接和 2 个 overflow，则总上限是 `4 × 3 × (8 + 2) = 120`。这是另一个配置示例，不是账户报表架构的 200 连接预算；报表容量须把 API、worker 和其他连接使用者放进同一总预算。任何池上限都不保证数据库一定接受这些连接；每个进程通常拥有自己的池，也不应在进程 fork 后共享已打开的连接。

> [!example] 一个连接如何被占住
> 若 `QueuePool` 只有一个连接、`max_overflow=0` 且 `pool_timeout=2` 秒，请求 A 在 t=0 借到连接并在事务未结束时等待远端服务 3 秒。请求 B 在 t=0.1 到达，虽然自己的 SQL 只需 10 毫秒，但到 t≈2.1 池等待先超时，B 尚未发出 SQL；A 在 t=3 归还连接也来不及挽救 B。把远端等待移到事务外并缩短数据库工作，才能释放这个槽位。

**接下来：** Session/事务决定一次数据库访问怎样借用连接；缓存则影响哪些读取到达数据库以及读到的版本新不新。见[怎样缓存数据库读取并说明陈旧窗口？](#11.%20%E6%80%8E%E6%A0%B7%E7%BC%93%E5%AD%98%E6%95%B0%E6%8D%AE%E5%BA%93%E8%AF%BB%E5%8F%96%E5%B9%B6%E8%AF%B4%E6%98%8E%E9%99%88%E6%97%A7%E7%AA%97%E5%8F%A3%EF%BC%9F)。请求截止时间与拒绝/重试预算见[请求超时后如何确认结果并安全重试？](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - Session 的身份映射、工作单元、flush、事务边界与首次连接借用：[SQLAlchemy 2.0, Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)，示例以 2.0 API 编写；官网在 2026-11-06 同时列出 2.1.8 为当前版本、2.0.57 为 2.0 维护版本。当前版本文档见 [SQLAlchemy 2.1, Session Basics](https://docs.sqlalchemy.org/en/21/orm/session_basics.html)。
> - QueuePool、pool_size、max_overflow、等待和进程 fork 边界：[SQLAlchemy 2.0, Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)；当前版本对应的 [SQLAlchemy 2.1, Connection Pooling](https://docs.sqlalchemy.org/en/21/core/pooling.html)。
> - LIMIT 分页需要唯一排序，且不同页的排序必须稳定：[PostgreSQL 18, LIMIT and OFFSET](https://www.postgresql.org/docs/18/queries-limit.html)。
> - 每请求 Session 的 Web 模式：[FastAPI, SQL (Relational) Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)，核对于 2026-11-06。
> - QueuePool 1 槽的等待/超时复现与 flush 回滚验证使用 SQLAlchemy 2.0.44、SQLite 3.51.0；另在 PostgreSQL 14.24、SQLAlchemy 2.0.44 和 psycopg2 上执行本页两条读取路径，验证账户隔离、同时间戳跨页、季度边界和连接归还。
> - 归档 EF Core 示例只用于对照对象/请求作用域：[ASP.NET Core 与 EF Core 示例](../../archive/back-end/ASP.NET-Core.md)。
## 11. 怎样缓存数据库读取并说明陈旧窗口？

**案例：** 报表 42 的已授权展示表示可缓存在 Redis 中，返回版本 9 或 10；数据库仍是报表版本的权威来源。job-demo-731 的 `queued/running/succeeded` 状态及结果引用要读权威数据库，不能用可能陈旧的报表缓存回答。每次请求仍要检查主体对报表的读取权限，缓存键不会授予权限。选择 cache-aside（旁路缓存）后，仍需回答：写入何时失效、缓存回填可能怎样过期、Redis 故障会给数据库带来多少额外压力。time to live（TTL，存活时间）能限制单个条目的寿命，却不能单独保证全程读到最新版本。

~~~mermaid
sequenceDiagram
    participant R as 读者
    participant C as Redis 缓存
    participant D as 权威数据库
    participant W as 写入者
    R->>C: GET report:acct-17:42
    C-->>R: 未命中（miss）
    R->>D: 读取 version 9
    D-->>R: 报表 42，version 9
    W->>D: 提交 version 10
    W->>C: DEL 缓存键
    R->>C: 回填刚才读到的 version 9，设置 30 秒 TTL
    Note over C: 失效发生后，旧版本再次获得新 TTL
~~~

### 一次读取和写入会经过哪些状态？

读取通常是：先 GET 缓存键；命中（hit）时取出缓存表示；未命中（miss）时查询主数据库；查询成功后再写入带 TTL 的缓存并返回。Redis 常用 GET、SET key value EX seconds、DEL 和 TTL 实现这些步骤。若数据库确定返回“报表不存在”，可以用几秒的短 TTL 缓存负结果；不要把超时、拒绝或数据库故障缓存成“不存在”。创建资源后也要删除对应负缓存。

写入应先在数据库提交新的权威状态，再删除缓存键。若反过来先删除缓存，随后读者可在旧数据库值上回填旧缓存。如果数据库提交成功而 Redis DEL 失败，旧值会持续到过期或后续失效；Redis 命令和数据库事务不是跨系统原子操作。对允许短暂陈旧的展示页，明确可接受年龄后可用短 TTL；对授权、余额和需要立即读己之写的操作，应绕过缓存读权威源或明确返回暂时不可用。

缓存键必须包含所有能改变返回表示的范围，例如租户、资源 ID、语言或筛选条件。报表如果按主体返回不同字段，缓存键也要有相应主体范围；即使键包含租户，缓存命中仍不能代替逐次主体/租户授权。见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

### 为什么存活时间不等于一致性保证？

图里的竞争顺序还可以按时钟复算：t=0，R 未命中并从数据库读到版本 9；t=1，W 提交版本 10 并执行 DEL；t=3，仍在途的 R 把此前读到的版本 9 设为 30 秒 TTL；该键到 t=33 才到期。因此 t=1 提交后，读者最晚可能在接近 32 秒后仍命中版本 9。竞态的关键是先前读到的旧值在 DEL 后才完成回填；若后续陈旧回填来自别的在途读取或本地副本，新的 SET 还会重新开始各自 TTL，不能说一次竞态必然持续回填。

若一个接口必须读己之写，可以在成功写入后绕过缓存读取，或将新版本号与无效化事件一起传播，使回填不得覆盖更高版本。跨数据库和 Redis 需要排序/条件写的设计时，须明确处理乱序、进程崩溃与重复失效；单独执行 DEL 不能提供这种原子版本协议。

> [!info] 负载计算也属于缓存策略
> 命中率只说明多少次读取绕过了数据库；一次失效风暴可能同时让大量请求变成未命中。比如某热键到期后，100 个并发请求都回源，一次正常读被放大成 100 次数据库读取。缓存方案要同时控制陈旧窗口和回源并发。

### 缓存击穿和 Redis 故障怎样限制？

热门键同时过期会产生 cache stampede（缓存击穿）。单进程内可以将同一键并发未命中合并成一个加载者，并给不同键的 TTL 加小幅随机抖动，减少整批键同时到期；这不协调多个进程。需要跨进程协调时，可使用有界租约的短锁，但等待要有截止时间。释放锁必须用 Redis Lua 脚本或等价原子命令，在一个原子操作里比较随机 token 并且只删除匹配的锁；若先比较、暂停、再单独 DEL，租约过期后旧持有者可能删掉新持有者的锁。锁只是减少重复加载，不能成为数据正确性的证明。

Redis 整体不可用时，应用无法读取仅存放在 Redis 的旧值；它可以在请求 deadline（截止时间）、并发回源上限和数据库连接预算内回源，或返回暂时不可用。若另有本地快照，只有端点允许该陈旧上限、且应用能核对快照实际年龄时才可返回；超出业务可接受范围就回源或失败。缓存故障应被监控，不要静默把数据库错误当成空值。

**接下来：** ORM Session 与连接池决定回源数据库的借出压力，见[如何限定 ORM Session 并排查连接池耗尽？](#10.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。高成本报表任务和故障后的确定结果见[怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

> [!info]- 来源
> - Redis cache-aside 的 cache-first、miss 回源、TTL 与更新失效：[Redis cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/)，核对于 2026-11-06；该页将 TTL 描述为受限陈旧窗口，跨数据库一致性方案属于应用设计。
> - Redis 的 SET 过期参数、DEL、TTL 与锁机制：[Redis Commands](https://redis.io/docs/latest/commands/)；按 Redis 官方当前文档核对于 2026-11-06。
> - 释放租约时比较锁 token 并原子删除，避免删除其他持有者的锁：[Redis Distributed Locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)；该页也列出 Redis 8.4 的 `DELEX ... IFEQ` 与较早版本 Lua 写法。
> - 报表展示的失效竞态、主体授权与 job 状态读取边界是本章应用设计；没有部署 Redis 服务做在线故障测试。
## 12. 请求超时后如何确认结果并安全重试？

**案例：** reserve-demo-208 条件扣减 SKU-7 的最后一件库存，数据库提交后 HTTP 响应丢失。调用方看到超时，但不知道请求没到服务器、事务回滚，还是扣减已经提交。网络超时描述的是“调用方没收到结果”，不是“数据库没有执行”；解决方法是为逻辑操作分配稳定身份，并把操作结果和本地效果一并持久化，使客户端可查询或按契约重放同一操作。

~~~mermaid
sequenceDiagram
    participant C as 客户端
    participant A as API
    participant D as 数据库
    C->>A: reserve-demo-208，预留 SKU-7
    A->>D: 条件扣减 + 写操作结果
    D-->>A: 同一事务提交，库存变 0
    A--xC: 响应在途中丢失
    Note over C: 客户端结果未知，不能据此断言回滚
    C->>A: POST 原预留请求，沿用同一键和相同参数
    A->>D: 按作用域键读取或裁决同键并发
    D-->>A: 返回已提交结果；不再扣库存
    A-->>C: 返回原结果
~~~

### 超时和截止时间让调用方处于什么状态？

timeout（超时）限定一次等待或操作的时长；deadline（截止时间）是整条调用链最晚允许完成的时间点。每经过一层都重新开始完整 timeout，会让多个串行下游调用的总耗时远超最初预算。服务应传递剩余时间或截止时限，并为清理和响应留出时间。连接建立、TLS 和响应读取是否都包含在一次库的 timeout 内，要按客户端 API 检查。

当写入被接受而响应丢失，调用方得到的是 unknown outcome（未知结果）：它无法从自己的连接状态区分“请求没到”与“效果已提交但响应丢失”。reserve-demo-208 的权威记录已是 `reserved`，`available` 从 1 变 0；客户端没有一个按此键查询的 GET 契约，因此重放原 POST，并沿用相同作用域键与相同参数，服务端返回已记录结果而不再扣减。若读取查询暂时查不到记录，这只表示当前可见快照没有已提交结果，并不能证明原事务已经回滚或不在进行。只有明确允许幂等重放的写请求，才能用同一键和同一参数安全重试；单纯的只读状态查询不应意外启动原操作。

HTTP 202 Accepted 是另一种显式状态：API 确认任务已受理，但没有表示已完成。账户报表契约没有按幂等键查询的 GET；若 202 响应丢失，客户端用相同 `report-demo-208` 和相同请求正文重放 POST，服务返回已存在的 `job-demo-731` 与状态 URL，再 GET 该已知 URL。连接断开不会自动取消已经持久接受的 job；需要取消时使用明确的取消请求。完整作业生命周期见[怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 怎样定义可安全重放的幂等键？

idempotency key（幂等键）是客户端为一次逻辑意图生成并在重试时保持不变的标识。服务必须定义它的唯一范围、保留时间、请求参数关系和结果重放规则。账户报表示例把键作用域定义为 (account_id, principal_id, key)；不能让另一个主体靠猜到键读取私有结果。服务还保存规范化请求指纹：同一个键、同一参数返回已存结果；同一键却换了 period 或 format，则返回明确冲突，不能默默把旧结果解释成新意图。

RFC 9110 对 HTTP 方法的幂等性定义为：重复一次或多次相同请求，其预期服务端效果等同于只执行一次；这不禁止每次请求分别记录日志。它是 HTTP 方法的语义。给某个 POST 另加稳定幂等键，则是应用层的去重和结果重放约定，两者不能互相代替。

去重记录和本地数据库效果必须处于同一事务；若扣库存提交后才单独写 reserve-demo-208 操作记录，中间崩溃会让重试无法识别原操作：本例最后一件已被扣完时会误报无库存；若其后补货，重试还可能再次扣减。对同键并发，先查询再插入不够：两个请求可能都看见“没有记录”。要由唯一约束裁决一方；失败方回滚本次条件扣减，再读取胜者提交的结果。服务还要明确保证的重放窗口，并在窗口内保留识别同一键所需的记录。窗口过后若删掉所有信息，服务无法仅凭键字符串判断它是旧操作还是新意图；若要拒绝任何过期旧键，就得继续保留可验证的墓碑。窗口外的重试保证必须写清楚，调用方不能把旧操作当成新请求重做。

若操作会调用外部支付或发消息，单库事务无法覆盖远端系统。durable outbox（持久发件箱）只让本地结果与待发布指令一起提交，并使 relay 能在崩溃后重发；它不会替远端付款去重。真正的资金效果仍需要收款方按相同业务键幂等处理，或通过权威对账识别重复。超时不自动撤销远端副作用。

### 重试时间和总工作量怎样受控？

只对可能暂时失败且重复执行安全的操作重试。使用有上限的 exponential backoff (指数退避) 并加入 full jitter（全抖动），避免所有客户端同时再试：

~~~text
cap(n) = min(max_delay, base_delay × 2^n)
wait(n) = 从 0 到 cap(n) 均匀随机选择
~~~

假定 base_delay 为 100 ms、max_delay 为 800 ms，前几次等待区间依次为 0–100 ms、0–200 ms、0–400 ms；客户端实际次数还须受剩余 deadline 限制。若最多 3 次尝试，初次请求失败后只在剩余预算装得下下一次调用和必要回包时重试。base、上限和次数是服务策略，不是通用常数。避免多个调用层各自重试：5 层各做 3 次会把一次逻辑请求放大为 3⁵ = 243 次下游调用。

> [!example] 响应截止时间下的重试复盘
> 客户端总截止时间为 2 秒，第一次（共最多 3 次尝试中的第 1 次）请求用了 1.2 秒后超时，剩余 0.8 秒。第一次失败后的退避是 `n=0`，所以等待上限为 100 毫秒；下一次调用至少需要 700 毫秒，并为处理/返回预留 50 毫秒，能容纳的等待最多只有 `800−700−50=50` 毫秒。若全抖动抽到 80 毫秒（合法，因为低于 100 毫秒），总计要 `80+700+50=830` 毫秒，超过剩余预算，应停止并把状态留作未知。最多 3 次尝试包括初次调用，因此总共最多只有两次退避，后续上限才是 200 毫秒。

### 取消如何作为协作式信号？

cancellation（取消）是通知仍在运行的工作“结果不再需要”。把信号传给下游，并在安全检查点停止多余计算、释放资源；不同运行时能否中止远端调用取决于 API。对已返回 202 且已持久接受的账户报表，浏览器断开只结束这次连接，不会取消后台 job；客户端必须向已知 job URL 显式请求取消。尚未接受的请求级工作则可在断开后结束。取消也不证明已经提交的数据库副作用回滚，提交状态仍要从权威业务记录确认。

**接下来：** 账户报表把幂等键、202、outbox 和后台尝试组合成一个可长期查询的流程，见[怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。队列发布确认与消费者 acknowledgement 的 broker 语义归[发布者确认和消费者确认分别证明什么？](#14.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)，连接借用预算归[如何限定 ORM Session 并排查连接池耗尽？](#10.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。

> [!info]- 来源
> - HTTP 幂等方法与 202 受理语义：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§9.2.2、§15.3.3，核对于 2026-11-06。
> - 副作用、超时、重试安全与请求令牌：[AWS Builders’ Library, Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)，核对于 2026-11-06。
> - timeout、backoff 与 jitter：[AWS Builder Center, Timeouts, retries, and backoff with jitter](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter)，原文 2019-12-05，核对于 2026-11-06。
> - deadline 传播和协作式取消：[gRPC Deadlines](https://grpc.io/docs/guides/deadlines/)，核对于 2026-11-06；具体行为仍取决于各 API。
## 13. 怎样设计一个可持久查询的账户报表？

**案例：** 用户为账户 acct-17 请求报表 42，统计有限时间范围内的账户活动并导出 CSV。任务可能超出一次 HTTP 请求的时限；用户断开浏览器后仍要能查询结果，且结果保留七天。请求只读账户数据，但会消耗查询、连接、worker（工作进程）和对象存储资源。这里使用 `report-demo-208` 作为客户端幂等键，`job-demo-731` 作为持久任务 ID；账户与报表共同标识报表资源，报表 ID 42、任务 ID 和请求键是三个不同身份。

设计从用户结果、硬约束和负载开始，再选满足要求的最小架构。若一次有界同步读取总能在调用方截止时间内完成，直接返回报表更简单；若任务可能更久、需在断连后继续，或要独立准入突发工作，才引入持久 job（任务）、队列和 worker（工作进程）。这不是生产测量：本例沿用容量页的教学假设——平均 5 次提交/秒、10 分钟峰值 20 次/秒、worker 平均处理 6 秒、每请求约 8 KiB、至多 12 次顺序数据库读取、平均结果 128 KiB、结果保留七天。可由请求参数预先判定的范围超限，在接受任务之前拒绝；实际读取时若到第 12 页仍未取完，worker 停止并写入有界失败状态，不继续无上限读取；报表只读账户活动，不改写账户业务数据。所有用户可见路径都要重新授权；系统要限制未开始任务和数据库连接，并持久记录成功、失败或取消结果。

### 如何接受请求并让用户查询结果？

一个可用的 HTTP API（HTTP 应用接口）契约如下：

~~~http
POST /v1/accounts/acct-17/reports
Idempotency-Key: report-demo-208
Content-Type: application/json

{"reportId":42,"period":"2026-Q2","format":"csv"}

HTTP/1.1 202 Accepted
Location: /v1/jobs/job-demo-731

{"jobId":"job-demo-731","status":"queued","cancelRequested":false,"statusUrl":"/v1/jobs/job-demo-731"}
~~~

`202 Accepted` 只表示已接受处理，不表示任务完成或最终必然成功。客户端之后可 `GET /v1/jobs/job-demo-731` 查询状态，`DELETE /v1/jobs/job-demo-731` 表示请求取消并保留可查询的 job 资源；若任务已终结，返回当前终态。只有成功且结果尚在保留期内，才可通过 `GET /v1/jobs/job-demo-731/result` 取回私有结果。`report.version` 表示报表展示数据的版本；job 的 `status` 和 `attempt` 表示这次导出的生命周期，两组字段不能互相推导。每个端点先验证当前调用者身份，再检查其是否可为 acct-17 创建/导出报表、访问该任务或读取其结果；路径中的账户号和难以猜测的 job ID 都不是授权凭据。`report:read` 不自动授予 `report:export`。worker 使用范围受限的服务身份，并在读取报表数据前重新验证提交主体当前仍有该报表的导出权限；若已撤销，就写入有界的 `authorization_revoked` 失败状态而不读取数据。接口的成功和错误表示应服从[HTTP API 契约](#3.%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F)；断线后的未知结果如何查证见[请求超时后如何确认结果并安全重试？](#%E8%B6%85%E6%97%B6%E5%92%8C%E6%88%AA%E6%AD%A2%E6%97%B6%E9%97%B4%E8%AE%A9%E8%B0%83%E7%94%A8%E6%96%B9%E5%A4%84%E4%BA%8E%E4%BB%80%E4%B9%88%E7%8A%B6%E6%80%81%EF%BC%9F)。

idempotency key（幂等键）在本例按 `(account_id, principal_id, key)` 唯一；同键还绑定规范化请求指纹，其中包含 `reportId=42`、时间范围和格式。若键与指纹都匹配，返回已存在的 job；同键但 `reportId`、时间段或格式不同，则按本例契约返回冲突。仅先查再插入不能关闭竞态：两个相同请求可能都查不到。数据库唯一约束裁决胜者；失败方先回滚整笔事务，不新增等待槽，再读取胜者 job 并比较指纹。既有键的重放只返回原 job，不重新准入或占用第二个槽。请求指纹只用于比较，worker 重启所需的标准化报表参数必须另行持久保存。不要把原始请求正文或敏感筛选条件塞进队列消息。

本例把成功结果对象保留 7 天，从 `succeeded` 与对象引用一同提交、结果对用户可见时起算；job 状态和最小幂等映射保留到终态后 14 天，以覆盖更长的客户端重试窗口。结果对象过期时，job 仍是 `succeeded`，结果端点返回 `result_expired`，同键请求仍指向原 job，绝不重建一次导出。14 天后删除幂等映射就不再有窗口外重放保证；若服务要拒绝任意旧键，必须继续保留可识别它的墓碑。调用方在约定窗口外应先查证旧操作，不能把同一键当成全新意图。

job 行至少保存稳定的 job ID、账户与请求主体、`report_id`、已验证的标准化报表参数、请求指纹和幂等键、创建/到期时间、状态、取消请求、attempt（尝试号）、`lease_expires_at`（租约到期时间）、等待槽保留状态、私有结果引用以及范围受限的错误码。

| 持久状态 | 含义与转移 |
| --- | --- |
| `queued` | 请求已提交，尚无 worker 领取当前排队轮次；可以仍待 outbox（事务型发件箱）发布，也可以已经在队列中。每个排队轮次持有一个等待槽。 |
| `running` | worker 已通过 conditional update（条件更新）领取当前尝试，等待槽已释放。`lease_expires_at` 到期使恢复器可以尝试接管；到期本身不自动撤销当前尝试。 |
| `succeeded` | 当前尝试的私有对象已写好，数据库已将结果引用与成功状态一起提交。 |
| `failed` | 不可重试错误或尝试耗尽后写入的终态，客户端能查询有界错误码。 |
| `cancelled` | 取消在完成提交之前生效的终态；不暴露结果对象引用。 |

`cancel_requested` 是独立布尔字段，不是任务状态：运行中的任务可保持 `running` 同时收到取消请求。终态一经提交就不再变成其他终态。租约到期后，恢复器按数据库当前时间才有资格提交接管；原 worker 在接管事务成功提交之前仍可能完成，租约时刻本身不撤权。成功、取消和恢复接管都用条件更新比较当前 `status`、`attempt` 与 `cancel_requested`，并只接受更新一行的胜者；先提交的一方决定后续状态。恢复器若赢得条件更新，则把尝试标为已取代，旧 worker 后续完成更新会因状态或 attempt 不匹配而失败。outbox（事务型发件箱）另有 `pending` / `published` 状态；`published` 表示 relay（中继器）已按选定 broker 的确认、路由和持久性契约记录发布结果，不表示 worker 已处理或 job 仍处于 `queued`。队列消费者的 acknowledgement（消费者确认，ACK）也不属于 job 状态。

### 任务、发件箱与队列怎样交接？

在同一个数据库事务中插入唯一 job、`pending` outbox 行，并原子预留一个共享等待槽；仅在计数未达到 240 时提交，否则回滚并在 **202 之前**拒绝过载请求。所有 API 副本都通过同一数据库计数规则争用槽位。队列载荷只需携带 job ID；每个 outbox 发布意图还需自己的唯一 ID 和发布状态，relay 只确认对应意图，不能让旧发布确认覆盖重新排队产生的新意图。等待槽跟随逻辑 job 的当前排队轮次：任务尚未被 worker 领取时，不论仍在 outbox 还是已经排入 broker，都只占一个槽；重排再次占一个槽，领取时释放；一条消息被重复投递也不新增槽位。

~~~mermaid
flowchart TD
    A[认证、授权并校验报表范围] --> T[同一数据库事务：job、outbox、一个等待槽]
    T -->|提交成功| R[返回 202 与稳定状态 URL]
    T -->|槽满或键冲突| X[回滚：拒绝过载，或查询同键结果]
    T -->|提交后| L[relay 发布 job ID]
    L --> Q[broker 按所选契约确认发布]
    Q --> O[outbox 标为 published；job 状态独立推进]
~~~

发布确认只结束发送端的一步。消费者继续按持久 job 状态推进：

~~~mermaid
flowchart TD
    Q[收到 job ID] --> W[条件领取：running、增加 attempt、释放等待槽]
    W --> Read[按已存参数读取有界数据]
    Read --> Obj[写当前 attempt 专属的私有对象]
    Obj --> Guard{仍是当前 attempt，且没有取消？}
    Guard -->|是| Done[提交 succeeded 与对象引用]
    Guard -->|否| Orphan[不发布此对象；按权威状态取消或延后]
    Done --> Ack[终态持久后确认消息]
~~~

读写失败、重复投递和租约超时不会跳过这些边界；下面分别说明它们怎样恢复。


数据库提交与队列发布是两个系统的写入，不能放进一个普通数据库事务。若先提交 job 后直接发布，进程可能在两步之间崩溃，导致永远无人处理的任务；若先发消息再提交，数据库回滚后队列会出现不存在的任务。outbox 把 job 和待发布记录一起提交；relay 读取并重试发布，只有按所选 broker 的契约验证发布确认、路由与所需持久性条件后才更新 outbox。relay 若在 broker 接收后、更新 outbox 前崩溃，可能再次发布，所以 worker 按 job ID 幂等领取；已确认的 outbox 行也要按保留策略清理。发布者确认和消费者 ACK 是两个独立边界；即使 relay 记录 `published`，worker 也可能已经领取任务甚至写入终态。数据库事务不覆盖 broker，也不覆盖对象存储。[队列确认页](#14.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)详解 broker 语义。

> [!example] job-demo-731 的一次正常完成
> 在这个明确的顺序示例中，relay 先验证所选 broker 契约并更新 `outbox=published`，之后 worker 才领取；因此这一时刻 `job=queued`、等待槽占用 1。worker 原子领取后，job 变成 `running`、attempt=1，等待槽归还。worker 写私有对象并提交结果引用后，job 才变成 `succeeded`；消费者随后按 broker 契约确认消息。真实系统中 worker 可能在 relay 更新 `published` 前就已领取，因此 outbox 状态、job 状态和消费者确认不能互相推导。

### 工作进程重试怎样避免旧结果覆盖新结果？

worker 领取任务时，以条件更新检查状态仍为 `queued`，递增 attempt 并设置有界租约，同时释放这个排队轮次的等待槽。另一个当前 attempt 仍持有任务时，重复投递不能另起并行工作，应按所选队列契约延后或确认重复消息。worker 崩溃后，恢复器用数据库当前时间检查 `lease_expires_at`，再按 `job_id` 和 attempt 做条件接管：先检查 `cancel_requested`；若已请求取消，直接写 `cancelled`，无需争用槽位。否则只有恢复任务取得一个新的共享等待槽，才能在同一数据库事务中把 job 改回 `queued` 并写入新的 `pending` outbox 发布意图；relay 持续重发该意图直到满足选定 broker 契约。若无槽，写入可查询的 `capacity_exhausted` 终态，但不能把已取消任务写成容量失败。该闭环确保只改 job 行不会让消息凭空重新可达；新旧重复消息都由条件领取规则消重。

attempt fencing（尝试号栅栏）以单调递增的 attempt 号隔离新旧 worker；每次 attempt 用不同、只创建一次的对象键，例如 `reports/job-demo-731/attempt-2.csv`。先将私有对象写入该键，再用 compare-and-set（比较并交换，CAS）条件更新，比较 `job_id`、`status='running'`、当前 `attempt` 和 `cancel_requested=false`。只有恰好更新一行，才提交 `succeeded` 和对象引用并让结果对用户可见；零行表示接管、取消或终态已先提交。worker 不以 `lease_expires_at` 到期时刻单独拒绝自己，胜负由这些持久条件更新的提交顺序决定。对象写入与数据库仍是两个持久系统；上传后进程崩溃可能留下未引用对象，但垃圾回收不能只按“当前无引用”立即删除：只有 attempt 已被接管或 job 已终结、数据库确认无引用，并且有上界的上传时限和额外安全宽限都已过去，才可回收。即使已失效的旧 worker 仍晚到上传，其对象也不能获得有效结果引用；后续清理仍需处理这类迟到的孤儿对象。S3 的 `If-None-Match: *` 是一种防止同名对象被覆盖的条件写法；本设计依赖的是“每次尝试使用不同键，且仅由数据库当前 attempt 引用”，并不要求选 S3。

具体时序：worker A 领取 attempt 1 后停顿，租约到期但恢复器尚未接管；此刻 A 仍可能先提交成功。若恢复器先提交接管事务，job 变回 `queued` 并新增 outbox 意图，随后 B 领取 attempt 2；A 再恢复时，`WHERE attempt = 1 AND status = 'running'` 更新零行，不能引用自己的对象。若 B 已发布结果引用，A 的不同对象键也不能覆盖它。对象是否可见由数据库当前 attempt 的条件提交决定，租约到期时间本身不作栅栏。

取消只是请求停止，并非证明计算已停止。API 将 `cancel_requested=true` 持久化；若 `queued` 任务仍占有当前排队轮次的槽位，API 可用条件状态转移将其置为 `cancelled` 并释放该槽，之后到达的重复消息只按权威终态处理。领取与取消若同时竞争同一行，条件状态更新决定唯一结果：取消先提交时，worker 不能再领取；领取先提交时，任务转为 `running`，worker 随后检查取消标志。若 `running` 任务收到取消后 worker 崩溃，恢复器过期接管时先写 `cancelled`，不会重新排队或因槽位不足写容量失败。运行中的 worker 还要在有界数据页之间以及发布结果前检查。worker 的完成更新与取消终态更新都比较当前 attempt 和取消字段：如果取消先提交，当前尝试不再能转为成功；若成功终态先提交，后到的取消请求返回当前终态。浏览器断开只结束连接；202 已持久接受的 job 会继续，只有向 `DELETE /v1/jobs/{id}` 显式请求取消才改变任务状态。202 之前尚未被接受的请求级工作可以在断开后结束。

### 何时应排队，怎样设容量边界？

若代表性报表稳定满足调用方截止时间和尾部时延目标，同步接口更简单：校验输入、执行有界查询、返回 CSV，无需 queue、outbox relay、worker、状态轮询和结果清理生命周期。任务可能超过请求预算、必须在断连后可查，或突发流量需要与 API 执行隔离时，才选择异步路径。队列能保存等待和隔离故障，但不会凭空增加处理能力。

沿用[容量与背压页](#23.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)的估算：64 个 worker 槽、准入目标 7 次/秒、30 个任务的短时突发，以及共享上限 240 个已接受未开始任务；应用连接池总上限是 200。若把峰值 20 次/秒持续按平均 6 秒处理，平均需要约 `20 × 6 = 120` 个并发 worker；64 个槽不能长期消化该到达率，因此准入规则要限流/拒绝，等待队列也不能无界增长。未开始任务包括 outbox 中尚未发布的任务。若 broker 暂时不可用，已接受任务仍占槽；槽已满时 API 必须在 **202 之前**返回过载错误。数据库不可用时无法持久接受任务，也不能声称已受理。

> [!info] 用平均到达率估算并发，不等于压测结果
> Little's law（利特尔法则）给出稳态关系：平均在途任务数约等于平均到达率乘以平均处理时长。若 20 次/秒持续到达且每项平均 6 秒，`20 × 6 = 120` 是近似并发需求；它不包含长尾、突发与失败重试，不能替代压测和限流。

部署与运行时保留以下检查：API、relay 与 worker 的任务表结构兼容，使升级期间旧任务仍可完成；按本例分开的 7 天结果与终态后 14 天状态/幂等元数据策略清理；限制重试数、对象上传时长和每次工作时长；监测 API 接受时延、pending outbox 的最老等待时间、数据库中最老 `queued` job 年龄、broker 最老消息年龄与深度、活跃 worker 槽、任务完成分位数、连接池等待与 SQL 耗时、对象存储用量、重试、取消和终态结果。broker 队列指标正常不能证明数据库中没有积压；`pending outbox` 或 `queued` 年龄持续增长都表示处理路径跟不上。发布时保留回滚路径，并考虑已经按旧 schema 接受的任务。


**继续阅读：** [数据库约束与索引](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F)说明唯一键与查询路径；[事务隔离与 WAL](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)说明数据库内提交边界；[数据访问与连接池](#10.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)说明每个请求/attempt 的 ORM 与连接生命周期；[HTTP 协议与 WebSocket](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F)说明客户端状态查询的传输边界；[可观测性、服务目标与事件响应](#31.%20How%20do%20you%20diagnose%20an%20API%20SLO%20violation?%20/%20%E5%A6%82%E4%BD%95%E8%AF%8A%E6%96%AD%20API%20SLO%20%E8%BF%9D%E7%BA%A6%EF%BC%9F)说明阶段指标。更长的设计检查清单见[AI 系统设计案例](../../ai-engineering/systems/ai-system-design-interview-questions.md)。

> [!info]- 来源
> - `202 Accepted` 表示已接受但尚未完成的 HTTP 语义：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§15.3.3，核对于 2026-11-06。
> - 同一数据库事务内的提交边界、唯一约束和并发行为：[PostgreSQL 18, Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html)、[Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) 与 [Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，核对于 2026-11-06。
> - 数据库与消息通知的双写故障、outbox 重复发布及消费者幂等：[AWS Prescriptive Guidance, Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)，核对于 2026-11-06。
> - 发送端 publisher confirms 与消费端 acknowledgements 是两个独立边界；RabbitMQ 的 unroutable/持久消息行为：[RabbitMQ 4.4, Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)，核对于 2026-11-06；本架构只要求按最终选择的 broker 契约确认。
> - 按对象名防止覆盖的条件写入示例：[Amazon S3, Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)，核对于 2026-11-06；S3 只是可选实现。
> - 从需求、约束与运行目标选择架构：[Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework)，核对于 2026-11-06。
## 14. What do publisher confirms and consumer acknowledgements prove? / 发布者确认和消费者确认分别证明什么？

A publisher confirm and a consumer acknowledgement cover different handoffs. A publisher confirm says the broker accepted a publish under its own configured rules; it does not say a consumer performed the business operation. A consumer acknowledgement tells the broker that the consumer reached the chosen processing boundary. If either confirmation is lost, work may be repeated, so make the business effect idempotent and acknowledge only after its durable outcome. / 发布者确认和消费者确认覆盖不同的交接边界。发布者确认表示 broker 按自身配置规则接受了消息，并不表示 consumer 已执行业务操作。消费者确认告诉 broker，consumer 已达到系统选定的处理边界。任一确认丢失都可能造成重复处理，因此业务效果应可幂等，并且只有在持久化业务结果后才确认消息。

**Key terms / 关键术语：** publisher confirm / 发布者确认；consumer acknowledgement / 消费者确认；redelivery / 重投；deduplication / 去重；ordering / 顺序；dead-letter queue / 死信队列。

~~~mermaid
sequenceDiagram
    participant P as Publisher
    participant B as Broker
    participant C as Consumer
    participant D as Business store
    P->>B: Publish message
    B-->>P: Confirm broker acceptance
    B->>C: Deliver message
    C->>D: Commit idempotent business effect
    D-->>C: Durable outcome
    C->>B: Acknowledge delivery
    Note over P,B: Lost confirm may cause publisher retry and duplicate publish
    Note over C,B: Crash after commit but before ack may cause redelivery
~~~

The sequence has two separate ambiguity windows. If the broker accepted a publish but its confirmation did not reach the publisher, the publisher may resend and create a duplicate. If the consumer commits its effect and then crashes before acknowledging, the broker may redeliver the message. If the consumer acknowledges before durable work, a crash can lose the work. The application therefore needs stable message or operation identity and an idempotent effect; queue delivery alone is not proof of business completion.

### Publisher confirmation / 发布者确认

Publisher confirms cover the publisher-to-broker boundary under the broker's rules. They do not know whether a consumer received, acknowledged, or completed the message. The publisher must also distinguish a broker confirmation from a routing guarantee: depending on broker and configuration, acceptance by an exchange may not mean that the message reached the intended queue.

With RabbitMQ, a publisher that has not received a confirm when a connection fails cannot know whether the message was accepted; retrying may duplicate it. For routable persistent messages, what the confirm means depends on the message and queue type; consult the configured queue's durability and replication semantics. A confirm is not a transaction across the publisher's database and the broker. Persisting business state and an outbox row together, then publishing from that outbox, handles that separate database-to-broker dual-write problem. The account-report implementation is in [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F).

### Consumer acknowledgement and redelivery / 消费者确认与重投

Choose the consumer's acknowledgement point from the business completion contract. If processing consists of a database update, make that update idempotent by message ID or operation key. A crash after database commit but before broker acknowledgement can then trigger redelivery without repeating the effect. The database commit and broker acknowledgement usually cannot share one local transaction, so this remaining duplicate window is expected.

With RabbitMQ 4.3 manual acknowledgements, an unacknowledged delivery is requeued when its channel or connection closes. Consumers must be ready for redelivery. This is a broker-specific behavior, not a universal queue rule. Acknowledging before durable work can lose work; acknowledging after durable work can cause redelivery if the acknowledgement is lost, so processing should tolerate duplicates.

A dead-letter queue makes repeatedly failed messages visible only if it is monitored and someone has defined whether to repair, retry, or discard them. Immediate requeue can create a hot retry loop, so define bounded attempts or delayed retry behavior. Keep the application operation's idempotency record and any relevant status query separate from the queue's delivery state.

### Preserve the order the business needs / 保留业务需要的顺序

Concurrent consumers may finish messages in a different order from delivery. A FIFO queue does not automatically serialize all effects across multiple consumers, retries, or partitions. If completion order is a correctness rule, define its scope—often per account or key—and enforce it with a single ordered partition, per-key sequence, conditional state transition, or serialization at the worker. Confirm the chosen broker's exact delivery and ordering contract.

Observe each boundary separately: publish attempts and confirms, unroutable messages, queue depth and oldest-message age, unacknowledged deliveries, retries and redeliveries, acknowledgements, dead-letter volume, and completed business outcomes. A growing oldest-message age indicates delay even while a queue continues accepting work. [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#23.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) explains how to constrain the work waiting behind those boundaries.

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) covers ambiguous request outcomes and operation idempotency; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F) applies outbox, attempt fencing, and post-outcome acknowledgement to a report job; [Database Fundamentals / 数据库基础](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F) covers the local transaction boundary used to persist business effects.

**Sources / 来源：** RabbitMQ 4.3, [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms) and [Reliability Guide](https://www.rabbitmq.com/docs/reliability), checked 2026-11-05. These references document RabbitMQ's confirm, manual-ack, redelivery, and publisher retry behavior; other brokers have different contracts.
## 15. 何时选择轮询、SSE、流式 Fetch 或 WebSocket？

报表查看者已请求刷新报表 42，接下来要决定怎样收取进度。选择取决于消息方向、请求形状、连接生命周期和恢复要求：轮询重复发普通 HTTP 请求；Server-sent Events (SSE，服务端事件) 用一个 HTTP 响应单向发送事件；流式 Fetch 让应用控制请求与读流；WebSocket 让连接两端主动发消息。重连只恢复连接，不保证所有事件都被应用处理；恢复需要服务端保留日志并接受游标，或客户端重新读取权威状态。

~~~mermaid
flowchart TD
    Need{报表端要发送，客户端也要连续发送消息吗？}
    Need -->|否，低频或客户端控制更新| Poll[轮询或长轮询]
    Need -->|否，服务端单向推送| Shape{普通 GET 是否满足请求需求？}
    Shape -->|是| SSE[SSE + EventSource]
    Shape -->|否| Fetch[Fetch 响应流]
    Need -->|是，持续双向消息| WS[WebSocket]
    Poll --> Recover[定义游标、重放或状态查询]
    SSE --> Recover
    Fetch --> Recover
    WS --> Recover
    Recover --> State[恢复报表当前状态或业务事件]
~~~

### 先按更新方向和请求形状选方式

| 方式 | 请求与方向 | 断线恢复由谁负责 | 适用边界 |
| --- | --- | --- | --- |
| 短轮询 | 客户端每隔一段时间发普通请求，返回当前状态或差异 | 客户端控制间隔、退避和停止；API 定义结果与游标 | 更新少且简单性重要；轮询频率过高会浪费请求，间隔过长会延迟发现变化 |
| 长轮询 | 客户端请求后，服务端等到事件或等待期限返回；客户端再发下一条 | 应用重新请求并带序号/游标；代理超时和断线仍须处理 | 需要兼容普通 HTTP 又要降低空轮询；等待请求占用连接和服务资源，须设上限 |
| SSE + EventSource | `GET` 建立 `text/event-stream` 响应，主要收服务端消息 | EventSource 通常自动重连；服务端依游标和保留日志重放 | 服务端单向推送、原生重连方便；原生 API 不接受自定义请求头或请求体 |
| 流式 Fetch | 一次 Fetch 的 body 分块可读；请求可按 API 契约带方法、头和正文 | 应用实现线格式解析、重试、游标、退避和取消 | 需要自定义请求头/Bearer 或 POST 查询后接收流 |
| WebSocket | 握手后客户端与服务端都可主动发完整消息 | 应用定义重连、认证过期、序号、确认和重放 | 双向低延迟交互值得维持长连接；协议不提供业务去重和恢复 |

还要估计连接数、更新频率、消息大小、后台休眠行为和服务端连接容量。一名客户端每秒两次轮询约 2 请求/秒，一万名客户端约 20,000 请求/秒；这只估计请求数，不代表 CPU、网络或数据库开销相同。容量与准入见[Web 服务如何限制拒绝服务的影响？](#24.%20Web%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%8B%92%E7%BB%9D%E6%9C%8D%E5%8A%A1%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F)。

### SSE 怎样从一致的快照位置续读？

`text/event-stream` 使用 UTF-8 文本，事件字段按行组织，以空行结束一条完整事件。`event` 命名类型，`data` 放内容，`id` 提供重连时可携带的游标，`retry` 可建议重连等待时间。网络包、HTTP 帧和 Fetch 读出的块都不是应用事件边界；客户端要按 SSE 语法解析。

**案例状态：** 在较早的时刻，浏览器曾缓存报表 42 的版本 8 并向服务器验证。之后一次新的刷新已启动；现在客户端从权威接口取得版本 9 的快照，状态为 `running`，且该快照已包含事件日志至游标 103。快照和游标必须来自同一一致性位置；否则两者之间刚发生的事件可能被跳过。

~~~http
GET /api/reports/42 HTTP/1.1
Accept: application/json
~~~

~~~json
{"id":42,"version":9,"status":"running","progress":0,"event_cursor":"103"}
~~~

客户端首次订阅时以应用约定的查询参数告诉服务器从快照游标之后读取：

~~~http
GET /api/reports/42/events?after=103 HTTP/1.1
Accept: text/event-stream
~~~

服务器发送事件 104，表示报表进入生成阶段；稍后报表完成，写入事件 105：

~~~text
id: 104
event: report.updated
data: {"report_id":42,"version":10,"status":"running","progress":80}

id: 105
event: report.updated
data: {"report_id":42,"version":11,"status":"ready","progress":100}

~~~

对应的浏览器订阅可以是：

~~~javascript
const source = new EventSource('/api/reports/42/events?after=103');
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
source.addEventListener('error', () => showConnectionState(source.readyState));
~~~

假定客户端已解析 104、随后连接断开；服务器日志仍保存 105。EventSource 重连时浏览器会把解析到的最后事件 ID 放入 `Last-Event-ID`。本例规定：重连请求的该字段优先于初连 URL 中的 `after=103`，服务器从 104 之后读取并重放 105。初次订阅用 URL 参数，因为原生 EventSource 不让页面设置 `Last-Event-ID` 请求头。

~~~mermaid
sequenceDiagram
    participant C as 浏览器
    participant S as 报表服务
    participant L as 事件日志
    C->>S: GET /api/reports/42/events?after=103
    S->>L: 读取 103 之后的事件
    L-->>S: 104、105
    S-->>C: 事件 104
    Note over C,S: 连接断开，日志仍保留 105
    C->>S: GET /api/reports/42/events?after=103，Last-Event-ID: 104
    S->>L: 按应用约定优先采用 Last-Event-ID
    L-->>S: 重放 105
    S-->>C: report.updated，version 11，ready
~~~

**游标和状态版本不是同一个编号。** `104`、`105` 是事件日志位置，用于从历史中续读；`version=10`、`version=11` 是报表状态修订，只有产品保证版本单调时，界面才可用它丢弃较旧状态。快照版本 9 已涵盖日志游标 103，因此后续状态更新从 104 开始。

`Last-Event-ID` 只表示浏览器解析了某个 SSE 事件并将 ID 作为重连位置；它可能在应用事件处理器完成前已更新，不能证明 `showStatus`、本地持久化或用户确认成功。若每一条事件都必须被业务处理，应用还需按订阅范围持久化已处理的 ID、去重并显式确认；传输本身不提供端到端只处理一次。若界面只需要最新状态，事件版本单调时可合并更新，并在重连后 GET 权威快照。

游标过期时服务器不能悄悄跳过缺口。本例的重置政策是发送一条完整 SSE 事件并终止当前流：

~~~text
event: reset
data: {}

~~~

`data` 字段和结尾空行不可省略，否则标准 EventSource 不会派发这条事件，客户端的 `reset` 处理器也不会运行。客户端收到后关闭 EventSource，重新 GET 快照和 `event_cursor`，再带新游标订阅。若服务器收到一次新的 SSE 请求后直接以 HTTP 204 响应，EventSource 会停止自动重连；这不是把已经开始的 200 流改成 204。断开原因和授权状态仍应由应用契约说明。每次初连或重连都要重新授权读取报表 42。

### 流式 Fetch 如何分开解析完成和传输 EOF？

当原生 EventSource 的 GET、Cookie 认证或请求字段不满足 API 需要时，Fetch 可以用 POST 提交筛选条件，再读 SSE 格式或其他明确线协议。`reader.read()` 可能只拿到半个 UTF-8 字符或半条事件；parser 要把片段缓冲到完整事件边界。此有限查询约定服务端最后发送并以空行结束以下终止事件：

~~~text
event: result.complete
data: {}

~~~

`data` 字段和结尾空行不可省略；parser 只在完整终止事件中识别它。EOF 之前没收到该事件表示查询响应截断。`decoder.decode()` 只冲刷 UTF-8 解码状态，不能代替 parser 判断应用事件是否完整。持续订阅遇到 EOF 则按游标重连。

下面的 parser 是本例接口约定：`feed()` 只向调用方交付已完整结束的事件，`hasTerminalEvent` 仅在解析到完整 `result.complete` 事件后为真，`finish()` 检查未闭合事件并拒绝截断结果。它不是浏览器内置 SSE parser。

~~~javascript
const response = await fetch('/api/reports/42/events/search', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer token-supplied-by-the-application',
    Accept: 'text/event-stream',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ stage: 'rendering' }),
  signal,
});
if (!response.ok || !response.body) throw new Error('HTTP ' + response.status);
if (!response.headers.get('content-type')?.startsWith('text/event-stream')) {
  throw new Error('Unexpected stream media type');
}

const reader = response.body.getReader();
const decoder = new TextDecoder();
let completed = false;
let stoppedEarly = false;
try {
  while (true) {
    const result = await reader.read();
    if (result.done) {
      parser.feed(decoder.decode()); // 只完成最终 UTF-8 解码
      parser.finish();               // 拒绝未以空行结束的尾部事件
      if (!parser.hasTerminalEvent) throw new Error('Truncated event stream');
      completed = true;
      break;
    }
    parser.feed(decoder.decode(result.value, { stream: true }));
    if (parser.hasTerminalEvent) {
      stoppedEarly = true;
      await reader.cancel();
      break;
    }
  }
} catch (error) {
  if (!stoppedEarly) {
    try { await reader.cancel(error); } catch { /* 保留原读取或解析错误 */ }
  }
  throw error;
} finally {
  reader.releaseLock();
}
if (!completed && !stoppedEarly) throw new Error('Incomplete search result');
~~~

`result.complete` 说明这次有限搜索流按 API 契约结束，不等于任何独立的持久报表作业已生成；作业完成要查询其权威状态。Fetch 收到响应头后正文仍可能失败，因此必须读到完整终态；跨源请求仍受 CORS 与凭据模式约束。

### WebSocket 适合哪些双向消息？

浏览器 WebSocket 先握手，再切换到双向消息协议。HTTP/1.1 常用 Upgrade 和 101；HTTP/2、HTTP/3 有各自扩展连接承载方式，不能概括为“升级到 TCP”。WebSocket 消息可跨多个帧，但消息确认、幂等处理、游标和掉线重放仍由应用定义。原生 WebSocket API 不会自动重连，调用方要在应用层实现退避、重新认证和游标恢复。

浏览器构造器接受 URL 与子协议，不开放任意自定义请求头。若握手使用 Cookie，恶意页面可能尝试建连；服务端须按策略检查 Origin、认证连接，并在每条敏感消息上逐次授权。WebSocket 不用 Fetch 的 CORS 响应许可机制，但仍有来源风险。代理超时、网络切换、客户端挂起和服务端资源都会限制连接寿命。

> [!example]- Node.js WebSocket 广播示例
> 下例展示连接集合与广播的最小形状。它不实现认证、租户隔离、消息校验、限速、去重、重连或恢复，不代表完整生产服务。
>
> ~~~javascript
> const { WebSocketServer, WebSocket } = require('ws');
> const server = new WebSocketServer({ port: 3000 });
> const clients = new Set();
>
> server.on('connection', (socket) => {
>   clients.add(socket);
>   socket.on('message', (data, isBinary) => {
>     for (const client of clients) {
>       if (client !== socket && client.readyState === WebSocket.OPEN) {
>         client.send(data, { binary: isBinary });
>       }
>     }
>   });
>   socket.on('close', () => clients.delete(socket));
> });
> ~~~

### 断线后如何确定报表状态？

先决定客户端需要“当前状态”还是“每一条事件”。当前状态可在断线后 GET 报表/作业资源，再从版本和游标建立新订阅；每一条变化都重要时，服务端要保留可重放日志并定义重复、缺口、过期和确认方式。初始快照必须一并交付与之对齐的事件游标，否则读快照和订阅之间可能漏变化。

SSE 可以自动重连，WebSocket 需要应用自己重连，Fetch 也要由应用重新发请求；它们都不能证明数据库副作用是否提交，也不能恢复服务进程内丢失的任务状态。遇到未知完成结果，应查稳定的状态资源，见[请求超时后如何确认结果并安全重试？](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - SSE 线格式、EventSource 重连、Last-Event-ID 更新、204 停止重连与事件解析：[WHATWG HTML Living Standard, Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)，§9.2，按 2026-11-05 版本核对。
> - Fetch 请求与响应体、取消和流处理：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，§2、§4；[Streams Standard](https://streams.spec.whatwg.org/)，§4；持续维护规范，核对于 2026-11-06。
> - 浏览器 WebSocket API：[WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/)，§2；握手和消息帧：[RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)，§4–§5；HTTP/2 承载扩展：[RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)；HTTP/3 扩展：[RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)，均核对于 2026-11-06。
> - Node.js `ws` 服务端广播：[ws README, Server broadcast](https://github.com/websockets/ws#server-broadcast)，核对于 2026-11-06。库文档描述该实现，不是协议规范。
## 16. When should work use a thread, process, or asynchronous I/O? / 何时选线程、进程或异步 I/O？

**Core model / 核心模型：** A process is an operating-system resource and protection boundary; a thread is an execution path inside a process. Threads share much of that process's memory and therefore need coordination when they update shared state. Concurrency means work overlaps in time; parallelism means work executes at the same time on multiple processing units. Asynchronous I/O can provide concurrency without assigning one thread to every waiting operation. / 进程是操作系统管理资源并隔离地址空间的边界；线程是在进程内执行指令的路径。线程共享进程中的许多内存，因此并发修改共享状态时需要协调。并发表示任务的执行时间重叠；并行表示多个处理单元同时执行任务。异步 I/O 可以在不为每个等待中的操作分配一个线程的情况下提高并发能力。

~~~mermaid
flowchart LR
    Wait[Many tasks waiting for I/O] --> Async[Async I/O lets one thread schedule progress]
    CPU[CPU-heavy work] --> Parallel[Worker thread or process for parallel execution]
    Shared{Must share mutable state?} -->|yes| Thread[Thread plus synchronization]
    Shared -->|no, or stronger isolation needed| Process[Separate process plus IPC]
~~~

**Key terms / 关键术语：** process / 进程；thread / 线程；address space / 地址空间；concurrency / 并发；parallelism / 并行；blocking I/O / 阻塞 I/O；non-blocking I/O / 非阻塞 I/O；asynchronous I/O / 异步 I/O；race condition / 竞态；deadlock / 死锁；cancellation / 取消。

### Process and thread / 进程与线程

| Aspect / 维度 | Process / 进程 | Thread / 线程 |
| --- | --- | --- |
| Memory / 内存 | Has its own virtual address space in the usual process model. Processes can explicitly map shared memory. / 通常拥有独立的虚拟地址空间；也可以显式映射共享内存。 | Threads in one process share its address space and global data; each thread has its own execution state and stack. / 同一进程中的线程共享地址空间和全局数据；每个线程有自己的执行状态和栈。 |
| Communication / 通信 | Uses an explicit boundary such as a pipe, socket, message, or shared mapping. / 通过管道、套接字、消息或共享映射等显式边界通信。 | Can pass references through shared memory, but concurrent access must follow a synchronization rule. / 可通过共享内存传递引用，但并发访问必须遵循同步规则。 |
| Typical choice / 常见选择 | Prefer when a fault or trust boundary matters, or work needs separate process lifetime. / 当故障或信任隔离、独立进程生命周期很重要时考虑使用。 | Prefer when work benefits from shared process state or CPU-parallel execution and the program can manage synchronization. / 当工作需要共享进程状态或 CPU 并行执行，且程序能管理同步时考虑使用。 |

These are useful defaults, not cost or isolation guarantees for every operating system. A process can deliberately share memory or handles; a thread does not automatically make CPU work faster. For Node-specific choices among its event loop, worker threads, and child processes, see [Node.js Fundamentals / Node.js基础](#17.%20How%20does%20Node.js%20schedule%20work%20across%20its%20event%20loop,%20workers,%20and%20processes?%20/%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F).

### Concurrency, parallelism, and I/O / 并发、并行与 I/O

Tasks are **concurrent** when their progress overlaps—for example, a server starts another request while the first waits for a response. They are **parallel** when instructions from both tasks execute at the same instant on separate cores or other processing units. A single event-loop thread can coordinate many waiting I/O operations, but a long synchronous callback still prevents that thread from running other callbacks. CPU parallelism needs another execution resource, such as a worker thread or process.

| I/O style / I/O 方式 | What the caller observes / 调用方观察到的行为 |
| --- | --- |
| Blocking / 阻塞 | The calling thread waits until the operation can make progress or completes. / 调用线程等待操作可以继续或完成。 |
| Non-blocking / 非阻塞 | An attempt returns promptly when it cannot proceed; the caller can wait for readiness or try again. A non-blocking result does not itself mean the full transfer completed. / 暂时无法继续时，调用立即返回；调用方可等待就绪或稍后重试。非阻塞返回本身不表示数据已经全部传输完成。 |
| Asynchronous / 异步 | The caller submits work and receives a later completion or callback. The runtime may use operating-system readiness, a completion facility, or a worker pool. “Async” describes the interface and scheduling relationship, not one universal implementation. / 调用方提交工作，随后接收完成通知或回调。运行时可能使用操作系统就绪通知、完成机制或工作线程池。“异步”描述接口与调度关系，并不对应唯一实现。 |

In Node.js, synchronous filesystem APIs block the event-loop thread. Callback- and promise-based filesystem APIs use libuv's thread pool except `fs.FSWatcher`; many network operations are driven by the operating system. Exact APIs have their own contracts. Async I/O therefore helps waiting workloads, but moving CPU-heavy JavaScript off the event loop requires workers or processes. See the [Event Loop / 事件循环](../../frontend/runtime/event-loop.md) note for scheduling details.

### Races and deadlocks / 竞态与死锁

A **race condition / 竞态** exists when the result depends on the timing or order of operations that access shared state. For example, an increment is a read–modify–write sequence: two workers can both read `10`, compute `11`, then each write `11`, losing one increment. Protect the invariant with a lock, an atomic operation, a single owner that processes messages, or a database constraint—whichever matches the boundary. In JavaScript, synchronous code in one event-loop turn runs to completion, but state can still change between `await` points; worker threads that share a `SharedArrayBuffer` need an explicit synchronization protocol.

A **deadlock / 死锁** occurs when tasks wait in a cycle. If worker A holds lock L1 and waits for L2 while worker B holds L2 and waits for L1, neither can continue. Consistent lock ordering and short critical sections prevent many such cycles. Avoid holding a lock while waiting on network or other unbounded work; a timeout can reveal a stuck wait, but does not by itself restore a partially changed invariant.

### Cancellation and cleanup / 取消与清理

Cancellation is a request to stop work, not proof that work has stopped or that its side effects were undone. Many APIs use cooperative cancellation: code checks a token, stops at a safe boundary, and releases resources or leaves shared state consistent. In POSIX threads, deferred cancellation is the default and takes effect at cancellation points; asynchronous cancellation can interrupt code while it holds a resource. Runtime and API contracts differ, so check whether the operation actually observes cancellation. In particular, cancelling a caller's wait does not retract a request that a remote service already accepted.

### A runnable shared-counter example / 可运行的共享计数示例

The two workers below share one integer. `Atomics.add` makes each read–modify–write increment one synchronized operation; after both workers exit, the expected count is `200000`. Without an atomic operation or another coordination rule, increments can be lost.

~~~javascript
const { Worker, isMainThread, workerData } = require('node:worker_threads');

if (isMainThread) {
  const shared = new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT);
  const workers = Array.from(
    { length: 2 },
    () => new Worker(__filename, { workerData: shared }),
  );

  const waitForExit = worker => new Promise((resolve, reject) => {
    worker.once('error', reject);
    worker.once('exit', code => {
      if (code === 0) resolve();
      else reject(new Error(`worker exited with code ${code}`));
    });
  });

  Promise.all(workers.map(waitForExit)).then(() => {
    console.log(Atomics.load(new Int32Array(shared), 0));
  }).catch(error => {
    console.error(error);
    process.exitCode = 1;
  });
} else {
  const counter = new Int32Array(workerData);
  for (let i = 0; i < 100_000; i++) Atomics.add(counter, 0, 1);
}
~~~

Verified with Node.js v26.11.1; observed output: `200000`. This checks one local runtime example, not performance scaling or every platform's worker implementation.

**Related notes / 相关笔记：** [Node.js Fundamentals / Node.js基础](#17.%20How%20does%20Node.js%20schedule%20work%20across%20its%20event%20loop,%20workers,%20and%20processes?%20/%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F) applies these process and worker boundaries to Node's APIs; [Event Loop / 事件循环](../../frontend/runtime/event-loop.md) explains how queued callbacks make progress on a JavaScript thread.

**Sources / 来源：** POSIX.1-2024 [General Information, process and thread model](https://pubs.opengroup.org/onlinepubs/9799919799/functions/V2_chap02.html); Linux [`pthreads(7)`](https://man7.org/linux/man-pages/man7/pthreads.7.html), for Linux/POSIX thread-sharing and cancellation-point details; Node.js v24 [worker_threads](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html) and [filesystem](https://nodejs.org/docs/latest-v24.x/api/fs.html#threadpool-usage) documentation, checked 2026-10-15. The filesystem docs specify that callback and promise APIs except `fs.FSWatcher` use libuv's thread pool.
## 17. How does Node.js schedule work across its event loop, workers, and processes? / Node.js 如何在事件循环、工作线程与进程之间调度工作？

**Core answer / 核心回答：** Use asynchronous APIs for I/O waits; one event-loop thread runs JavaScript callbacks and a long synchronous callback blocks it. Move CPU-heavy JavaScript to a bounded worker pool, and use child processes when process isolation matters. The choice changes memory sharing, communication, fault boundaries, and shutdown duties. A worker pool also needs a bounded admission policy; see [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#23.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F). / I/O 等待通常使用异步 API；JavaScript 回调在事件循环线程上运行，长时间同步回调会阻塞它。CPU 密集型 JavaScript 可交给有界 worker 池；需要进程隔离时可使用子进程。不同选择会改变内存共享、通信、故障边界与关闭责任。

**Key terms / 关键术语：** event loop / 事件循环；isolate / 隔离环境；worker thread / 工作线程；child process / 子进程；cluster / 多进程服务；IPC / 进程间通信。

### What's the difference between a process and a thread?

**进程 / Process** is an operating-system execution boundary with its own virtual address space. **线程 / Thread** is an execution path inside a process; threads can share process memory, so shared mutable data needs coordination.

Node has a JavaScript event-loop thread for each isolate, not one JavaScript thread for the whole machine. A worker thread runs JavaScript in another isolate in the same process. It can exchange messages, transfer an ArrayBuffer, or share a SharedArrayBuffer; shared memory requires explicit synchronization such as Atomics. A child process has a separate process address space and communicates through IPC or other operating-system channels.

Node also uses background mechanisms for asynchronous work: network I/O is commonly driven by the operating system, while selected APIs such as filesystem operations, cryptography, compression, and some name-resolution work use libuv's worker pool. Their JavaScript callbacks run on the event-loop thread. CPU-heavy JavaScript on that thread delays other callbacks.

For the reusable process/thread model of address spaces, shared resources, concurrency, I/O, and cancellation, see [Processes, Threads, and Concurrency / 进程、线程与并发](#16.%20When%20should%20work%20use%20a%20thread,%20process,%20or%20asynchronous%20I/O?%20/%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F); this note applies it to Node's event loop and worker choices.

---

### How do you use multiple CPU cores in Node.js?

Choose based on the work and isolation needed:

- **Worker threads / 工作线程** run CPU-intensive JavaScript in parallel and can communicate by message or shared memory. Use a bounded worker pool for repeated tasks rather than creating one thread per small job.
- **Child processes / 子进程** run in separate process memory and provide stronger isolation; IPC messages are a boundary to account for.
- **Cluster / 多进程服务** starts multiple Node processes that can accept connections on the same server port. It is one deployment option for multi-core servers, not a guarantee of linear throughput scaling or balanced work.

Built-in asynchronous I/O is usually a better choice for I/O-bound work than worker threads. For process or worker choices and shared-state trade-offs, see the linked Node.js API documentation.

An external process manager is optional. PM2 is one choice for starting and observing clustered workers:

~~~bash
pm2 start app.js --name api -i max
pm2 list
pm2 monit
pm2 reload api
~~~

PM2 may fall back from a cluster reload to a restart if it cannot complete it. The application must handle shutdown and drain or close its own work; availability during reload is not guaranteed.

#### Child process example

This compact CommonJS example runs the same file in a child process and sends one task over the fork IPC channel. It is illustrative; production code also needs workload limits, error handling, and shutdown policy.

~~~javascript
const { fork } = require('node:child_process');

if (process.argv[2] === 'worker') {
  process.on('message', ({ n }) => {
    let a = 0;
    let b = 1;
    for (let i = 0; i < n; i++) [a, b] = [b, a + b];
    process.send({ result: a });
  });
} else {
  const child = fork(__filename, ['worker']);
  child.on('message', message => {
    console.log(message.result);
    child.disconnect();
  });
  child.send({ n: 10 });
}
~~~

#### Cluster example

Each worker is a separate process. Restarting workers, health checks, graceful shutdown, and shared session state are application or process-manager responsibilities; the cluster module does not make in-memory state shared.

~~~javascript
const cluster = require('node:cluster');
const http = require('node:http');
const { availableParallelism } = require('node:os');

if (cluster.isPrimary) {
  for (let i = 0; i < availableParallelism(); i++) cluster.fork();
  cluster.on('exit', (worker, code, signal) => {
    console.error('worker exited', worker.id, code, signal);
  });
} else {
  http.createServer((request, response) => {
    response.end('Hello');
  }).listen(8000);
}
~~~

Workers have separate heaps. If a session, cache, or connection map must be shared, choose a deliberate external store, routing strategy, or message-broadcast mechanism. A Redis store is one option, not a universal requirement.

---


**Related questions / 相关问题：** [Node.js event-loop phases and microtasks / Node.js 事件循环阶段与微任务](#18.%20How%20do%20Node.js%20event-loop%20phases%20and%20microtask%20queues%20interact?%20/%20Node.js%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E9%98%B6%E6%AE%B5%E4%B8%8E%E5%BE%AE%E4%BB%BB%E5%8A%A1%E9%98%9F%E5%88%97%E5%A6%82%E4%BD%95%E4%BA%A4%E4%BA%92%EF%BC%9F) explains host scheduling; [How do Node.js streams propagate backpressure? / Node.js 流如何传播背压？](#19.%20How%20do%20Node.js%20streams%20propagate%20backpressure?%20/%20Node.js%20%E6%B5%81%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%E8%83%8C%E5%8E%8B%EF%BC%9F) explains chunk flow and cleanup; [How should a Node.js service drain on shutdown? / Node.js 服务如何排空并关闭？](#20.%20How%20should%20a%20Node.js%20service%20drain%20on%20shutdown?%20/%20Node.js%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E6%8E%92%E7%A9%BA%E5%B9%B6%E5%85%B3%E9%97%AD%EF%BC%9F) covers in-flight work and resource closure; [What does serverless leave to the application? / 无服务器计算仍要求应用负责什么？](#What%20the%20runtime%20still%20leaves%20to%20the%20application%20/%20%E8%BF%90%E8%A1%8C%E5%B9%B3%E5%8F%B0%E4%BB%8D%E7%95%99%E7%BB%99%E5%BA%94%E7%94%A8%E7%9A%84%E8%B4%A3%E4%BB%BB) describes provider-managed execution environments.
**Sources / 来源：** Node.js v24 documentation for [worker threads](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html), [child processes](https://nodejs.org/docs/latest-v24.x/api/child_process.html), [cluster](https://nodejs.org/docs/latest-v24.x/api/cluster.html), [filesystem](https://nodejs.org/docs/latest-v24.x/api/fs.html), [crypto](https://nodejs.org/docs/latest-v24.x/api/crypto.html), [zlib](https://nodejs.org/docs/latest-v24.x/api/zlib.html), and [DNS](https://nodejs.org/docs/latest-v24.x/api/dns.html); [PM2 Quick Start](https://pm2.keymetrics.io/docs/usage/quick-start/) and [cluster mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/), checked 2026-10-15.
## 18. How do Node.js event-loop phases and microtask queues interact? / Node.js 事件循环阶段与微任务队列如何交互？

Node runs JavaScript callbacks on an event-loop thread while libuv coordinates timers and I/O through phases. Node's next-tick queue and the Promise/queueMicrotask microtask queue are separate scheduling mechanisms; their order depends on where code runs. Give the Node version and execution context before stating an order. / Node 在事件循环线程上运行 JavaScript 回调，libuv 则通过多个阶段协调计时器和 I/O。Node 的 nextTick 队列与 Promise/queueMicrotask 微任务队列是不同的调度机制，执行上下文会影响它们的先后顺序。说明 Node 版本与执行位置后，再给出顺序规则。

**Key terms / 关键术语：** event-loop phase / 事件循环阶段；poll / 轮询阶段；microtask / 微任务；process.nextTick / nextTick 队列；CommonJS / CommonJS 模块；ES module / ES 模块；timer threshold / 计时器阈值。

~~~mermaid
flowchart TD
    subgraph loop[libuv event-loop phases]
        Timers[Timers] --> Pending[Pending callbacks]
        Pending --> Poll[Poll: I/O]
        Poll --> Check[Check: setImmediate]
        Check --> Close[Close callbacks]
        Close --> Timers
    end
    Operation[Current JavaScript operation completes] --> Tick[Node drains nextTick queue]
    Tick --> Micro[Node drains microtask queue]
    Micro --> LoopNext[Event loop continues]
~~~

The diagram is a simplified loop outline. The idle and prepare phases are internal. A JavaScript operation's completion handling occurs around the loop and is not itself another libuv phase. ES module evaluation already runs within microtask processing, which explains why the top-level CommonJS and ES module examples below differ.

### What the event-loop phases do / 事件循环阶段各自做什么

| Phase | Main role |
|---|---|
| Timers | Run timer callbacks once their minimum delay threshold has passed; the requested delay is not an exact deadline. |
| Pending callbacks | Run certain I/O callbacks deferred from an earlier loop iteration. |
| Poll | Retrieve and process I/O events; it may wait for I/O when appropriate. |
| Check | Run callbacks scheduled with setImmediate. |
| Close callbacks | Run selected close events, such as a socket close after abrupt destruction. |
| Idle and prepare | Internal libuv phases. |

In libuv 1.45.0, used by Node.js 20 and later, timers run after poll on each loop iteration; earlier versions also ran timers before poll. This changes some timer/immediate timing relationships. At top level, do not rely on a fixed order between setTimeout(fn, 0) and setImmediate(fn). Inside an I/O callback, setImmediate runs in the check phase after poll; the official guide describes it as running before the timer in that situation.

~~~javascript
const fs = require('node:fs');

// At top level, the order can vary.
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));

// Inside an I/O callback, setImmediate runs in the check phase.
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timer after I/O'), 0);
  setImmediate(() => console.log('immediate after I/O'));
});
~~~

### How do nextTick and microtasks differ by module context? / nextTick 与微任务顺序如何受模块上下文影响？

The nextTick queue is drained after the current JavaScript operation finishes and before the event loop continues. Promise handlers and queueMicrotask callbacks use the microtask queue. In CommonJS top-level execution, nextTick callbacks run before Promise/queueMicrotask callbacks. ES module evaluation itself runs as microtask work, so its top-level Promise/queueMicrotask callbacks run before nextTick callbacks.

| Context | Ordering for the calls below |
|---|---|
| CommonJS top level | process.nextTick, Promise reaction, queueMicrotask |
| ES module top level | Promise reaction, queueMicrotask, process.nextTick |

~~~javascript
// Save as example.cjs
const { nextTick } = require('node:process');

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
// Checked output on Node.js v26.11.1:
// nextTick
// promise
// microtask
~~~

~~~javascript
// Save as example.mjs
import { nextTick } from 'node:process';

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
// Checked output on Node.js v26.11.1:
// promise
// microtask
// nextTick
~~~

Current Node.js documentation marks process.nextTick as Legacy and recommends queueMicrotask for most userland deferrals. A recursively replenished nextTick queue can starve I/O because the loop cannot reach poll until the queue drains. Keep nextTick only when its particular scheduling boundary is required by existing API behavior.

One historical use is making a callback-based API consistently asynchronous, including validation errors, so the caller can finish setting up state before the callback runs. Another is emitting a readiness event on the next tick so callers can register a listener after construction:

~~~javascript
const { EventEmitter } = require('node:events');

function createEmitter() {
  const emitter = new EventEmitter();
  process.nextTick(() => emitter.emit('ready'));
  return emitter;
}

const emitter = createEmitter();
emitter.on('ready', () => console.log('ready'));
~~~

Use queueMicrotask for ordinary portable deferral unless the API depends on nextTick-specific ordering. These rules describe Node's host queues; they do not define browser scheduling. [Asynchronous JavaScript / 异步 JavaScript](../../frontend/javascript/asynchronous-javascript.md) covers Promise behavior outside Node's host phases.

**Related notes / 相关笔记：** [Node.js scheduling and worker choices / Node.js 调度与 worker 选择](#17.%20How%20does%20Node.js%20schedule%20work%20across%20its%20event%20loop,%20workers,%20and%20processes?%20/%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F) applies these host queues to server workloads; [Processes, Threads, and Concurrency / 进程、线程与并发](#16.%20When%20should%20work%20use%20a%20thread,%20process,%20or%20asynchronous%20I/O?%20/%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F) explains the execution resources used for CPU work.

**Sources / 来源：** [Node.js event-loop phases and timer behavior](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick) and [Node.js v26 process.nextTick / queueMicrotask guidance](https://nodejs.org/api/process.html#when-to-use-queuemicrotask-vs-processnexttick), checked 2026-11-05. The CJS and ESM output examples were checked on Node.js v26.11.1; the libuv timer phase change is documented for libuv 1.45.0 (Node.js 20).
## 19. How do Node.js streams propagate backpressure? / Node.js 流如何传播背压？

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

**Related notes / 相关笔记：** [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#23.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) applies the same bounded-work rule to requests, worker slots, and durable queues.
## 20. How should a Node.js service drain on shutdown? / Node.js 服务如何排空并关闭？

Graceful shutdown is an application lifecycle, not something the event loop or HTTP server performs for every dependency. On a shutdown signal, mark the instance unready and have each request handler reject work before enqueueing it; this also catches requests on already-open keep-alive connections. Then stop accepting connections, let tracked handlers and response streams finish, cancel work at the deadline, and close pools, workers, timers, and other owned resources after their users have stopped. Pass `workAbort.signal` to cancellable handlers and track accepted work so `waitForInFlightWork()` has a real completion condition.

**核心解释（中文）：** 收到关闭信号后先摘除就绪并拒绝新任务，再停止接入、等待已接收请求和后台工作排空；到期后发出协作取消并强制关闭 HTTP 连接。服务端关闭与跟踪任务都结算后，再回收它们使用的资源；即使其中一项失败，也要完成清理并报告错误，且在生命周期和清理报告结束前保留截止计时器。

**Key terms / 关键术语：** readiness / 就绪状态；in-flight work / 在途工作；graceful shutdown / 优雅关闭；deadline / 截止时间；cooperative cancellation / 协作式取消；owned resources / 应用拥有的资源。

~~~mermaid
stateDiagram-v2
    [*] --> Ready
    Ready --> Draining: SIGTERM / mark unready
    Draining --> Waiting: stop accepting new connections
    Waiting --> Closed: in-flight work and server close
    Waiting --> Deadline: deadline expires
    Deadline --> Cancel: abort cooperative work
    Cancel --> ForceClose: close remaining HTTP connections
    Closed --> Cleanup: release owned resources
    ForceClose --> Cleanup
    Cleanup --> [*]
~~~

~~~javascript
const workAbort = new AbortController();
let draining = false;

function rejectWhileDraining(res) {
  if (!draining) return false;
  res.writeHead(503, { Connection: 'close' });
  res.end();
  return true;
}
// Call first in each request handler: if (rejectWhileDraining(res)) return;

async function shutdown() {
  draining = true;
  markReadiness(false);

  const deadline = setTimeout(() => {
    workAbort.abort(new Error('shutdown deadline'));
    server.closeAllConnections();
  }, 10_000);

  const serverClosed = new Promise((resolve, reject) => {
    server.close((error) => error ? reject(error) : resolve());
  });

  try {
    const lifecycle = await Promise.allSettled([
      serverClosed,
      waitForInFlightWork(),
    ]);
    const lifecycleFailures = lifecycle.filter((result) => result.status === 'rejected');

    let cleanupFailure;
    let cleanupFailed = false;
    try {
      await closeOwnedResources();
    } catch (error) {
      cleanupFailed = true;
      cleanupFailure = error;
    }

    for (const { reason } of lifecycleFailures) {
      console.error('shutdown lifecycle failed:', reason);
      process.exitCode = 1;
    }
    if (cleanupFailed) {
      console.error('resource cleanup failed:', cleanupFailure);
      process.exitCode = 1;
    }
  } finally {
    clearTimeout(deadline);
  }
}

process.once('SIGTERM', () => {
  void shutdown().catch((error) => {
    console.error('shutdown failed:', error);
    process.exitCode = 1;
  });
});
~~~

`markReadiness`, `waitForInFlightWork`, and `closeOwnedResources` stand for application-owned health, task, and resource hooks. `waitForInFlightWork()` must settle only after tracked work has stopped using its dependencies; a rejection reports failed work, not permission to clean up while that work still runs. The referenced deadline timer stays active while `Promise.allSettled()` awaits both server close and tracked work, and the code still attempts owned-resource cleanup before reporting lifecycle or cleanup failures. Keep the timer referenced until it fires or shutdown cleanup finishes; `unref()` would allow Node to exit before its callback when no other handle keeps the event loop active. `server.close()` stops new connections and, in Node.js 26.11.1, closes idle connections while waiting for the rest. `closeAllConnections()` is the deadline's forceful HTTP(S) fallback; call it after `server.close()` as shown, and close upgraded WebSocket or HTTP/2 sessions through their own owners. The task abort is cooperative: if a handler ignores its signal or another handle keeps the process alive, the service supervisor must enforce the final hard stop. A signal listener also replaces Node's default signal exit behavior on supported POSIX systems, so the handler must complete or deliberately set a failure exit code.


**Sources / 来源：** The shutdown example and lifecycle behavior were checked against [Node.js v26.11.1 HTTP](https://nodejs.org/download/release/v26.11.1/docs/api/http.html) and [process](https://nodejs.org/download/release/v26.11.1/docs/api/process.html) documentation on 2026-10-15. The timer-reference behavior uses [Node.js v26.12.1 timers](https://nodejs.org/api/timers.html), checked 2026-10-27.

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) explains cancellation and ambiguous remote outcomes; [Queue delivery acknowledgements / 队列确认与重投](#14.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) explains why a consumer acknowledges only after its chosen durable boundary.
## 21. How do Python values, iterators, and resource lifetimes behave? / Python 的值、迭代器与资源生命周期如何工作？

**Core model / 核心模型：** Python names are bindings to objects. A collection may be changed in place or a name may be rebound to another object; those are different operations. Function defaults are evaluated when the function is defined, iterators produce values as they are requested, and context managers define cleanup around a block. Type hints describe intent to static tools but do not validate runtime input. A virtual environment separates a project's installed packages from other environments. / Python 名称绑定到对象。集合可以被原地修改，名称也可以重新绑定到另一个对象，这是两种不同操作。函数默认值在函数定义时求值，迭代器按需产生值，上下文管理器则为代码块定义资源清理。类型提示表达意图并帮助静态工具检查，但不会在运行时验证输入。虚拟环境将项目安装的包与其他环境隔离。

~~~mermaid
flowchart LR
    File[CSV file] --> Iterator[Generator reads one row at a time]
    Iterator -->|valid row| Yield[Yield row to consumer]
    Iterator -->|later malformed row| Error[Raise parsing error]
    Error --> Unwind[Exception unwinds nested with blocks]
    Unwind --> Close[Close file and remove temporary directory]
    Yield --> Partial[Earlier output may already have escaped]
~~~

**Key terms / 关键术语：** object / 对象；name binding / 名称绑定；mutable / 可变；immutable / 不可变；alias / 别名；shallow copy / 浅拷贝；default argument / 默认参数；iterable / 可迭代对象；iterator / 迭代器；generator / 生成器；exception / 异常；context manager / 上下文管理器；type hint / 类型提示；virtual environment / 虚拟环境。

### Collections and object references / 集合与对象引用

Lists and dictionaries are mutable: an operation such as `append` or item assignment changes that object. Strings and tuples are immutable. A tuple cannot have its slots replaced, although it can still contain a mutable object whose value changes. Sets keep unique elements and do not provide sequence indexing; dictionaries map keys to values and preserve insertion order in Python 3.7 and later.

A name does not contain a separate copy of the value. Assignment binds the name to an object, so two names can refer to the same mutable object. Mutating through either name is visible through the other. Rebinding one name changes only that name's binding. A shallow copy creates a new outer container while keeping references to nested objects; use a deeper copy or explicit reconstruction only when the nested values also need independent ownership.

~~~python
event = {"id": "evt-1", "tags": ["new"]}
alias = event
alias["tags"].append("priority")
print(event["tags"])  # ['new', 'priority']

outer_copy = event.copy()
outer_copy["id"] = "evt-copy"  # a different outer dictionary
outer_copy["tags"].append("shared")  # the nested list is still shared
print(event["tags"])  # ['new', 'priority', 'shared']

alias = {"id": "evt-2", "tags": []}  # only alias is rebound
print(event["id"])  # evt-1
~~~

### Calls, argument binding, and defaults / 调用、参数绑定与默认值

At a call, Python binds supplied argument values to parameters by position or keyword. A parameter receives a reference to the supplied object; the call does not copy a mutable argument. Mutating that object inside a function can therefore be observed by the caller, while assigning a new object to the local parameter only rebinds that local name.

Default expressions are evaluated once when Python executes the `def` statement. If the default is a list or dictionary and the function mutates it, later calls reuse that same object. Use `None` when it means “no value supplied,” then create per-call state inside the function. If `None` itself is a meaningful input, choose a separate sentinel.

~~~python
def unsafe_add(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

print(unsafe_add("first"))   # ['first']
print(unsafe_add("second"))  # ['first', 'second'] — same default list

def add(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

print(add("first"))   # ['first']
print(add("second"))  # ['second']
~~~

### Iteration and generators / 迭代与生成器

An **iterable** can supply an iterator. An **iterator** returns its next value on request and signals completion with `StopIteration`; a `for` loop handles that protocol. A generator function uses `yield` to produce an iterator whose local state resumes at the next request. This lets a pipeline process one item at a time instead of first building a complete result list. The work, and any exception raised by that work, happens as the consumer advances the generator. A generator is usually one-pass; materializing it with `list(...)` consumes it and stores all produced values.

~~~python
from collections.abc import Iterable, Iterator

def ready_rows(rows: Iterable[dict[str, str]]) -> Iterator[dict[str, str]]:
    for row in rows:
        if row["status"] == "ready":
            yield row
~~~

Streaming reduces intermediate storage and can begin output early, but it does not make a whole operation atomic. If a later row is invalid, earlier rows may already have been emitted or acted on. Validate or stage first when the operation requires all-or-nothing effects.

### Exceptions and context managers / 异常与上下文管理器

Exceptions report that an operation could not complete normally. Catch one where the program can recover, translate it into a useful boundary error, or add context and re-raise it with `raise ... from error`. Avoid swallowing an exception when the caller still needs to know that work failed.

A context manager pairs setup and cleanup around a block. Once `__enter__` completes successfully, `__exit__` is called when the block ends, including when an exception leaves the block. A context manager may intentionally suppress an exception; ordinary file context managers close the file and allow the original error to continue. This is why file and temporary-directory lifetimes should be explicit rather than left to garbage collection.

### What type hints do and do not do / 类型提示的作用与边界

Annotations give readers and static analyzers a shared description of expected values and returns. A type checker can report a mismatch before execution, and an editor can use the information for navigation and completion. Python does not automatically reject a value because it conflicts with an annotation; data read from a file, database, or network still needs parsing and validation at that boundary. Runtime validation requires an explicit check or a library designed to perform it.

~~~python
def declared_integer() -> int:
    return "still a string"

print(declared_integer())  # Python returns the string; a type checker can flag it
~~~

### A small file-processing example / 小型文件处理示例

Save this as `python-fundamentals-example.py`. It filters synthetic CSV rows lazily, copies each selected row before adding a tag, and uses nested context managers to close the file and remove the temporary directory even if parsing raises an exception.

~~~python
import csv
from collections.abc import Iterable, Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

Row = dict[str, str]


def ready_rows(rows: Iterable[Row]) -> Iterator[Row]:
    for line_number, row in enumerate(rows, start=2):  # line 1 is the header
        try:
            status = row["status"]
            count = int(row["count"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"CSV row {line_number}: status and integer count are required"
            ) from error

        if status == "ready" and count > 0:
            yield row


def add_tag(row: Row, tag: str = "reviewed") -> Row:
    enriched = row.copy()  # a shallow copy is enough because values are strings
    enriched["tag"] = tag
    return enriched


CSV_TEXT = """id,status,count
evt-1,ready,3
evt-2,queued,1
evt-3,ready,nope
"""


def main() -> None:
    try:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.csv"
            path.write_text(CSV_TEXT, encoding="utf-8")

            with path.open(encoding="utf-8", newline="") as source:
                for row in ready_rows(csv.DictReader(source)):
                    print(add_tag(row))
    except ValueError as error:
        print(f"Rejected input: {error}")


if __name__ == "__main__":
    main()
~~~

Expected output:

~~~text
{'id': 'evt-1', 'status': 'ready', 'count': '3', 'tag': 'reviewed'}
Rejected input: CSV row 4: status and integer count are required
~~~

The first row is yielded before the generator reaches the malformed fourth CSV line. The example catches the parsing error outside both `with` blocks, so the file and temporary directory still close during exception unwinding. A real application that writes results to a database or calls a remote service must decide whether partial progress is acceptable and use a transaction or staging boundary when it is not.

### Language behavior, implementations, and versions / 语言语义、实现与版本

The examples use Python 3.11 syntax and the language behavior documented for Python 3.11. Names, mutability, default evaluation, iteration, and `with` cleanup are language/runtime contracts; they do not depend on CPython's internal object layout. Other details can be implementation-specific or change between Python versions. For example, dictionary insertion order is a language guarantee from Python 3.7; CPython 3.6 preserved it as an implementation detail. In CPython, `id(obj)` currently represents an object's memory address, but code should not treat an identity value as a durable identifier. Check the target interpreter and minimum supported version before relying on newer syntax or runtime behavior.

### Isolated environment and run command / 隔离环境与运行命令

A virtual environment gives a project its own package installation area; it does not install or pin the Python interpreter itself. Select the intended interpreter when creating the environment, and use that environment's Python to invoke `pip` so package installation and execution target the same environment. Declare third-party requirements in the project's packaging or dependency files. A dependency-free example needs no installation step.

On POSIX, from the directory containing the saved example, create an environment and run it with:

~~~sh
python3.11 -m venv .venv && .venv/bin/python python-fundamentals-example.py
~~~

For a project with a `requirements.txt`, install its declared packages with `.venv/bin/python -m pip install -r requirements.txt` before running the script. A virtual environment isolates packages, while repeatability still depends on selecting a compatible Python version and recording the project's dependency versions and platform requirements.

**Verified run / 运行验证：** The file-processing example ran with CPython 3.11.13 and printed the expected output above. This verifies the example on that interpreter; it is not a claim that every Python implementation or platform has identical implementation details.

**Related notes / 相关笔记：** [API Reliability and Asynchronous Delivery / API可靠性与异步交付](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) explains timeouts, cancellation, and safe retries. [Capacity and backpressure](#23.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) covers bounded work.
Python-specific coroutine and framework behavior is explained in [Python Async and FastAPI Request Lifecycle / Python异步与FastAPI请求生命周期](#22.%20Why%20can%20an%20async%20FastAPI%20endpoint%20still%20block?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%E5%BC%82%E6%AD%A5%20FastAPI%20%E6%8E%A5%E5%8F%A3%E4%BB%8D%E4%BC%9A%E9%98%BB%E5%A1%9E%EF%BC%9F).
Application-level request, response, error, and pagination contracts are covered in [HTTP API Contracts / HTTP API契约](#3.%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F).

**Sources / 来源：** Python 3.11 [Tutorial](https://docs.python.org/3.11/tutorial/) and [Language Reference](https://docs.python.org/3.11/reference/), including [objects and types](https://docs.python.org/3.11/reference/datamodel.html#objects-values-and-types), [function definitions](https://docs.python.org/3.11/reference/compound_stmts.html#function-definitions), [iterators and generators](https://docs.python.org/3.11/reference/datamodel.html#generator-functions), and [`with` statements](https://docs.python.org/3.11/reference/compound_stmts.html#the-with-statement); [`typing`](https://docs.python.org/3.11/library/typing.html); and the Python Packaging User Guide's [installing packages](https://packaging.python.org/en/latest/tutorials/installing-packages/) and [managing application dependencies](https://packaging.python.org/en/latest/tutorials/managing-dependencies/) tutorials. Checked 2026-10-15.

### Representative answers / 代表性回答

**How do mutability, argument binding, and defaults affect a function call? / 可变性、参数绑定与默认值如何影响函数调用？** Names bind to objects, so a caller and a parameter can refer to the same mutable object. An in-place mutation is visible through both references; rebinding the local parameter does not rebind the caller's name. Python evaluates a default expression when the function is defined, so a mutable default is shared across calls. Use `None` and allocate a fresh list or dictionary inside when each call needs independent state.

名称绑定到对象，因此调用方和形参可能引用同一可变对象。原地修改会通过两个引用都可见；在函数内部重新绑定形参不会改变调用方的名称绑定。Python 在函数定义时求值默认表达式，因此可变默认值会在多次调用间共享。若每次调用需要独立状态，使用 `None` 并在函数内部创建新列表或字典。

**How do iterators, generators, and context managers control work and resources? / 迭代器、生成器与上下文管理器如何控制工作和资源？** An iterator produces one value per request, and a generator packages that pull-based behavior with `yield` and saved execution state. That can avoid building an entire intermediate collection, but later errors may occur after earlier values have already been consumed. A context manager runs its exit behavior when a block ends, including during exception unwinding, so files and other resources have a clear cleanup boundary.

迭代器按请求产出一个值，生成器通过 `yield` 和保存的执行状态封装这种拉取式行为。这样可以避免构建整个中间集合，但后续错误可能在较早的值已经被消费后才发生。代码块退出时（包括异常展开期间），上下文管理器都会运行退出逻辑，因此文件等资源有明确的清理边界。

**What do Python type hints guarantee at runtime? / Python 类型提示在运行时保证什么？** By themselves, they guarantee nothing about the values passed or returned. They communicate expected shapes to humans and static tools. Programs still parse and validate untrusted or external data where it enters the application, and use explicit runtime checks when runtime enforcement is required.

类型提示本身不会在运行时保证输入值或返回值的类型。它们向读者和静态工具传达预期的数据形状。程序仍需在外部数据进入应用时解析与校验；需要运行时强制时，应添加显式检查或使用专门的校验库。
## 22. Why can an async FastAPI endpoint still block? / 为什么异步 FastAPI 接口仍会阻塞？

**Core idea / 核心模型：** `asyncio` lets one event-loop thread make progress on other tasks while the current task waits for asynchronous I/O. An `async def` declaration alone does not make blocking work asynchronous: choose `def` for synchronous libraries that block, and `async def` when awaited libraries can suspend. Tie every acquired resource to a clear cleanup boundary, and treat cancellation as a cooperative request to stop. / `asyncio`让事件循环线程在当前任务等待异步I/O时推进其他任务。仅仅声明`async def`不会让阻塞操作异步：使用同步阻塞库时可选择`def`，使用能通过`await`挂起的库时选择`async def`。资源应绑定明确的清理边界；取消是要求任务协作停止，而非强制终止。

**Key terms / 关键术语：** coroutine function / 协程函数；coroutine object / 协程对象；awaitable / 可等待对象；task / 任务；event loop / 事件循环；cooperative scheduling / 协作式调度；blocking I/O / 阻塞I/O；deadline / 截止时间；cancellation / 取消；yield dependency / `yield`依赖；worker thread / 工作线程。

### From `async def` to a running task / 从`async def`到运行中的任务

An `async def` **coroutine function** describes work. Calling it creates a **coroutine object**; it does not run the body. `await coro()` drives that coroutine as part of the current task. `asyncio.create_task(coro())` schedules it as a separate **Task**, so it can progress concurrently with other tasks. Keep and await created tasks; starting work without collecting its result makes failures and shutdown hard to control. In Python 3.11, `asyncio.TaskGroup` is a structured way to create related tasks and wait for them together.

An **awaitable** is any object accepted by `await`, including coroutine objects, Tasks, and Futures. During an incomplete await, the current task suspends and the event loop can run another ready task or service I/O. This is cooperative: code runs until it reaches a suspension point. A synchronous call such as `time.sleep()`, a blocking database driver, or a long CPU loop prevents the event-loop thread from serving other tasks during that call.

An `async def` function containing `yield` is an **async-generator function**; calling it returns an **async-generator object**, not a coroutine object. FastAPI manages that object's dependency lifecycle to run cleanup after yielding the resource.

### Choose the boundary by the library you call / 按所调用的库选择边界

For an awaited database or HTTP client, use an `async def` route and await its I/O. A synchronous `def` route or dependency that FastAPI calls is run in its worker thread pool, so a legacy synchronous client can fit that boundary. Conversely, a synchronous helper called directly from inside an `async def` route is just a normal function call; FastAPI does not automatically move that nested call to a thread.

`asyncio.to_thread()` is useful for blocking I/O that cannot yet be replaced, and it keeps the event loop available while the thread waits. It is not a general CPU-parallelism switch: in a GIL-enabled CPython runtime, the lock limits simultaneous execution of pure-Python CPU work. CPython offers free-threaded builds from 3.13, but extension support and whether the GIL is enabled still matter. A process pool or separate worker can run CPU work in parallel, with serialization, startup, memory, and queueing costs. Native extensions that release the GIL and other Python implementations can differ. Measure the chosen runtime and library combination. [CPython free-threading guide](https://docs.python.org/3/howto/free-threading-python.html) Bound thread/process concurrency so offloading does not merely move an unbounded queue; see [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#23.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) for admission and backpressure.

### Cancellation, deadlines, and cleanup / 取消、截止时间与清理

`Task.cancel()` arranges for `CancelledError` to be raised in the task at a later opportunity, commonly at an `await`. Use `try/finally` to release resources and normally let cancellation propagate after cleanup. Do not catch `BaseException` or suppress `CancelledError` as a generic error; structured concurrency and timeout scopes rely on cancellation being visible.

In Python 3.11, `asyncio.timeout(seconds)` cancels the current task when its time budget expires and raises `TimeoutError` outside the context manager. It is cooperative: a blocking synchronous function prevents the event loop from delivering that cancellation until the function returns. A timeout around `await asyncio.to_thread(...)` stops waiting in the coroutine but cannot forcibly stop a thread function already running. A client timeout also does not prove that a remote operation stopped or had no side effect. Pass remaining request budget to supported downstream calls and use the broader [API reliability guidance](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) for end-to-end deadlines and unknown outcomes.

### Choose the dependency scope from its last use / 按最后一次使用选择依赖作用域

In FastAPI 0.128.0, a yielded dependency defaults to request scope. The framework enters it before the route runs. If the route returns a streaming body that will keep using the resource, retain the request scope through response processing. If the dependency is only needed while running the route, `Depends(scope="function")` ends it when the handler returns, before sending the response. Return data that no longer needs the resource when choosing function scope. / 如果响应生成过程中还需使用资源，就保留 request scope。路由返回前已完成全部资源使用时，才选择 function scope。

~~~mermaid
sequenceDiagram
    participant F as FastAPI
    participant D as Yield dependency
    participant R as Route
    participant B as Response body
    F->>D: Acquire resource
    F->>R: Call route
    R-->>F: Return response
    alt function scope
        F->>D: Clean up
        F->>B: Generate and send body
    else request scope
        F->>B: Generate and send body
        B->>D: Use resource while streaming
        F->>D: Clean up at end of request scope
    end
~~~

Put cleanup in `finally`. In an already-cancelled AnyIO scope, awaited cleanup can be cancelled too. When it must await, give that cleanup a short shielded deadline and let the original cancellation propagate. The smoke check below exercises explicit task cancellation and both streaming lifetimes. A dropped connection does not necessarily cancel every kind of downstream work. Test the selected ASGI server and response type before depending on disconnect behavior. A background job should acquire its own resources at its own lifetime boundary. [FastAPI dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/) · [AnyIO finalization](https://anyio.readthedocs.io/en/stable/cancellation.html#finalization)

~~~mermaid
flowchart LR
    Sync[Blocking sync library] -->|def route or dependency| Pool[FastAPI worker thread pool]
    Async[Async library] -->|await| Loop[Event loop can run other tasks]
    Inline[Blocking call inside async route] -->|no suspension| Block[Event loop is blocked]
    CPU[Pure-Python CPU work] -->|bounded process pool or worker| Parallel[Other execution resource]
~~~

### Runnable request example / 可运行的请求示例

This small app has a sync settings dependency, an async resource dependency, an awaited route with a deadline, a streaming route that needs request-scoped cleanup, a deliberately bad blocking route, and a thread-offloaded I/O route. Save the complete block as `async_api_demo.py`; it is an executable smoke check rather than a production server.

~~~python
import asyncio
import threading
import time

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from httpx import ASGITransport, AsyncClient

trace = []
slow_started = []
quick_seen = []


def load_settings():
    # FastAPI runs a sync dependency it calls in its worker thread pool.
    return {"region": "demo", "thread": threading.get_ident()}


class Store:
    async def get(self, item_id: int, region: str):
        await asyncio.sleep(0)  # stand-in for an async driver wait
        return {"id": item_id, "region": region}


async def get_store():
    trace.append("open")
    try:
        yield Store()
    finally:
        trace.append("close")


app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(
    item_id: int,
    settings=Depends(load_settings),
    store=Depends(get_store, scope="function"),
):
    assert settings["thread"] != threading.get_ident()
    async with asyncio.timeout(0.5):
        return await store.get(item_id, settings["region"])


def blocking_io():
    time.sleep(0.06)
    return "done"


@app.get("/bad")
async def bad_route():
    slow_started.append(time.monotonic())
    blocking_io()  # blocks the event-loop thread
    return {"ok": True}


@app.get("/quick")
async def quick_route():
    quick_seen.append(time.monotonic())
    return {"ok": True}


@app.get("/offloaded")
async def offloaded_route():
    return {"result": await asyncio.to_thread(blocking_io)}


@app.get("/stream")
async def stream(store=Depends(get_store)):  # default yield scope is request
    async def body():
        trace.append("body")
        yield "x"

    return StreamingResponse(body(), media_type="text/plain")


@app.get("/wait")
async def wait_forever(store=Depends(get_store)):
    await asyncio.Event().wait()


async def check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://example.test"
    ) as client:
        trace.clear()
        response = await client.get("/items/7")
        assert response.json() == {"id": 7, "region": "demo"}
        assert trace == ["open", "close"]  # function scope closes before send

        trace.clear()
        response = await client.get("/stream")
        assert response.text == "x"
        assert trace == ["open", "body", "close"]  # request scope covers body

        trace.clear()
        task = asyncio.create_task(client.get("/wait"))
        await asyncio.sleep(0.01)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError("request task was expected to be cancelled")
        assert trace == ["open", "close"]

        slow_started.clear()
        quick_seen.clear()
        bad = asyncio.create_task(client.get("/bad"))
        await asyncio.sleep(0)  # let /bad block before /quick is scheduled
        quick = await client.get("/quick")
        await bad
        assert quick.status_code == 200
        assert quick_seen[0] - slow_started[0] >= 0.05

        response = await client.get("/offloaded")
        assert response.json() == {"result": "done"}


asyncio.run(check())
~~~

The `/bad` route delays the next event-loop request because it calls a blocking helper directly. Use a synchronous route for a synchronous I/O stack, or explicitly offload a blocking call; when possible prefer a native async client. The `/items` route awaits I/O and receives the sync and async dependencies through FastAPI's respective boundaries. Its 0.5-second timeout is only a local teaching budget, not a recommended service-wide setting.

### Python and runtime versions / Python与运行时版本

`async`/`await` syntax is part of Python; `asyncio` is a standard-library API. This example was checked with **CPython 3.11.13**, FastAPI **0.128.0**, Starlette **0.47.2**, and HTTPX **0.28.1**. `asyncio.timeout()` and `asyncio.TaskGroup` require Python 3.11; `asyncio.to_thread()` requires Python 3.9+. CPython is one Python implementation, so GIL statements above are explicitly CPython-specific. Verify framework lifecycle options against the installed FastAPI version: newer live documentation may describe behavior absent in an older release.

### Interview answers / 面试回答

**Why can an `async def` endpoint still stall other requests? / 为什么`async def`接口仍会拖慢其他请求？** An async function only yields when it awaits an operation that actually suspends. Calling a synchronous network/file helper or doing a long CPU loop inline keeps the event-loop thread busy. I would use an async driver, a sync route/dependency that FastAPI can offload, or a bounded thread/process worker chosen for the workload; then I would measure queueing and latency.

异步函数只有在等待一个确实会挂起的操作时才让出执行权。在函数内直接调用同步网络/文件操作，或执行很长的CPU循环，都会占住事件循环线程。我会使用异步驱动、由FastAPI代为卸载的同步路由/依赖，或根据工作负载选择有界线程/进程工作池，并测量排队与延迟。

**What happens when a request is cancelled while it owns a resource? / 请求持有资源时被取消会怎样？** Cancellation is delivered cooperatively, so I put release logic in `finally` and let `CancelledError` propagate. For FastAPI `yield` dependencies I choose request scope if response streaming still consumes the resource, and function scope if cleanup should happen before sending the response. I would not assume a client timeout or disconnect proves remote work stopped; I would keep downstream deadlines and side-effect handling explicit.

取消通过协作方式传递，因此我会把释放逻辑放进`finally`并让`CancelledError`继续传播。若响应流仍要使用FastAPI的`yield`依赖，我会选择request scope；若资源应在响应发送前关闭，则选择function scope。我不会因为客户端超时或断开就认定远端工作已停止；下游截止时间与副作用处理仍需显式定义。

**Sources / 来源：** Python 3.11 [asynchronous generator functions](https://docs.python.org/3.11/reference/expressions.html#asynchronous-generator-functions), [`asyncio` tasks, cancellation, timeouts, and threads](https://docs.python.org/3.11/library/asyncio-task.html), [asyncio development guidance](https://docs.python.org/3.11/library/asyncio-dev.html), and [executor cancellation behavior](https://docs.python.org/3.11/library/concurrent.futures.html); FastAPI [async and sync route behavior](https://fastapi.tiangolo.com/async/), [yield dependency scopes](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/), and [streaming dependency lifetime](https://fastapi.tiangolo.com/advanced/advanced-dependencies/); version-pinned FastAPI [0.128.0 dependency resolver](https://github.com/fastapi/fastapi/blob/0.128.0/fastapi/dependencies/utils.py), checked 2026-10-15. Related: [Python Fundamentals / Python基础](#21.%20How%20do%20Python%20values,%20iterators,%20and%20resource%20lifetimes%20behave?%20/%20Python%20%E7%9A%84%E5%80%BC%E3%80%81%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E8%B5%84%E6%BA%90%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E5%A6%82%E4%BD%95%E5%B7%A5%E4%BD%9C%EF%BC%9F), [API Reliability and Asynchronous Delivery / API可靠性与异步交付](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F), [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F), and [Database Fundamentals / 数据库基础](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F). [HTTP API Contracts / HTTP API契约](#3.%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F) defines the request, response, and error shapes used by these handlers. [Data Access and Connection Pools / 数据访问与连接池](#10.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F) expands the resource example into database-session, transaction, and pool-lifetime choices.
## 23. How do you size and bound an asynchronous work pipeline? / 如何估算并限制异步工作管线？

Size a pipeline by naming its system boundary, arrival rate, time in each stage, resource held by each unit of work, and maximum waiting work. Little's Law estimates average work in flight in a stable system; it does not promise peak throughput or tail latency. A queue gives work somewhere durable to wait, but only admission control and backpressure keep that wait bounded. / 估算管线时，要明确系统边界、到达速率、各阶段耗时、每个任务占用的资源和最大等待量。Little 定律估算稳定系统中的平均在途工作；它不承诺峰值吞吐量或尾部时延。队列让工作可以持久等待，但只有准入控制和背压才能限制等待规模。

**Key terms / 关键术语：** admission control / 准入控制；backpressure / 背压；in-flight work / 在途工作；queue age / 队列等待时长；Little's Law / Little 定律；connection pool ceiling / 连接池配置上限。

### Bound work before estimating replicas / 先限制工作量，再估算副本数

Bound in-flight requests, worker count, and every waiting queue. An unbounded queue turns overload into growing memory use and delay. When a bound is reached, choose an explicit policy: wait within the request deadline, reject, defer to durable storage, or shed work that can safely be dropped. Include queue wait in the request's latency budget and report overload distinctly from successful completion.

~~~mermaid
flowchart LR
    S[Submission] --> Rate{Rate budget available?}
    Rate -->|no| Reject[Reject without claiming acceptance]
    Rate -->|yes| Slots{Shared waiting slot available?}
    Slots -->|no| Reject
    Slots -->|yes| Reserve[Atomically reserve one job slot]
    Reserve --> Outbox[Outbox or durable queue]
    Outbox --> Start[Worker starts job]
    Start --> Release[Release reservation once]
    Outbox -->|publish retry or broker copy| Outbox
~~~

For a durable job, count the logical job once while it is in the outbox or waiting in the broker. Moving the same job between those systems does not consume a second waiting slot. Release the reservation through a guarded transition when the job starts or becomes terminal before starting. If a retry or lease recovery returns it to waiting, reserve a slot again before requeueing. The account-report case uses this rule and defines the database transitions in [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F).

Under steady-state conditions, Little's Law is:

~~~text
average work in flight = arrival rate × average time in system
~~~

The system boundary must include the queue if the arrival rate and elapsed time include queued work. For example, 40 requests/s × 0.2 s in the chosen system implies about 8 average in-flight requests. This is a planning check, not a universal concurrency cap: bursts, latency distributions, retries, and downstream limits still need measurement.

### Synthetic account-report sizing example / 合成账户报表容量估算

**Assumptions / 假设：** Consider a teaching workload with an average of 5 submissions/s and a 10-minute peak of 20/s. Each validated request is 8 KiB, and its submission transaction holds a database connection for 10 ms. A worker makes 12 sequential indexed reads, holding a database connection for 20 ms per read. Mean worker time is 6 s, the average report is 128 KiB, and job metadata is 2 KiB. These are synthetic inputs for arithmetic, not observed traffic, service measurements, an SLO, or a recommended default.

#### Estimate worker slots and admission / 估算 worker 槽位与准入

At the average arrival rate, mean worker concurrency is 5 jobs/s × 6 s = 30 jobs. At the stated peak, offered load would require 20 × 6 = 120 concurrent jobs if every request were admitted.

A plan with 4 worker replicas × 2 processes per replica × 8 active job slots per process has 64 slots. If the slots stayed full, the estimate is 64 / 6 = 10.67 jobs/s; at a planning utilization of 70%, it is 64 × 0.70 / 6 = 7.47 jobs/s. A 7 jobs/s token-bucket admission rate uses an estimated 7 × 6 / 64 = 65.6% of slots. These values are starting limits to test, not measured capacity guarantees.

Bound acceptance separately from waiting work. In this example, allow a sustained 7 submissions/s with a burst of 30 and at most 240 accepted-but-not-started jobs across the outbox and broker queue. Reserve one shared slot per job before returning **202 Accepted**; moving a job from outbox to broker does not count it twice. Release the reservation once when work starts or becomes terminal before starting. If all workers stop, the bound fills after a short interruption; once the waiting allowance is full or the rate limit is exhausted, return a documented overload response without claiming the request was accepted.

At 20 offered submissions/s for 600 s, 12,000 requests arrive. A token bucket admitting at most 7 × 600 + 30 = 4,230 in that interval leaves at least 7,770 not admitted, assuming the shared waiting allowance and other limits do not reject sooner. A rejected or ambiguous submission still follows the deadline and idempotency rules in [API timeout and safe retry / API 超时后的结果确认与安全重试](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F).

#### Budget database connections / 预算数据库连接

Budget every process-local pool, including overflow, before increasing replicas:

| Process group | Maximum calculation | Possible connections |
|---|---:|---:|
| API: 4 replicas, 2 processes each, pool 8 + overflow 2 | 4 × 2 × (8 + 2) | 80 |
| Workers: 4 replicas, 2 processes each, pool 8 + overflow 2 | 4 × 2 × (8 + 2) | 80 |
| Other services using the same database | Assumed allocation | 40 |
| Configured application total | 80 + 80 + 40 | 200 |
| Example database connection budget | Assumed total | 240 |
| Unallocated headroom | 240 − 200 | 40 |

This pool ceiling is not a prediction that 200 connections will be busy. Each report uses 12 sequential reads × 0.020 connection-seconds = 0.24 connection-seconds. That implies 5 × 0.24 = 1.2 average checked-out connections for report reads at the average arrival rate, or 20 × 0.24 = 4.8 if the offered peak were admitted; a 10 ms submission transaction adds 0.05 average or 0.2 at that peak. Query fan-out, connection hold time, and real pool behavior must be measured before treating these estimates as resource headroom. The application-level pool ceiling and its per-process scope are explained in [Data Access and Connection Pools / 数据访问与连接池](#10.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F).

#### Estimate result bytes and retention / 估算结果体量与留存

At 5 completed reports/s, 128 KiB per report produces 640 KiB/s of results. Seven days of output retention is:

~~~text
128 KiB × 5/s × 604,800 s ÷ 1,048,576 KiB/GiB ≈ 369 GiB
~~~

This is before compression, replication, and cleanup lag. Two KiB of metadata per job adds about 5.8 GiB per seven days before indexes.

At a sustained 7 completions/s, result volume averages 0.875 MiB/s; this is a long-run planning rate, not an instantaneous upper bound. The permitted 30-job burst could produce 3.75 MiB if all reports complete in one interval, and backlog drain can exceed the current admission rate. At a sustained 20 completions/s, the corresponding long-run result volume is 2.5 MiB/s. Measure result downloads separately from generation and retention.

#### Test the first bottleneck / 验证最先触顶的资源

Under these assumptions, worker slots bind before the estimated database connection count: peak demand needs 120 active jobs while the plan has 64 slots. That does not prove database CPU, storage I/O, or network has spare capacity.

Load-test the representative 8 KiB input, 12-read fan-out, and output sizes. Ramp average traffic, apply the 20/s burst, then test rate rejection, a full queue, slow reads, retries, and worker loss. Record request acceptance latency separately from job queue wait and completion time. Compare distributions such as p50, p95, and p99 for each user-visible stage; the 6 s mean belongs in the concurrency estimate, not as a p95 promise. Track sustained throughput, queue age, busy slots, database checkout wait and CPU, retained bytes, and completed-job outcomes against the service objective before changing pool size or replicas. [Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应](#31.%20How%20do%20you%20diagnose%20an%20API%20SLO%20violation?%20/%20%E5%A6%82%E4%BD%95%E8%AF%8A%E6%96%AD%20API%20SLO%20%E8%BF%9D%E7%BA%A6%EF%BC%9F) explains how to turn these signals into useful service indicators.

**How would you answer “How many workers do we need?” / 如何回答“需要多少个 worker？”** I would state the workload and service-time assumptions, use Little's Law for mean in-flight jobs, and compare that with a bounded worker plan and pool budget. Here the mean suggests 30 active jobs, but peak demand suggests 120; 64 slots and a 7/s admission limit are hypotheses to test under the expected payload and fan-out. I would measure queue age and stage latency distributions before adding replicas, because the first limit could move to the database or storage. / 我会先说明工作负载和处理时长假设，用 Little 定律估算平均在途任务，再与有界 worker 和连接池预算比较。此例平均负载约需 30 个并发任务，但峰值需求约为 120；64 个槽位和每秒准入 7 个是待压测的假设，应按预期 payload 和扇出测量队列等待及各阶段时延分布，再决定是否扩容，因为首个瓶颈也可能转移到数据库或存储。

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) covers deadline and unknown-outcome policy; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#13.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F) applies these bounds to a complete service contract; [Queue delivery acknowledgements / 队列确认与重投](#14.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) covers broker delivery state; [AI System Design Interview Questions / AI 系统设计面试题](../../ai-engineering/systems/ai-system-design-interview-questions.md) has a different worked latency allocation and model-stage concurrency estimate.

**Sources / 来源：** Little and Graves, [“Little’s Law Deals with Queuing Systems”](https://web.eng.ucsd.edu/~massimo/ECE158A/Handouts_files/Little.pdf), in *Building Intuition* (2008), pp. 81–82, for the steady-state relation and system boundary; [Google SRE Workbook: Implementing SLOs](https://sre.google/workbook/implementing-slos/), checked 2026-10-15, for latency distributions and percentile-based indicators. The numeric workload and all capacity figures above are synthetic calculations from the stated assumptions.
## 24. Web 服务如何限制拒绝服务的影响？

denial of service (DoS，拒绝服务) 通过流量洪峰、连接耗尽或昂贵请求让服务资源不够用；distributed denial-of-service (DDoS，分布式拒绝服务) 指多来源同时发起的攻击。保障要沿请求实际能到达的层次布置：链路入口被塞满时，应用限流代码还没有机会运行；请求已进应用后，按 Internet Protocol address (IP 地址) 限流也不能替代对昂贵工作、并发和排队长度的约束。

**案例：** 多个来源同时请求报表 42。大量流量可能先占满上游网络；也可能是有效格式的请求通过入口，却反复触发一次昂贵的数据汇总。两种情况下要保护的资源和起作用的位置不同。

~~~mermaid
flowchart LR
    Attack[分布式或高成本请求] --> Ingress[互联网链路与上游清洗]
    Ingress --> Edge[边缘缓存 / 网关过滤和早期限制]
    Edge --> App[按身份、路由成本准入和并发限制]
    App --> Data[有界数据库、缓存与队列资源]
    App --> Client[429、503 或服务降级]
    Ingress --> Signals[异常流量与容量告警]
    Edge --> Signals
    App --> Signals
~~~

### 过载发生在哪一层，就在哪一层减压

| 层次 | 典型故障 | 可以做什么 | 控制的边界 |
| --- | --- | --- | --- |
| 上游链路、DNS、网络入口 | 洪峰占满接入带宽，应用请求尚未到达 | 与网络/云服务商预先安排足够入口容量、DDoS 流量清洗、路由和过滤策略；保存应急联系和切换方案 | 仅在服务器里的代码无法清除已经塞满的上游链路 |
| Content Delivery Network (内容分发网络，CDN)、反向代理、网关 | 边缘连接、TLS、头部解析或无效请求消耗资源 | 限制头部/请求体大小、连接与超时，过滤明显异常流量；只缓存适合共享的公开表示；以低成本规则尽早拒绝 | 边缘按 IP 计数会受共享地址、代理和分布式来源影响；它也不了解所有业务授权 |
| API 与业务处理 | 有效请求触发昂贵查询，或同一租户占用服务槽位 | 按未认证来源、账户/租户、路由和估算成本组合限流；约束时间范围、查询复杂度、并发和返回量 | 受限额度可能误伤高峰期的合法用户；要让用户范围和服务容量相匹配 |
| 数据库、缓存、worker、队列 | 连接池耗尽、慢查询堆积、待处理任务无限增长 | 限制并发、队列长度、单任务成本和处理时间；必要时拒绝新工作并保留已接受工作 | 无限扩大队列会把即刻过载改成更迟的内存、存储和恢复过载 |
| 监控与事件响应 | 攻击特征未及时发现或缓解动作不一致 | 对比平常流量基线、资源指标和请求分布；启动已演练的上游清洗、临时规则、沟通与恢复步骤 | 单次请求日志无法提供链路容量和分布式来源全貌 |

### 速率限制和工作上限怎样一起计算？

rate limit（速率限制）约束某个键在一段时间内可提交多少请求；quota（配额）约束一段周期内可消耗的总量；并发限制约束同一时刻有多少工作在执行。它们处理不同的资源形状。例如读取报表 42 的小缓存只消耗少量资源，已获聚合操作授权的用户提交长时间范围聚合则会占用更多数据库工作。请求格式有效不代表用户有权启动昂贵计算；先检查身份和资源权限，再按路由估算成本计费。每个便宜缓存读取扣 1 个工作点，每个长范围聚合扣 4 点，同一主体的额度因此反映可接受的实际工作量，而不是给昂贵请求更多额度。还要限制时间范围、查询时限和并发槽位。

> [!example] 令牌桶的实际预算
> 假定一个主体专属的 token bucket（令牌桶）初始有 8 个工作点，每秒补 4 点；先看每个请求都只扣 1 点的情况。20 个请求同时在 `t=0` 到达时，最多先放行 8 个；若排队且没有其他流量，`t=0.25、0.50、0.75、1.00` 各补足 1 点，再各放行一个，至 `t=1.00` 累计上限是 `8 + 4 × 1 = 12` 个，余下 8 个仍待处理。不开队列时，首批 8 个之外的请求会立刻被拒绝，实际放行量可以低于 12。若请求有不同成本，每次从同一桶扣对应点数：4 点的长范围聚合会比 1 点的缓存读取更快耗尽额度。一般在长度为 `T` 的时间内，桶初始满时成本预算不超过 `burst + rate × T`。这是对单个计数键和这组成本的上限计算，不是服务整体容量保证。
>
> 如果三个进程各自保存一个相同的本地桶，短窗口预算上限相加可到 36 点；本例的 20 个请求仍最多只能放行 20 个，而且到达顺序、各请求成本及是否排队会影响实际结果。全局额度需要网关集中计数、共享状态或明确分片额度；共享状态提高一致性，却引入可用性和延迟成本。具体方案按部署规模选择。

CDN可以在更靠近用户的边缘节点缓存适合共享的公开内容或执行入口规则；Network Address Translation (网络地址转换，NAT)可能让许多合法用户共享同一个出口 IP。匿名请求发生在身份认证之前，不能只靠账户限流；登录后的请求也不能只靠 IP 限流，而分布式攻击来源又可能跨越许多地址。可以在不同阶段组合 IP/网络特征、账户、租户、路由和成本额度，并为误伤、绕过、状态存储可用性设计补救。反向代理转发的客户端 IP 只有在信任该代理、拒绝外部伪造转发头时才可用于策略。

速率限制是准入政策，不会给出一个“安全的 QPS”。容量章负责在正常负载下估算资源与背压，见[如何估算并限制异步工作管线？](#23.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)；本章强调在攻击者可分布请求、上游容量会饱和且不同请求成本悬殊时，应由哪一层拒绝或削减工作。

### 限额触发时如何让客户端和服务一起恢复？

若单个调用方超过合同额度，API 可按其错误契约返回 `429 Too Many Requests`，并选择用 `Retry-After` 建议等待时间；若服务整体暂时不能处理，请求也可能得到 `503 Service Unavailable`。这些状态表达本次 HTTP 请求结果，不会自行清除队列或建立未来重试。客户端应遵守等待时间，并用带抖动的指数退避避免一群用户同时重试；对于有副作用的 POST，还要先按[请求超时后的结果确认与安全重试契约](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)处理未知结果。

当入口流量超过上游能力时，应用返回 429/503 并不能帮助未到达应用的请求；要让上游服务商启动预案。当应用数据库或 worker 过载时，边缘可先挡掉已知攻击形态，但 API 还要把并发和队列限制在下游可承受范围，不能让短时间增长的队列拖垮健康的请求。限额和降级策略要配合服务目标，也要监控拒绝比例、合法租户成功率、数据库等待和可用容量，才能判断是不是阻断了攻击同时误伤正常读者。

> [!info]- 来源
> - 分布式流量、IP 欺骗、攻击类别、预防和响应步骤：[CISA、FBI、MS-ISAC, Understanding and Responding to Distributed Denial-of-Service Attacks](https://www.cisa.gov/sites/default/files/2024-03/understanding-and-responding-to-distributed-denial-of-service-attacks_508c.pdf)，2024-03-21，§2–§5；核对于 2026-11-06。
> - 网络与应用层 DoS、限速以及可消耗资源的应用输入：[OWASP Denial of Service Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html)，Fundamentals、Application Attacks、Network Attacks、Rate Limiting，按 2026-11-06 版本核对。
> - `429 Too Many Requests` 与可选 `Retry-After`：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，§4，2012-04；临时过载 `503` 与等待建议字段：[RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§10.2.3、§15.6.4，2022-06。均核对于 2026-11-06。
## 25. How can a minimal counterexample trace a regression to its root cause? / 如何用最小反例沿调用路径定位回归根因？

**核心回答 / Core answer：** Start with an observable expected outcome, trace the request through its entry point, dependencies, data access, and side effects, then build the smallest counterexample that can disprove a specific hypothesis. If the failure occurs at a lost tenant predicate, restore that predicate and test both owner and non-owner requests. Review the implementation and its tests independently: they can pass together while sharing the same missing assumption. / 先写出可观察的预期结果，再沿入口、依赖、数据访问和副作用追踪请求，并构造足以推翻某个具体假设的最小反例。如果故障来自丢失租户条件，就恢复该条件，并分别检查所有者与非所有者请求。实现和测试要独立审查：两者可能共享同一个遗漏假设，即使一起通过也不能证明需求已满足。

**Key terms / 关键术语：** expected behavior / 预期行为；entry point / 入口；call path / 调用路径；minimal reproduction / 最小复现；falsifiable hypothesis / 可证伪假设；root cause / 根因；regression check / 回归检查；generated change / 生成式改动。

### Follow one generated authorization bug / 跟踪一个生成式授权缺陷

Suppose a generated refactor changes a job lookup from the existing tenant-scoped query to `session.get(Job, job_id)`. Its generated test creates a job for `tenant-a` and reads it back as `tenant-a`; that test passes. The requirement, however, is that the current tenant may read only its own job. A matching owner read does not exercise that boundary.

Start with an observable expectation: after `tenant-a` creates a job, `tenant-b` requesting the same ID receives `404`, while `tenant-a` still receives `200`. Then follow the request rather than guessing from the response: the route reads `tenant_id` from the principal dependency, passes it to the database lookup, and serializes the returned job. The generated patch still receives `tenant_id`, but its new `session.get` lookup ignores it.

The minimal reproduction is one create and one read under a different tenant. If the response is `200`, the hypothesis “the database lookup no longer constrains the row by the current tenant” is supported. If the route rejects the second tenant earlier, or the lookup is tenant-scoped, the hypothesis is false and the next step is to inspect that earlier branch or another code path. This makes the hypothesis testable rather than a label attached after the fact.

The smallest coherent fix is to restore both predicates in the query:

~~~python
job = session.scalar(
    select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
)
~~~

The root cause is the lost tenant predicate, not response serialization or a missing test fixture. Keep the owner success path, add the cross-tenant `404` assertion, and retain the missing-principal, invalid-request, duplicate-create, and repeated-worker checks from [Software Testing Strategy / 软件测试策略](#26.%20How%20should%20test%20boundaries%20prove%20the%20failure%20risks%20that%20matter?%20/%20%E5%A6%82%E4%BD%95%E9%80%89%E6%8B%A9%E6%B5%8B%E8%AF%95%E8%BE%B9%E7%95%8C%E6%9D%A5%E8%AF%81%E6%98%8E%E5%85%B3%E9%94%AE%E6%95%85%E9%9A%9C%E9%A3%8E%E9%99%A9%EF%BC%9F). Those nearby checks show that the fix did not break the surrounding route and persistence behavior. They do not prove production identity validation or broker semantics, which were not part of this reproduction.

### Read a generated change against the requirement / 对照需求独立阅读生成式改动

Read the requirement first and write down the expected outcomes before using the generated tests as a guide. Then inspect the changed route, its callers and dependencies, the query or transaction it reaches, and the error/response mapping. Compare the assertions with that expected behavior: in this case, a suite that tests only `tenant-a` cannot detect a missing tenant predicate, even if every generated test passes.

Run the minimal counterexample against the changed code, inspect the actual query and row returned, apply the narrow fix, then run the owner and non-owner cases plus relevant nearby checks. Read the new tests too: verify that they reach the changed route and real database boundary, that their fixtures establish the intended principal, and that they assert the required failure rather than only a happy-path response. For a database or delivery claim, identify the engine or broker the test actually used; a stubbed session or local function call is evidence only for that seam.

The review is complete when the observed failure, its cause, the changed behavior, and the regression evidence line up with the requirement. A model-written test passing is one observation, not independent proof that the requirement is complete. Keep the change as small as the cause allows: this example needs the missing query predicate and its negative regression assertion, not a new repository layer or review-management process.

**Interview answer / 面试回答：** I first state the expected behavior, trace the entry point through the relevant dependency and data access, and build the smallest request that can disprove my hypothesis. Here, the other tenant receives the row because the generated refactor drops the tenant condition. Restoring that condition and running both owner and non-owner requests is the focused fix and regression check. I read the generated implementation and tests independently because their shared assumptions can omit the same requirement. / 我先明确预期行为，再沿入口、依赖和数据访问追踪调用路径，并构造能够推翻假设的最小请求。这个例子中，另一租户读到了任务，是因为生成式重构删掉了租户条件。恢复该条件并分别运行所有者和非所有者请求，就是聚焦的修复与回归验证。我会独立阅读生成实现和测试，因为二者可能共享同一个遗漏假设。

**Sources checked 2026-10-15:** GitHub's official [reviewing proposed changes](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests) documentation describes inspecting commits and diffs, and its [review concepts](https://docs.github.com/en/pull-requests/concepts/giving-reviews) explain review feedback and deeper inspection. The reproduced tenant behavior and query correction are exercised in the linked synthetic API example; no personal project or generated artifact is used.
## 26. How should test boundaries prove the failure risks that matter? / 如何选择测试边界来证明关键故障风险？

**核心回答 / Core answer：** Choose the narrowest boundary that can exercise the failure condition: isolate a pure rule with a unit test, connect the real route and principal seam for API behavior, and let the selected database execute SQL for constraints and transactions. Use the configured broker or a deployed-like journey when delivery guarantees or assembled wiring are the risk. The FastAPI example below proves route behavior and local SQLite state transitions; it does not prove production identity, PostgreSQL behavior, broker redelivery, or external effects. / 选择能够触达故障条件的最小测试边界：纯规则用单元测试隔离；API 行为接入真实路由和主体接缝；约束与事务由所选数据库实际执行 SQL 验证。若风险在消息投递保证或部署后的组件装配，就纳入配置好的 broker 或近似生产的端到端链路。下方 FastAPI 示例能证明路由行为和 SQLite 本地状态变更，不能证明生产身份认证、PostgreSQL 行为、broker 重投或外部副作用。

**Key terms / 关键术语：** unit test / 单元测试；integration test / 集成测试；compatibility contract / 兼容性契约；end-to-end (E2E) test / 端到端测试；fixture / 测试夹具；test seam / 测试接缝；test double / 测试替身。

### Choose the boundary from the failure risk / 按故障风险选择测试边界

| Risk | Useful boundary | Evidence that boundary can provide |
|---|---|---|
| A pure rule maps input to the wrong result | Unit | The rule's inputs and outputs, with unrelated I/O absent. |
| A route validates the wrong shape, returns the wrong status, or skips tenant authorization | API integration | The actual router, request validation, dependency path, response serialization, and error mapping. An in-process client does not exercise a network socket or production identity provider. |
| Duplicate keys, rollback, or a conditional update violate a durable invariant | Database integration | The selected database engine executes the schema and statements. A mock session cannot prove a constraint or transaction. |
| An existing consumer can no longer read a response | Compatibility contract | Compare a pinned or published schema and representative consumer expectations with the provider's current output. Checking only a freshly generated schema does not prove compatibility with an older client. |
| A queue redelivery or acknowledgement order causes a duplicate or lost effect | Broker integration | The configured broker, acknowledgement mode, consumer, and durable store exercise the delivery boundary. Calling a handler twice tests its database behavior, not broker delivery guarantees. |
| Login, API, database, and worker wiring fail only when assembled | End-to-end | A controlled deployed-like journey with the actual selected services and identities. It is slower and narrower in number; use it for failures that depend on that wiring. |

These are complementary boundaries, not a required test-count pyramid. Keep quick, deterministic checks close to the risk, then add a higher-boundary check only when it proves something the lower one cannot. The existing [Frontend Testing / 前端测试](../../frontend/testing/frontend-testing.md) note owns Jest, component, browser, and frontend release examples; this note applies the same risk-and-feedback idea to API, persistence, and delivery boundaries.

### One job API with a database-backed worker / 一个带数据库 worker 的任务 API

The small example below creates a tenant-owned job. `POST /jobs` validates a request and gives the same tenant's request key a database uniqueness rule. `GET /jobs/{id}` scopes lookup by the current tenant. A worker delivery changes `pending` to `done` with one conditional database update; replaying the same job ID must not increment the effect counter twice.

The fixture creates a fresh in-memory SQLite database for each test and keeps it on one shared connection so the in-process test client and the test's database inspection see the same database. The `Session` dependency and worker's session-factory argument are deliberate seams: they control database lifetime while still executing real SQL against SQLite. `X-Tenant-ID` stands in for a principal supplied by trusted authentication middleware; it is a test input, not an authentication scheme to trust in a deployed service. For the general authorization rule, see [Web Security and Authentication / Web安全与身份认证](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F). The queue call is represented by calling the worker twice; no broker is present.

~~~python
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from sqlalchemy import Integer, String, UniqueConstraint, create_engine, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_key", name="uq_job_tenant_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(60), nullable=False)
    request_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(12), nullable=False, default="pending")
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class JobCreate(BaseModel):
    request_key: str = Field(min_length=1, max_length=64)
    payload: str = Field(min_length=1, max_length=200)


class JobView(BaseModel):
    id: int
    request_key: str
    state: str
    processed_count: int


def tenant_from_test_header(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=401, detail="authentication required")
    return x_tenant_id


def get_session(request: Request):
    with request.app.state.session_factory() as session:
        yield session


def create_app() -> FastAPI:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    app = FastAPI()
    app.state.engine = engine
    app.state.session_factory = session_factory

    @app.post(
        "/jobs",
        status_code=201,
        response_model=JobView,
        responses={
            401: {"description": "Authentication required"},
            409: {"description": "Request key already exists for this tenant"},
        },
    )
    def create_job(
        body: JobCreate,
        tenant_id: Annotated[str, Depends(tenant_from_test_header)],
        session: Annotated[Session, Depends(get_session)],
    ):
        try:
            with session.begin():
                job = Job(
                    tenant_id=tenant_id,
                    request_key=body.request_key,
                    payload=body.payload,
                )
                session.add(job)
                session.flush()
                response = JobView(
                    id=job.id,
                    request_key=job.request_key,
                    state=job.state,
                    processed_count=job.processed_count,
                )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="request key already exists")
        return response

    @app.get("/jobs/{job_id}", response_model=JobView)
    def read_job(
        job_id: int,
        tenant_id: Annotated[str, Depends(tenant_from_test_header)],
        session: Annotated[Session, Depends(get_session)],
    ):
        job = session.scalar(
            select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
        )
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return JobView(
            id=job.id,
            request_key=job.request_key,
            state=job.state,
            processed_count=job.processed_count,
        )

    return app


def deliver_job(session_factory, job_id: int) -> str:
    with session_factory() as session, session.begin():
        result = session.execute(
            update(Job)
            .where(Job.id == job_id, Job.state == "pending")
            .values(state="done", processed_count=Job.processed_count + 1)
        )
        if result.rowcount == 1:
            return "processed"
        return "duplicate" if session.get(Job, job_id) is not None else "missing"


@pytest.fixture
def app():
    application = create_app()
    yield application
    application.state.engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def headers(tenant_id: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id}


def test_api_schema_auth_and_tenant_scope(client):
    body = {"request_key": "daily-7", "payload": "sample"}
    assert client.post("/jobs", json=body).status_code == 401
    assert client.post(
        "/jobs", headers=headers("tenant-a"), json={"request_key": "", "payload": "x"}
    ).status_code == 422

    created = client.post("/jobs", headers=headers("tenant-a"), json=body)
    assert created.status_code == 201
    assert set(created.json()) == {"id", "request_key", "state", "processed_count"}
    assert created.json()["state"] == "pending"

    job_id = created.json()["id"]
    own_read = client.get(f"/jobs/{job_id}", headers=headers("tenant-a"))
    other_read = client.get(f"/jobs/{job_id}", headers=headers("tenant-b"))
    assert own_read.status_code == 200
    assert other_read.status_code == 404


def test_openapi_exposes_the_public_request_and_response_shape(client):
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/jobs"]["post"]
    assert {"201", "401", "409", "422"} <= set(operation["responses"])
    request_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_ref = operation["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
    request_schema = schema["components"]["schemas"][request_ref.rsplit("/", 1)[1]]
    response_schema = schema["components"]["schemas"][response_ref.rsplit("/", 1)[1]]
    assert set(request_schema["properties"]) == {"request_key", "payload"}
    assert set(response_schema["properties"]) == {"id", "request_key", "state", "processed_count"}


def test_database_unique_constraint_rolls_back_duplicate_create(client, app):
    body = {"request_key": "daily-7", "payload": "sample"}
    first = client.post("/jobs", headers=headers("tenant-a"), json=body)
    duplicate = client.post("/jobs", headers=headers("tenant-a"), json=body)
    assert first.status_code == 201
    assert duplicate.status_code == 409

    with Session(app.state.engine) as session:
        count = session.scalar(select(func.count()).select_from(Job))
    assert count == 1


def test_replayed_worker_delivery_changes_database_once(client, app):
    created = client.post(
        "/jobs",
        headers=headers("tenant-a"),
        json={"request_key": "daily-8", "payload": "sample"},
    )
    job_id = created.json()["id"]

    assert deliver_job(app.state.session_factory, job_id) == "processed"
    assert deliver_job(app.state.session_factory, job_id) == "duplicate"
    result = client.get(f"/jobs/{job_id}", headers=headers("tenant-a"))
    assert result.json()["state"] == "done"
    assert result.json()["processed_count"] == 1
~~~

Extract that block into `test_jobs.py` and run `python -m pytest -q test_jobs.py`. The tests assert visible API behavior, the request and response schema exposed by this app, an actual SQLite uniqueness violation with rollback, and a repeated worker call against the same database. The OpenAPI assertion checks this version's declared shape; a compatibility gate should compare with a released schema or exercise a real supported consumer before claiming an older client remains compatible.

The database is SQLite 3.51.0 through SQLAlchemy 2.0.44. This is a real database engine and the test executes its unique constraint and transaction, but its locking, typing, SQL dialect, and concurrency behavior do not establish PostgreSQL behavior. `TestClient` exercises FastAPI through an in-process ASGI transport, not a live server, network, production authentication provider, or deployed application. `deliver_job` exercises a repeated database operation; it does not prove a broker's redelivery, acknowledgement, ordering, or outage guarantees. Those claims need a broker-backed integration test using the selected broker's configuration. External side effects such as email or payment also need an outbox or downstream idempotency boundary; this example changes only local database state. See [safe retries](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) and [broker acknowledgements](#14.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) for the separate contracts. For the session and transaction lifecycle, see [Data Access and Connection Pools / 数据访问与连接池](#10.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F).

**Interview answer / 面试回答：** I start from the failure risk and choose the lowest boundary that can prove it. Here the API tests verify validation, public response shape, and tenant-scoped access; a real SQLite database verifies uniqueness and rollback; the repeated worker call verifies the local idempotent state transition. I would add a contract comparison for compatibility and a broker-backed test before claiming delivery or acknowledgement guarantees. / 我先从故障风险出发，选择能够证明该风险的最低边界。这个例子用 API 测试验证输入校验、公开响应结构和租户范围访问，用真实 SQLite 验证唯一性约束与回滚，再用重复 worker 调用验证本地幂等状态变更。要声称兼容既有客户端或消息投递确认语义，还需要契约对比和真实 broker 测试。

**Sources checked 2026-10-15:** [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/) and [testing dependencies with overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/) for in-process request checks and dependency seams; [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) for function-scoped setup and cleanup; SQLAlchemy 2.0 [constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html), [session transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), and [SQLite pooling](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads-or-coroutines); SQLite [CREATE TABLE and UNIQUE constraints](https://www.sqlite.org/lang_createtable.html) and [transactions](https://www.sqlite.org/lang_transaction.html). Runtime behavior was checked with the versions recorded above; the live FastAPI documentation is not a substitute for the named runtime check.
## 27. How do you integrate, revise, or recover Git history without losing work? / 如何在不丢失工作的前提下集成、修改或恢复 Git 历史？

Git stores snapshots behind movable branch references, while the working tree and index hold changes not yet committed. Choose merge or rebase based on whether others rely on the commits, and choose reset, revert, or reflog recovery according to which local or shared history state must change. These commands repair repository history and files; they do not roll back a deployed application, database migration, or external side effect. / Git 用提交保存快照，分支是可移动引用；工作区和暂存区保存尚未提交的修改。根据提交是否已被他人依赖选择合并或变基，再根据需要改变的是哪部分本地或共享历史选择 reset、revert 或 reflog 恢复。这些命令修复的是仓库历史和文件，不会回滚已部署应用、数据库迁移或外部副作用；生产恢复见[应用部署与持续交付](#30.%20How%20do%20you%20promote%20one%20validated%20artifact%20and%20recover%20each%20state%20layer%20safely?%20/%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B7%B2%E9%AA%8C%E8%AF%81%E4%BA%A7%E7%89%A9%E5%B9%B6%E5%88%86%E5%88%AB%E6%81%A2%E5%A4%8D%E5%90%84%E5%B1%82%E7%8A%B6%E6%80%81%EF%BC%9F)。

### Core commands

| Command | Purpose |
|---|---|
| `git init` | Create an empty repository in the current directory |
| `git clone <url>` | Copy a repository and its history |
| `git status` | Show branch and working-tree state |
| `git add <path>` | Stage changes for the next commit |
| `git diff` | Show unstaged changes; use `--staged` for staged changes |
| `git commit -m "message"` | Record the staged snapshot |
| `git log --oneline --graph --decorate` | Inspect recent history and branch references |

Stage deliberately. `git add .` stages changes under the current directory; `git add -A` stages additions, modifications, and deletions in the repository. Review `git diff --staged` before committing.

### Remote operations

~~~bash
git remote add origin <url>
git fetch origin
git push -u origin main
git pull
~~~

`git fetch` updates remote-tracking references without integrating them into the current branch. `git pull` fetches and then integrates the selected upstream using the configured or requested fast-forward, merge, or rebase behavior; inspect its options when the result matters. Fetch first when you want to review incoming commits before integrating them.

### Branching

~~~bash
git branch feature/login       # create a branch
git switch feature/login       # switch branches
git switch -c feature/login    # create and switch
git branch -d feature/login    # delete only when Git considers it merged
git branch -D feature/login    # force-delete the branch reference
~~~

A feature branch is one collaboration approach. A team can instead integrate small changes directly or use a release-branch strategy. Git Flow adds long-lived branches such as `develop`; it can suit scheduled releases but adds merging and coordination. Choose according to release and integration needs rather than treating one strategy as universal.

### Merge vs. rebase

#### `git merge`

Merge integrates another branch into the current branch. If possible, Git may fast-forward the current branch reference; otherwise it creates a merge commit that records both parent histories.

~~~bash
git switch main
git merge feature/login
~~~

~~~
A---B---C---M  main
     \     /
      D---E    feature/login
~~~

#### `git rebase`

Rebase replays commits onto a new base. The replayed commits have new IDs because their parent history changes.

~~~bash
git switch feature/login
git rebase main
~~~

~~~
A---B---C              main
         \
          D'---E'      feature/login
~~~

| Situation | A common choice | Why |
|---|---|---|
| Integrating work while keeping both branch histories visible | Merge | Records the integration point when a merge commit is created |
| Updating an unpublished local branch | Rebase | Replays local commits on the updated base |
| Commits others have already based work on | Coordinate before rebasing | Rebase changes commit IDs and requires collaborators to reconcile history |

A rebase can be useful on a shared branch only when the team coordinates the history rewrite and remote update. The practical rule is to avoid rewriting commits others may rely on.

### Resolving conflicts

When Git cannot combine edits automatically, it marks the affected file:

~~~
<<<<<<< HEAD
const timeout = 3000;
=======
const timeout = 5000;
>>>>>>> feature/login
~~~

1. Inspect the conflict and decide how the changes should combine.
2. Remove the conflict markers and edit the final content.
3. Stage the resolved path with `git add <path>`.
4. Finish with `git commit` after a merge, or `git rebase --continue` during a rebase.

Use `git merge --abort` or `git rebase --abort` to stop an integration that is still in progress.

### Useful commands

#### `git stash`

Save tracked working-tree changes temporarily when switching tasks or branches.

~~~bash
git stash push -m "work in progress"
git stash list
git stash apply       # keep the stash entry
git stash pop         # apply and remove the stash entry if successful
git stash drop        # discard a stash entry
~~~

Untracked files are not included by default; use `-u` when they should be included.

#### `git cherry-pick`

Apply the change introduced by a selected commit to the current branch, creating a new commit.

~~~bash
git cherry-pick <commit>
~~~

### Undo or recover by state layer / 按状态层撤销与找回

First ask whether the change lives in the working tree, index, or commit history, and whether others already rely on the commit. For example, if a bad change is already on a shared branch, `git revert <commit>` records a new inverse change. It preserves the published commit identity. Reverting a merge commit requires choosing the mainline parent. Resolve conflicts and verify what the inverse change actually does.

For an unshared local commit, `git reset <target>` can move the current branch. Choose what else should change.

| Reset mode | Branch | Index | Working tree |
| --- | --- | --- | --- |
| `--soft` | Move to target | Keep | Keep |
| `--mixed` | Move to target | Set to target | Keep |
| `--hard` | Move to target | Set to target | Set to target, discarding tracked local edits that differ from the target and possibly overwriting untracked paths |

Use `git status` and save any edits you need before a hard reset. If a local branch moved by mistake, inspect `git reflog`, find the prior commit, and make it reachable again with `git branch recovery <commit>`. Inspect that new branch before applying or restoring anything. Reflogs are local and expire, so use another durable copy for backup. / 共享提交通常用 revert 产生新的撤销记录。只调整本地分支时，按需要保留的暂存区与工作区选择 reset 模式。误移动后可从 reflog 找旧提交并先用新分支保留。 [Git reset](https://git-scm.com/docs/git-reset) · [Git reflog](https://git-scm.com/docs/git-reflog)

### Pull request and code review workflow

A common workflow is to branch from the repository's integration branch, commit focused changes, push, open a pull request, review and revise, then merge using the repository's chosen method. The exact branch name and merge policy vary by project.

For commits, concise messages that describe the change help future readers. **Conventional Commits** is one optional convention, often paired with tooling that reads its prefixes:

~~~
feat(auth): refresh access tokens
fix(api): handle missing user
refactor(utils): extract date formatting
docs(readme): clarify setup
~~~

**See also:** [Agile and Scrum](#46.%20How%20does%20Scrum%20help%20a%20team%20inspect%20and%20adapt%20work?%20/%20Scrum%20%E5%A6%82%E4%BD%95%E5%B8%AE%E5%8A%A9%E5%9B%A2%E9%98%9F%E6%A3%80%E6%9F%A5%E5%B9%B6%E8%B0%83%E6%95%B4%E5%B7%A5%E4%BD%9C%EF%BC%9F) for team-process context, and [Frontend Testing](../../frontend/testing/frontend-testing.md) for CI checks in a pull request.

Sources: [Git pull](https://git-scm.com/docs/git-pull), [Git merge](https://git-scm.com/docs/git-merge), [Git rebase](https://git-scm.com/docs/git-rebase), [Git reset](https://git-scm.com/docs/git-reset), [Git revert](https://git-scm.com/docs/git-revert), [Git reflog](https://git-scm.com/docs/git-reflog), [Git stash](https://git-scm.com/docs/git-stash), and [Git cherry-pick](https://git-scm.com/docs/git-cherry-pick). Git manuals checked 2026-10-15.
## 28. How do images, containers, volumes, and networks determine state and connectivity? / 镜像、容器、卷和网络如何决定状态留存与服务连通？

An image supplies the read-only filesystem and configuration template; a container adds a writable runtime layer; a volume stores data beyond container replacement; and a shared network gives services a path to reach one another. Port publishing exposes a container port through the host, while secrets belong in the build or runtime channel that needs them. The commands and Compose examples below show what survives removal and how services connect. / 镜像提供只读文件系统和配置模板，容器增加运行时可写层，卷让数据独立于容器替换而留存，共享网络则让服务彼此连通。端口发布通过宿主机暴露容器端口；密钥应只进入实际需要它的构建或运行时通道。下面的命令和 Compose 示例说明删除容器后什么会保留，以及服务如何通信。

Before starting a fresh `postgres:16` instance in the examples below, provide a non-empty `POSTGRES_PASSWORD` through the shell environment or a secret manager. The official image requires it to initialize an empty data directory; it can be passed at runtime without placing a credential in the image or source file. Changing the variable later does not rotate a password in an already initialized volume.

### Common operations

| Task | Command | Notes |
|---|---|---|
| Download an image | `docker pull redis:7` | Pin a tag or digest when repeatability matters; a tag may move. |
| List local images | `docker image ls` | Images can have multiple tags. |
| Create and start a container | `docker run --name cache -d redis:7` | Pulls the image if it is not available locally. |
| List running containers | `docker ps` | Add `-a` to include stopped containers. |
| Stop / start a container | `docker stop cache` / `docker start cache` | A stopped container still exists. |
| Read container logs | `docker logs cache` | Add `-f` to follow new output. |
| Run a command in a running container | `docker exec -it cache /bin/sh` | Run only when the image includes `/bin/sh`; minimal images may contain no shell. |
| Remove a stopped container | `docker rm cache` | `-f` also stops and removes a running container. |
| Remove an image | `docker image rm redis:7` | Refer to an image tag or image ID, not a container ID. |

Detached mode (such as `docker run -d`) returns the terminal while the container's main process runs. It does not supervise an application or guarantee that the container stays healthy. Use `docker ps` and `docker logs` to inspect it.

---

### Publish ports

A port mapping forwards a host port to a port in the container. This publishes a container service to the host network; it does not make the service healthy or authenticated.

~~~bash
docker run -d --name cache -p 127.0.0.1:6000:6379 redis:7
~~~

For the default bridge/NAT configuration on Docker Engine 28 and later, a localhost-published port is scoped to the Docker host. Earlier Engine releases had an exception where hosts on the same Layer 2 network could reach a localhost-published port. Check the actual Engine version, network mode and routing before relying on the bind for exposure control. [Docker port publishing, checked 2026-11-06](https://docs.docker.com/engine/network/port-publishing/) Omitting the host IP generally publishes on all host interfaces, subject to the host and Docker networking configuration. Container-to-container traffic on a shared Docker network normally uses the container port directly, not a published host port.

---

### Networks

A user-defined bridge network lets attached containers communicate by container or service name through Docker's embedded DNS. Network membership controls which containers can connect at the Docker network layer; it is not application authentication or authorization.

~~~bash
docker network create app-net
docker run -d --name db --network app-net \
  --env POSTGRES_PASSWORD postgres:16
~~~

Only expose a host port when a process outside the network needs to connect. In Compose, services join a project network by default and can usually use each other's service names as hostnames.

---

### Volumes and persistent data

Container writable layers are removed with their containers. A **named volume / 命名卷** is managed by Docker and remains after the container is removed. A **bind mount / 绑定挂载** maps a host path into the container and is useful when both host and container need the files. A volume is not a backup; plan backups and restore tests separately.

The examples pin PostgreSQL 16 and mount `/var/lib/postgresql/data`. Starting with the official PostgreSQL 18 image, the default data directory is version-specific and the recommended volume mount is `/var/lib/postgresql`. Check the image's data path when upgrading and migrate or restore the data explicitly. Changing the tag and mount point alone does not upgrade the database files. [Official Postgres image, PGDATA](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)

Omitting the volume source creates an anonymous volume with a generated name; it normally persists after container removal but is not automatically reused by a later container.

~~~bash
docker volume create db-data
docker run -d --name db --env POSTGRES_PASSWORD \
  --mount type=volume,src=db-data,dst=/var/lib/postgresql/data postgres:16
~~~

The destination path belongs to the image or application, so check that product's documentation. Compose declares named volumes at the top level:

~~~yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
~~~

Compose normally preserves declared named volumes on `docker compose down`. Adding `-v` removes project volumes and their data; review that effect before using it.

---

### Compose

Compose describes a multi-container application in a YAML file. The default project network provides service-name discovery, so an application container can address the database as `db` on its container port. Publish a port only when the host or another external network needs access.

~~~yaml
services:
  app:
    build: .
    environment:
      DATABASE_HOST: db
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
~~~

~~~bash
docker compose up -d
docker compose ps
docker compose logs -f app
docker compose down
~~~

The current Compose Specification is used by Compose V2. Its top-level `version` field is obsolete and does not select a schema version. The older standalone `docker-compose` command is a legacy interface; use `docker compose` with the Compose CLI plugin.

---

### Dockerfile and image builds

A Dockerfile describes image build steps. `RUN` executes during build; `CMD` supplies a default command or arguments when a container starts; `ENTRYPOINT` defines the executable to run. A runtime command can override `CMD`.

~~~dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
CMD ["node", "dist/index.js"]
~~~

Build with `docker build -t my-app:1.0 .`. This example assumes a package lockfile. The build context is the set of files sent to the builder; use a `.dockerignore` file to exclude files such as local dependencies, version-control data, and secrets. Multi-stage builds keep build-only stages out of the final image unless files are copied from them. Copy only the runtime files and dependencies the application needs.

Do not put credentials in a Dockerfile's `ENV` or `ARG` values. Use a BuildKit secret mount for a credential needed during build; it is made available to the build instruction without baking it into the image. At runtime, Compose secrets can be granted to selected services and mounted as files; protect the source secret file and host.

~~~dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
~~~

~~~bash
docker build --secret id=npmrc,src=.npmrc -t my-app:1.0 .
~~~

To push an image to a registry, authenticate with that registry, tag the image with its repository address, and push the tag. These commands use placeholders; `docker login` prompts or uses configured credentials, which should not be committed:

~~~bash
docker login registry.example.com
docker tag my-app:1.0 registry.example.com/team/my-app:1.0
docker push registry.example.com/team/my-app:1.0
~~~

Sources: [official PostgreSQL image environment variables and secrets](https://github.com/docker-library/docs/blob/master/postgres/README.md#environment-variables), [Docker image and container concepts](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/), [Docker networking](https://docs.docker.com/engine/network/), [port publishing](https://docs.docker.com/engine/network/port-publishing/), [Docker volumes](https://docs.docker.com/engine/storage/volumes/), [Compose file reference](https://docs.docker.com/compose/compose-file/), [Compose variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/), [`docker run` environment variables](https://docs.docker.com/reference/cli/docker/container/run/#set-environment-variables--e---env), [Docker build secrets](https://docs.docker.com/build/building/secrets/), [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/), [`docker login`](https://docs.docker.com/reference/cli/docker/login/), [`docker tag`](https://docs.docker.com/reference/cli/docker/image/tag/), and [`docker push`](https://docs.docker.com/reference/cli/docker/image/push/). Docker documentation checked 2026-10-15.
## 29. How do deployment components carry a request and share responsibilities? / 部署组件怎样承接请求并分担职责？

Trace compute, networking, and storage along the request path. Managed infrastructure can operate a component, while the application still defines its data, access, workload and recovery policy. / 沿请求路径定位计算、网络和存储。托管基础设施可以代为运行组件，应用仍需定义数据、权限、负载和恢复策略。

### Request and data path / 请求与数据路径

For a typical web application, the browser talks only to public entry points; server-side services reach databases, object storage, and queues through controlled routes and identities:

~~~text
Name lookup, before the connection:
Browser -- DNS query for app.example --> resolver
resolver -- CDN / load-balancer address --> Browser

HTTPS request:
Browser -- HTTPS --> CDN (optional) --> public load balancer
                                          |
                                          v
                                 private API compute
                                  /      |       \
                             database  objects    queue --> workers
~~~

The load balancer terminates or forwards HTTPS and sends requests only to configured targets. Compute runs the API and workers. A database stores structured state, object storage holds large files, and a queue separates work that can finish asynchronously. A browser may upload or download an object through a narrowly scoped, expiring signed URL; that does not require making the storage bucket public.

Network reachability and authorization are separate checks. A route table, firewall or security group decides which network paths exist; an identity and resource policy decides which actions a reachable principal may perform. A common layout exposes only the load-balancer listener, permits API traffic from the load balancer, and permits database traffic only from the API. Keep data services private where the provider supports it, and add controlled outbound access or private service endpoints only when required. A task or workload identity should receive only the actions and resources it needs; application users still need application-level authorization. / 网络可达不等于有权访问：网络规则控制通信路径，IAM 与资源策略控制主体能执行的操作。应用运行身份应只获得所需资源和操作权限；业务用户的授权仍由应用负责。

### Managed service and application responsibilities / 托管服务与应用责任

| Layer / 层 | Provider or platform manages / 平台管理 | Application team owns / 应用团队负责 |
|---|---|---|
| Compute / 计算 | Underlying hardware and, depending on the offer, host maintenance and scheduling. | Image or package, startup and shutdown behavior, resource limits, scaling policy, and application health. |
| Database / 数据库 | Database service infrastructure and only the backups, patching, and failover included in the selected configuration. | Schema and migrations, query and connection behavior, access grants, retention choices, and restore testing. |
| Object storage / 对象存储 | Storage service availability and documented durability mechanisms. | Object naming, privacy, retention/lifecycle, upload limits, and who receives a signed URL. |
| Queue / 队列 | Message storage and delivery within service guarantees and configured limits. | Idempotent processing, retry/backoff, poison-message handling, queue age, and dead-letter recovery. |

“Managed” removes some infrastructure work; it does not choose safe defaults for the workload. Read the service contract and configuration: automated backups, retention, public access, network placement, and failover behavior are often selectable. A managed database cannot fix an unindexed query or a connection storm, and a managed queue cannot make a non-idempotent consumer safe to retry.

Choose a runtime by workload constraints. A managed application platform or function service can reduce host operations for ordinary stateless APIs or bounded event-driven jobs, subject to its execution, startup, and networking limits. A managed container service fits long-running APIs and queue workers when packaging and process control matter. Use virtual machines when the workload needs host-level control or a legacy environment, and budget for operating-system patching and capacity management. Compare steady and peak load, required minimum capacity, startup/cold-start tolerance, execution duration, portability, and the team’s ability to operate the platform; “serverless” does not mean state-free or cost-free.

#### What the runtime still leaves to the application / 运行平台仍留给应用的责任

A managed function service owns the execution infrastructure, while the application owns durable state, resource cleanup and idempotent behavior across retries. For example, AWS Lambda may reuse an execution environment. A cached client can reduce setup time on a warm call. An in-memory counter in that environment cannot be the authoritative history across invocations, concurrent workers, or restarts. Persist progress externally. / 云函数平台可复用执行环境，应用仍要把持久状态、重试语义与资源清理设计清楚。

Compare duration, concurrency, cold starts, billing and long-lived connections against the selected provider and plan. Choose a function for a bounded event-driven job when those limits fit. For long-lived connections or jobs that may outlast an invocation, compare an API or worker runtime with explicit process and shutdown controls. [AWS Lambda execution lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) · [Lambda application design](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html) · [API retries and uncertain outcomes](#12.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)

### Failure and cost model / 故障与成本模型

| Boundary / 边界 | Failure to plan for / 需要考虑的故障 | Cost or limit to watch / 成本或限制 |
|---|---|---|
| Load balancer and network / 负载均衡与网络 | Bad route or listener, no healthy targets, blocked egress, or an expired certificate. | Requests and processed bytes, public addresses, NAT gateways, and cross-zone or internet data transfer. |
| Compute / 计算 | Startup failure, crash loop, CPU/memory saturation, or slow scale-out. | Minimum replicas and CPU/memory time; autoscaling cannot create capacity instantly. |
| Database / 数据库 | Exhausted connections, lock contention, storage or I/O limits, or failover delay. | Provisioned compute, storage, I/O, replicas, and retained backups. |
| Object storage / 对象存储 | Permission errors, unavailable routes, unexpectedly public objects, or unbounded retention. | Stored bytes, requests/retrieval, lifecycle transitions, replication, and outbound transfer. |
| Queue and workers / 队列与工作进程 | Duplicate or delayed delivery, poison messages, or growing backlog. | Requests, retained messages, worker compute, and the delay before backlog drains. |

Track each boundary with a useful signal: request errors and latency at ingress, ready replica count and saturation for compute, connection/query pressure for the database, request errors and object growth for storage, and oldest-message age plus dead-letter count for a queue. Cost estimates should include idle minimums and peak headroom as well as per-use storage, requests, and data movement; a service with a low unit price can still be expensive when retries or egress multiply the workload.

[Back to the main question / 返回主问题](#30.%20How%20do%20you%20promote%20one%20validated%20artifact%20and%20recover%20each%20state%20layer%20safely?%20/%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B7%B2%E9%AA%8C%E8%AF%81%E4%BA%A7%E7%89%A9%E5%B9%B6%E5%88%86%E5%88%AB%E6%81%A2%E5%A4%8D%E5%90%84%E5%B1%82%E7%8A%B6%E6%80%81%EF%BC%9F).
## 30. How do you promote one validated artifact and recover each state layer safely? / 如何晋级已验证产物并分别恢复各层状态？

Build one immutable application artifact, test those exact bits, and promote the same artifact through staging to production with runtime configuration supplied separately. Readiness and gradual rollout protect traffic while error, latency, and saturation signals establish whether to stop or return to the last known-good application version. Persistent data and external effects have separate owners and recovery paths: image rollback cannot reverse a database migration, sent email, payment, or other completed action. / 构建一个不可变应用产物，验证这份确切产物，再把同一产物从预发环境晋级到生产，并单独注入运行时配置。就绪检查和渐进式放量保护流量，错误率、延迟和资源饱和信号决定是否暂停或恢复到上一个已知正常的应用版本。持久数据和外部副作用各有其所有者与恢复路径：镜像回滚不能撤销数据库迁移、已发送邮件、支付或其他已完成操作。

The [production request path and responsibility model](#29.%20How%20do%20deployment%20components%20carry%20a%20request%20and%20share%20responsibilities?%20/%20%E9%83%A8%E7%BD%B2%E7%BB%84%E4%BB%B6%E6%80%8E%E6%A0%B7%E6%89%BF%E6%8E%A5%E8%AF%B7%E6%B1%82%E5%B9%B6%E5%88%86%E6%8B%85%E8%81%8C%E8%B4%A3%EF%BC%9F) explains which components run the service and own its data. The following steps focus on how a tested artifact safely replaces the one serving traffic.

### One artifact from checks to production / 一个产物经过检查再到生产

Use one generic path and adapt the checks to actual regression risks:

~~~text
commit
  -> static/type checks -> unit and integration checks -> production build
  -> test the built artifact -> publish it with commit and content identity
  -> deploy that same artifact to staging -> smoke/browser check
  -> protected production gate -> gradual traffic shift -> observe and complete
~~~

Build once, then promote the same artifact. For a container, record and deploy its immutable digest rather than a mutable tag; for a static bundle, retain a checksum or release identifier with the emitted files. Rebuilding separately for staging and production weakens the claim that the tested bits are the deployed bits. If frontend configuration is compiled into the bundle, that bundle is environment-specific; a shared artifact needs safe public runtime configuration. Values shipped to a browser are public, never secrets.

Inject secrets at runtime from a secret store or protected deployment environment, and give the deployment identity only the permissions needed for its target. Keep non-secret environment configuration separate from the image. A deployment environment can also restrict source branches, protect production with approval, and scope access to environment secrets; these controls protect the release gate, while credentials still need rotation and least privilege.

Readiness is a traffic gate: an instance should receive requests only when it can serve its assigned work. Liveness is a restart signal for a process that cannot recover on its own. Exact probe behavior varies by platform; do not make liveness depend on every transient downstream service, since a database outage can then trigger a restart storm. Roll out gradually when the platform and workload permit it, watch a small set of error, latency, and saturation thresholds, and stop or redeploy the last known-good artifact when they cross the release limit. A green process probe alone does not prove the user journey works.

Database changes need an independent compatibility plan. A common expand-and-contract sequence adds a backward-compatible schema shape, deploys code that tolerates both shapes, backfills or dual-writes as needed, switches reads, and removes the old shape only after old code and the rollback window are gone. Run migrations as a controlled step rather than once per replica. Redeploying an older image does not reverse a schema migration, sent email, payment, or other external side effect; rollback may require a forward fix, an idempotent compensating action, or a tested restore plan. Restoring a backup can discard writes made after that backup, so it is a recovery decision rather than a routine application rollback.

For the frontend-specific type/test/build and critical-browser-check sequence, see [Frontend Testing / 前端测试](../../frontend/testing/frontend-testing.md). The existing [Docker Operations / Docker操作参考](#28.%20How%20do%20images,%20containers,%20volumes,%20and%20networks%20determine%20state%20and%20connectivity?%20/%20%E9%95%9C%E5%83%8F%E3%80%81%E5%AE%B9%E5%99%A8%E3%80%81%E5%8D%B7%E5%92%8C%E7%BD%91%E7%BB%9C%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%8A%B6%E6%80%81%E7%95%99%E5%AD%98%E4%B8%8E%E6%9C%8D%E5%8A%A1%E8%BF%9E%E9%80%9A%EF%BC%9F) note covers image construction and local container mechanics.

**Interview answer / 面试回答：** Start with the request/data path and trust boundaries, then choose the least operational runtime that meets workload constraints. Build and verify one immutable artifact, inject runtime configuration and secrets, release behind readiness and monitored thresholds, and keep schema or external-state recovery separate from image rollback. / 先画出请求和数据路径及信任边界，再按负载约束选择运维负担最低的运行时。构建并验证一个不可变产物，运行时注入配置和密钥，在就绪检查与监控阈值保护下发布，并把数据库和外部状态的恢复方案与镜像回滚分开。

**Sources checked 2026-10-15:** [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html); [AWS VPC network example](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-example-private-subnets-nat.html); [ECS task IAM roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html); [Application Load Balancer health checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html); [ECS deployment circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html); [Kubernetes startup, readiness and liveness probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/); [Amazon RDS shared responsibility and query tuning](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/); [Amazon S3 access control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-management.html); [S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html); [Amazon SQS standard queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html); [SQS dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html); [AWS Fargate pricing dimensions](https://aws.amazon.com/fargate/pricing/); [Amazon RDS pricing](https://aws.amazon.com/rds/pricing/); [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/); [Docker Compose in production](https://docs.docker.com/compose/how-tos/production/); [Docker image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/); [GitHub Actions deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments); [CodeDeploy rollback behavior](https://docs.aws.amazon.com/codedeploy/latest/userguide/deployments-rollback-and-redeploy.html); [Vite static deployment](https://vite.dev/guide/static-deploy.html). AWS examples document one provider's current service boundaries and are not universal defaults; verify the selected provider, service, region, and configuration.
## 31. How do you diagnose an API SLO violation? / 如何诊断 API SLO 违约？

**Core model / 核心模型:** Start from the outcome users need, measure it with a clear service-level indicator, and use correlated metrics, traces, and logs to find which stage is failing. Metrics show the aggregate shape; a trace follows one request across stages; logs explain specific events. / 从用户需要的结果开始，用明确定义的服务等级指标衡量它，再用相互关联的指标、追踪和日志定位故障阶段。指标显示整体趋势，追踪串起单个请求的各阶段，日志说明具体事件。

**Key terms / 关键术语:** service-level indicator (SLI) / 服务等级指标；service-level objective (SLO) / 服务等级目标；service-level agreement (SLA) / 服务等级协议；error budget / 错误预算；trace / 分布式追踪；span / 跨度；cardinality / 基数。

**Core answer / 核心回答：** SLI 是符合资格的用户请求中“好事件 / 总事件”的实测比例；SLO 是该比例在指定时间窗内应达到的目标；SLA 是对外业务协议，可能规定计量方式和未达标后果。例：30 天内 10,000 次有效请求中，9,940 次在 400 ms 内成功，SLI 为 99.4%；若 SLO 为 99.5%，错误预算是 `(1 − 99.5%) × 10,000 = 50` 次坏事件，实际 60 次即超出 10 次。告警后先确认用户影响和分母，再沿 trace 定位慢/失败阶段并查关联日志；根据证据缓解，以用户 SLI 和依赖信号验证恢复，并记录原因与后续改进。

~~~mermaid
flowchart LR
    Metrics[Metric shows user-impact window and scope] --> Trace[Representative trace locates slow or failed stage]
    Trace --> Logs[Correlated logs explain that event]
    Logs --> Mitigate[Choose evidence-based mitigation]
    Mitigate --> Verify[Verify user SLI and dependency recovery]
    Verify --> Learn[Record cause and follow-up]
~~~

### Follow one request through three signals / 用三种信号跟踪一个请求

Consider a generic catalog lookup: `client → API edge → catalog service → cache/database → response`. Instrument the boundaries that make up this user action. Propagate trace context across service calls so spans from the edge, service, and database client can be assembled into one trace. A span is one timed operation; parent-child spans show which sub-operation took time. Context propagation connects spans across process and network boundaries. [OpenTelemetry: traces](https://opentelemetry.io/docs/concepts/signals/traces/) and [context propagation](https://opentelemetry.io/docs/concepts/context-propagation/).

| Signal / 信号 | What it answers / 回答的问题 | Example for the lookup / 查询示例 |
|---|---|---|
| **Metrics / 指标** | Is the service broadly healthy, and when did behavior change? | Count eligible requests and failures; measure end-to-end duration, dependency duration, in-flight work, and resource saturation over time. Metrics aggregate measurements, so they are efficient for trends and alerts. |
| **Traces / 追踪** | Which stage made this particular request slow or unsuccessful? | One trace contains a root request span and child spans for cache and database work. Compare their durations and statuses to see where time accumulated. |
| **Logs / 日志** | What event or decision happened at that stage? | A structured record such as `cache_lookup=miss` or `database_timeout` adds event detail. Include the active `trace_id` and `span_id` when available so the record can be found from the trace. |

Start with the metric to find the affected time window, route, and outcome. Then inspect a representative slow or failed trace and follow its child spans. Use the trace and span identifiers to find detailed log events from the same request. For example, an edge metric may show that catalog lookups are slow, a trace may show most of one request's 700 ms elapsed in the database span, and a correlated log may show that the connection pool waited before timing out. The metric establishes scope, the trace locates the stage, and the log gives event detail. [OpenTelemetry: signals](https://opentelemetry.io/docs/concepts/signals/) describes the three signal types; its [logs guide](https://opentelemetry.io/docs/concepts/signals/logs/) describes correlating logs with active traces and spans.

Signals have different coverage. Metrics can remain useful when traces are sampled, but a missing trace is not proof that no request or failure occurred. Check telemetry freshness and instrumentation coverage before treating silence as recovery.

### Keep telemetry safe and bounded / 让遥测信息安全且有界

Use stable, low-cardinality metric dimensions such as route template (`/catalog/{itemId}`), response class, region, and dependency. Do not attach `request_id`, `trace_id`, user or tenant IDs, raw URL paths, search terms, prompts, or other per-request values to metric measurements. Every distinct dimension combination can create another time series and increase aggregation cost; OpenTelemetry's metrics guide warns that user IDs and raw paths can cause unbounded cardinality. [OpenTelemetry: metrics and cardinality limits](https://opentelemetry.io/docs/concepts/signals/metrics/).

Request and trace identifiers are useful correlation fields in logs and traces, where each record is already about an individual event or operation. Treat them as sensitive linkage data: restrict access and retention, and never log credentials, authorization headers, cookies, or raw user content just to make a failure searchable. Prefer stable route names and bounded result categories; redact or omit fields that are not needed to diagnose the service.

### Define a user outcome and its budget / 定义用户结果与预算

An **SLI** is a measured indicator of a service outcome, commonly a ratio of good events to eligible events. An **SLO** is the target for that indicator over a stated period. An **SLA** is an external business agreement that can specify measurement rules and consequences if commitments are missed; an internal SLO is not automatically an SLA. [Google SRE Workbook: Implementing SLOs](https://sre.google/workbook/implementing-slos/) defines event-based SLIs, explains error budgets, and distinguishes an SLA as a business contract.

**Synthetic example / 合成示例.** Suppose a catalog lookup service chooses the following request-based SLI over a rolling 30-day window:

- **Eligible events:** every authenticated, syntactically valid catalog lookup accepted at the public API edge. Exclude synthetic health checks. Keep service errors, timeouts, and requests with no completed response in the denominator.
- **Good event:** the edge completes a successful response in at most 400 ms from acceptance.
- **SLI:** good eligible events ÷ all eligible events.
- **SLO:** at least 99.5% of eligible events are good in the rolling 30-day window.

If the window contains 10,000 eligible lookups and 9,940 are good, the SLI is `9,940 ÷ 10,000 = 99.4%`. The error budget is `1 − 0.995 = 0.5%`, or `10,000 × 0.005 = 50` bad events for this traffic volume. The 60 bad events observed exceed that budget by 10. This event-based calculation weights each request equally; it does not prove every region or user group had the same experience. The chosen edge measurement also does not include the user's device or network after the edge completes its response. Google SRE recommends specifying both the user outcome and how it is measured, because measurement boundaries change what failures are visible.

The SLI must keep its denominator and eligibility rules stable: dropping timeouts or slow successes would make the number look better while excluding users who did not receive a timely result. Report request volume with the ratio, and inspect meaningful low-cardinality slices such as region or route when an overall number hides a localized failure.

### Alert, investigate, mitigate, and learn / 告警、调查、缓解与复盘

For the example SLO, a focused alert could fire when at least 100 eligible lookups occur in a rolling 10-minute window, fewer than 99% are good, and that condition persists for 5 minutes. A minimum event count reduces noise from tiny samples. The alert should carry the SLI numerator, denominator, time window, affected route/region, and links to the relevant metric and trace views. Page when this user-outcome condition holds; internal component signals help explain the cause.

When it fires:

1. **Confirm impact and scope.** Check event counts, SLI trend, error types, route/region, and recent changes. Make sure telemetry is arriving and the denominator still matches the SLI definition.
2. **Locate the stage.** Compare stage and dependency latency, errors, saturation, and in-flight work. Inspect affected traces, then use trace IDs to read the specific correlated logs. For asynchronous work, inspect queue age and depth as part of [capacity and backpressure](#23.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F). [Broker delivery](#14.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) explains the acknowledgement boundary.
3. **Mitigate the user impact.** Choose the smallest safe action supported by evidence, such as rolling back a change that matches the onset or temporarily reducing load on a saturated dependency. Record the action and its expected effect; do not add retries blindly if they can amplify overload.
4. **Verify recovery.** Confirm that the user-facing SLI returns above the alert threshold with adequate traffic, and check the affected stage and dependency signals for continuing saturation or error growth. A quiet alert alone is not evidence that the service recovered.
5. **Follow up.** Record the user impact and time window, the causal mechanism, the mitigation, and a small set of owned changes to prevent recurrence or improve detection. Link the incident to relevant tests and telemetry gaps.

Use the SLO to guide tradeoffs. For AI-backed flows, pair [production signals](../../ai-engineering/systems/ai-production-observability-and-feedback.md) with task-quality measures from [LLM evaluation](../../ai-engineering/evaluation/llm-evaluation-methods.md). HTTP success and latency describe delivery. Task evaluation establishes whether generated answers are useful or correct.

### Sources / 来源

- OpenTelemetry's unversioned concept pages, checked 2026-10-15: [Signals](https://opentelemetry.io/docs/concepts/signals/) (last modified 2026-03-10), [Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/) (2026-04-23), [Traces](https://opentelemetry.io/docs/concepts/signals/traces/) (2026-01-14), [Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/) (2026-07-02), [Logs](https://opentelemetry.io/docs/concepts/signals/logs/) (2026-08-07), and [Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) (2026-08-10).
- [Google SRE Workbook, Chapter 2: Implementing SLOs](https://sre.google/workbook/implementing-slos/), checked 2026-10-15.
## 32. How do input constraints and access patterns determine algorithm choice and complexity? / 输入约束与访问模式如何决定算法选择和复杂度？

Choose an algorithm by the invariant the input provides, then count the work and storage required as the input grows. Dynamic programming reuses overlapping states; binary search discards half of a sorted search range; two pointers move only when ordering proves a region cannot contain the answer. Big-O summarizes that growth under stated assumptions, while representation, allocation, memory locality, and runtime constants still affect elapsed time.

先利用输入所提供的不变量选择算法，再计算输入规模增长时所需的操作和存储。动态规划复用重叠子问题，二分查找利用有序性缩小搜索区间，双指针则只在排序等条件足以证明某一段不含答案时移动。Big-O 概括这些前提下的增长趋势；表示方式、分配、内存局部性和运行时常数仍会影响实际耗时。

Big-O leaves out cache locality, memory bandwidth, and dependent loads. See [Memory Hierarchy and Data Locality / 内存层次与数据局部性](#40.%20Why%20are%20contiguous%20scans%20often%20faster%20than%20linked-list%20walks?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F) for the hardware costs that can change elapsed time without changing an operation's asymptotic bound.

### Match the technique to the input / 按输入约束选择方法

- When several states repeat and each can be defined from earlier ones, choose a [dynamic programming state and update order](#37.%20How%20do%20you%20choose%20a%20dynamic%20programming%20state%20and%20update%20order?%20/%20%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92%E6%80%8E%E6%A0%B7%E9%80%89%E6%8B%A9%E7%8A%B6%E6%80%81%E5%92%8C%E6%9B%B4%E6%96%B0%E9%A1%BA%E5%BA%8F%EF%BC%9F).
- When order rules out a group of candidates, use [binary search or two pointers](#36.%20How%20do%20ordered%20inputs%20enable%20binary%20search%20and%20two%20pointers?%20/%20%E6%9C%89%E5%BA%8F%E8%BE%93%E5%85%A5%E6%80%8E%E6%A0%B7%E6%94%AF%E6%8C%81%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%EF%BC%9F) and prove why the discarded range is safe to ignore.
- If the job is reordering, inspect how [partition balance and copying change sorting cost](#38.%20Why%20do%20partition%20choices%20change%20quicksort%20costs?%20/%20%E5%88%86%E5%8C%BA%E9%80%89%E6%8B%A9%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E6%94%B9%E5%8F%98%E5%BF%AB%E9%80%9F%E6%8E%92%E5%BA%8F%E7%9A%84%E4%BB%A3%E4%BB%B7%EF%BC%9F).
- For text, choose [the units that define length and equality](#39.%20Which%20units%20should%20a%20text%20algorithm%20count%20and%20compare?%20/%20%E6%96%87%E6%9C%AC%E7%AE%97%E6%B3%95%E5%BA%94%E6%8C%89%E4%BB%80%E4%B9%88%E5%8D%95%E4%BD%8D%E8%AE%A1%E6%95%B0%E5%92%8C%E6%AF%94%E8%BE%83%EF%BC%9F) before analyzing a loop.

### Big-O reference

| Complexity | Typical example | Condition |
|---|---|---|
| O(1) | Array index access | Indexed access, not search |
| O(1) average | Hash-table lookup | Expected under ordinary hash distribution |
| O(log n) | Binary search; balanced BST operation | Sorted input or bounded tree height |
| O(n) | Linear scan | One pass |
| O(n log n) | Merge sort; balanced quicksort | Quicksort can degrade to O(n²) |
| O(n²) | Nested scan; simple quadratic sort | Depends on input size and algorithm |
| O(2^n) | Naive recursive Fibonacci; subset enumeration | Exponential growth |
| O(n!) | Permutation enumeration | Factorial growth |

**See also:** [Core Data Structures](#33.%20Which%20data%20structure%20fits%20the%20access%20pattern,%20and%20when%20do%20its%20cost%20bounds%20hold?%20/%20%E5%93%AA%E7%A7%8D%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E9%80%82%E5%90%88%E5%BD%93%E5%89%8D%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F) for trees and tries, and [Practical Data Structure Implementations](#35.%20How%20can%20an%20LRU%20cache%20find%20an%20entry%20and%20update%20recency%20efficiently?%20/%20LRU%20%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E9%AB%98%E6%95%88%E6%89%BE%E5%88%B0%E6%9D%A1%E7%9B%AE%E5%B9%B6%E6%9B%B4%E6%96%B0%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F) for LRU caches and [queues and stacks](#34.%20How%20do%20FIFO%20and%20LIFO%20change%20the%20representation%20of%20pending%20work?%20/%20FIFO%20%E4%B8%8E%20LIFO%20%E6%80%8E%E6%A0%B7%E5%BD%B1%E5%93%8D%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%E7%9A%84%E8%A1%A8%E7%A4%BA%EF%BC%9F) for removal-order implementations.
## 33. Which data structure fits the access pattern, and when do its cost bounds hold? / 哪种数据结构适合当前访问模式，复杂度界何时成立？

Operation cost follows from both the structure and how an operation reaches its target. Arrays provide constant-time indexed access but shift elements on middle insertion; linked lists update in constant time only when the needed link is already known; search trees need logarithmic height for logarithmic search. Traversal order and child representation matter too, and asymptotic bounds do not capture the cost of pointer chasing versus contiguous memory.

操作代价既取决于结构，也取决于操作如何找到目标。数组按下标访问为常数时间，但在中间插入时要移动元素；链表只有在已知所需链接时才能常数时间更新；搜索树只有保持对数高度，搜索才有对数界。遍历顺序和子节点表示也会影响选择，而渐进复杂度无法体现指针追逐与连续内存访问的实际差别。

### Tree traversals

For a binary tree, depth-first orders differ in when the current node is visited:

- **In-order / 中序**: left, node, right. This yields ascending values only when the tree satisfies the binary-search-tree ordering rule.
- **Pre-order / 前序**: node, left, right. Useful when serializing a tree with enough structure to recover its shape.
- **Post-order / 后序**: left, right, node. Useful when computing or releasing children before their parent.

#### Kth smallest in a BST

This iterative in-order traversal uses O(h) stack space for tree height h. It assumes node values are non-null numbers and the tree obeys the BST ordering rule. It returns null when k is invalid or the tree has fewer than k nodes.

~~~javascript
function kthSmallest(root, k) {
  if (!Number.isInteger(k) || k <= 0) return null;
  const stack = [];
  let node = root;

  while (node || stack.length) {
    while (node) {
      stack.push(node);
      node = node.left;
    }
    node = stack.pop();
    if (--k === 0) return node.val;
    node = node.right;
  }
  return null;
}
~~~

---

### Trees and operation costs

| Structure | Indexed access / search | Insert or delete |
|---|---|---|
| Array | Index access O(1); value search O(n) | Middle insert/delete O(n) because elements move |
| Linked list | Finding by value or index O(n) | O(1) insertion at a known link; deletion needs the predecessor link (singly linked) or target node (doubly linked), otherwise O(n) worst case |
| Height-balanced BST | Search O(log n) | O(log n) |
| Unbalanced BST | Worst-case search O(n) | Worst-case O(n) |

A balanced search tree gives logarithmic operations by keeping height logarithmic. If insertions produce a chain, those operations degrade to linear time. Array access remains fast by index, while inserting into the middle shifts later elements.

These bounds do not capture cache locality or dependency chains. See [Memory Hierarchy and Data Locality / 内存层次与数据局部性](#40.%20Why%20are%20contiguous%20scans%20often%20faster%20than%20linked-list%20walks?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F) for why contiguous scans can outperform pointer-based traversal and when a known-node list update is actually O(1).

---

### Self-balancing trees

#### Red-Black Tree

A red-black tree is a binary search tree with coloring invariants that bound its height. Red nodes have black children, and every path from a node to a descendant leaf has the same black height; implementations also treat the root and leaf sentinels as black. These rules give O(log n) worst-case search, insertion, and deletion.

Java's `TreeMap` explicitly documents a red-black-tree implementation. C++ `std::map` specifies ordered associative behavior and logarithmic lookup, insertion, and key-removal bounds, but its standard does not prescribe a tree shape. Check the language and library documentation before inferring a product's internal structure: [Java `TreeMap`](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/TreeMap.html) and [C++ associative containers](https://eel.is/c++draft/associative.reqmts).

#### B-Tree and B+ Tree

B-trees are multi-way search trees designed to reduce storage-page reads by keeping several keys in each node.

- In a B-tree, records or record references may be stored in internal nodes as well as leaves.
- In a B+ tree, internal nodes guide the search and records are stored at leaves; leaf links commonly support ordered range scans.

These are family descriptions, not a guarantee that every database index uses the same variant or layout. Check the database's manual for its index type and behavior.

---

### Trie (prefix tree)

A trie shares prefixes between keys. Lookup takes O(m) steps for a key of length m when each next edge can be selected in constant expected time; the cost depends on the node's child representation. Tries can use substantial memory when keys share few prefixes.

Use one when prefix traversal or prefix queries are central, such as autocomplete or routing tables; a hash map may be simpler for exact-key lookup.

---

### DOM tree traversal

A DOM tree is a hierarchy of Node objects. Pass an explicit visit callback and a node or null root. Snapshot each node's children before walking so the traversal has a clear view if callbacks mutate the DOM.

#### DFS — depth-first search

~~~javascript
function dfs(root, visit) {
  if (!root) return;
  visit(root);
  for (const child of Array.from(root.childNodes)) {
    dfs(child, visit);
  }
}

function dfsIterative(root, visit) {
  if (!root) return;
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    visit(node);
    const children = Array.from(node.childNodes);
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push(children[i]);
    }
  }
}
~~~

#### BFS — breadth-first search

~~~javascript
function bfs(root, visit) {
  if (!root) return;
  const queue = [root];
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head];
    visit(node);
    for (const child of Array.from(node.childNodes)) {
      queue.push(child);
    }
  }
}
~~~

A queue implemented with repeated `Array.prototype.shift` can move all remaining elements on each removal and make a traversal quadratic. Advancing a head index keeps this traversal O(n) in the number of visited nodes, with O(n) queue space.

DFS is useful when depth-first order or a path is needed. BFS is useful for level order and shortest paths in an unweighted graph; a DOM tree has one unique path from the root to each node.

---

### Array ↔ Tree conversion

Flat rows with parent identifiers can be transformed into a hierarchy for a tree UI or converted back for an API or database representation. This example expects unique IDs, one root whose parent ID is 0, and each other row to reference an existing parent.

#### Array to tree

~~~javascript
function arrayToTree(rows) {
  if (!Array.isArray(rows)) throw new TypeError('rows must be an array');

  const nodes = new Map();
  for (const row of rows) {
    if (!row || nodes.has(row.id)) throw new RangeError('rows must have unique IDs');
    nodes.set(row.id, { ...row, children: [] });
  }

  const roots = [];
  for (const row of rows) {
    const node = nodes.get(row.id);
    if (row.parentId === 0) {
      roots.push(node);
      continue;
    }
    const parent = nodes.get(row.parentId);
    if (!parent) throw new RangeError('parent ID does not exist');
    parent.children.push(node);
  }

  if (roots.length !== 1) throw new RangeError('expected exactly one root');
  const root = roots[0];

  const seen = new Set();
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    if (seen.has(node)) throw new RangeError('rows contain a cycle');
    seen.add(node);
    for (const child of node.children) stack.push(child);
  }
  if (seen.size !== nodes.size) throw new RangeError('rows contain a disconnected cycle');
  return root;
}
~~~

The two passes take O(n) expected time and O(n) space with a map. Reserve ID 0 for the root marker, or change the marker to match the data format.

#### Tree to array

~~~javascript
function treeToArray(root) {
  if (!root) return [];
  const rows = [];
  const stack = [{ node: root, parentId: 0 }];
  while (stack.length) {
    const { node, parentId } = stack.pop();
    rows.push({ id: node.id, parentId, name: node.name });
    const children = node.children ?? [];
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push({ node: children[i], parentId: node.id });
    }
  }
  return rows;
}
~~~

This conversion expects an acyclic tree with a single root. Preserve application-specific fields deliberately; this example emits only `id`, `parentId`, and `name`.

### Linked structure in React Fiber

React represents its work tree with Fiber nodes linked through fields such as `child`, `sibling`, and `return`. The nodes still form a tree; sibling pointers encode the ordered children. This structure lets the reconciler keep work units and progress between scheduling steps.

**Concurrent rendering is conditional.** React can pause or restart render work for updates using concurrent features such as transitions. An update rendered without such features can remain synchronous. React applies DOM mutations during commit after rendering work is ready, so do not describe every render or commit as freely interruptible. Fiber is an implementation detail; use React's public APIs rather than depending on its internal node layout.

See [React 18](https://react.dev/blog/2022/03/29/react-v18) for concurrent rendering behavior and [React's Fiber types](https://github.com/facebook/react/blob/main/packages/react-reconciler/src/ReactInternalTypes.js) for the illustrative implementation.

**See also:** [Algorithms and Complexity](#32.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F) for searches and dynamic programming, and [Practical Data Structure Implementations](#35.%20How%20can%20an%20LRU%20cache%20find%20an%20entry%20and%20update%20recency%20efficiently?%20/%20LRU%20%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E9%AB%98%E6%95%88%E6%89%BE%E5%88%B0%E6%9D%A1%E7%9B%AE%E5%B9%B6%E6%9B%B4%E6%96%B0%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F) for LRU caches and [queues and stacks](#34.%20How%20do%20FIFO%20and%20LIFO%20change%20the%20representation%20of%20pending%20work?%20/%20FIFO%20%E4%B8%8E%20LIFO%20%E6%80%8E%E6%A0%B7%E5%BD%B1%E5%93%8D%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%E7%9A%84%E8%A1%A8%E7%A4%BA%EF%BC%9F) for removal-order implementations.
## 34. How do FIFO and LIFO change the representation of pending work? / FIFO 与 LIFO 怎样影响待处理工作的表示？

Choose the removal order first. A stack removes the newest item and maps directly to an array end. A queue removes the oldest and needs a way to advance the front without moving every remaining element on each removal. / 先定取出顺序。栈取最新项，可以直接使用数组末尾。队列取最旧项，需要移动逻辑队首，而非每次搬动其余元素。

### Queue (FIFO)

**队列 / Queue** processes values in first-in, first-out order. This linked-list version throws on an empty read so every value, including `null` and `undefined`, remains distinguishable from the empty state.

~~~javascript
class Queue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }

  get isEmpty() {
    return this.length === 0;
  }

  enqueue(value) {
    const node = { value, next: null };
    if (this.tail) this.tail.next = node;
    else this.head = node;
    this.tail = node;
    this.length++;
  }

  dequeue() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    const value = this.head.value;
    this.head = this.head.next;
    if (!this.head) this.tail = null;
    this.length--;
    return value;
  }

  peek() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    return this.head.value;
  }
}
~~~

Enqueue, dequeue, and peek take O(1) time. Array `shift` removes the first element but may move the remaining indexed elements, so a linked queue or a head index is preferable for a queue that grows large. Breadth-first traversal with a head index appears in [Core Data Structures](#33.%20Which%20data%20structure%20fits%20the%20access%20pattern,%20and%20when%20do%20its%20cost%20bounds%20hold?%20/%20%E5%93%AA%E7%A7%8D%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E9%80%82%E5%90%88%E5%BD%93%E5%89%8D%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F).

---

### Stack (LIFO)

**栈 / Stack** processes values in last-in, first-out order. An array provides a compact stack; this version also throws on empty `pop` or `peek` so stored `undefined` is not confused with an empty stack.

~~~javascript
class Stack {
  constructor() {
    this.items = [];
  }

  get isEmpty() {
    return this.items.length === 0;
  }

  push(value) {
    this.items.push(value);
  }

  pop() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items.pop();
  }

  peek() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items[this.items.length - 1];
  }
}
~~~

Array `push` and `pop` are the natural stack operations. Their exact growth costs are runtime implementation details; a dynamic array may occasionally resize.

[Back to the main question / 返回主问题](#35.%20How%20can%20an%20LRU%20cache%20find%20an%20entry%20and%20update%20recency%20efficiently?%20/%20LRU%20%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E9%AB%98%E6%95%88%E6%89%BE%E5%88%B0%E6%9D%A1%E7%9B%AE%E5%B9%B6%E6%9B%B4%E6%96%B0%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F).
## 35. How can an LRU cache find an entry and update recency efficiently? / LRU 缓存怎样高效找到条目并更新使用顺序？

An LRU cache has two jobs: find an entry by key and identify the least recently used entry to evict. An insertion-ordered map can provide both if each hit moves the key to the end. A separate map and doubly linked list make the same two responsibilities explicit. / LRU 缓存有两项工作：按键查找，以及找出最久未使用的条目进行淘汰。有插入顺序的映射在每次命中时把键移到末尾，就能承担这两项工作。映射加双向链表则显式分开这两个职责。

**Key terms / 关键术语** · recency / 使用新近程度 · eviction / 淘汰 · ordered map / 有序映射

### LRU Cache

**最近最少使用缓存 / Least Recently Used cache** evicts the least recently accessed entry when full.

#### Using `Map`

`Map` preserves insertion order. Deleting and reinserting a hit moves it to the newest position. This API supports arbitrary keys and values; use `has` to distinguish a stored `undefined` from a missing key. A zero-capacity cache remains empty.

~~~javascript
class LRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.cache = new Map();
  }

  has(key) {
    return this.cache.has(key);
  }

  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }

  put(key, value) {
    if (this.capacity === 0) return;
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size === this.capacity) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
~~~

Map operations are commonly treated as expected constant-time in application analysis, but the ECMAScript specification requires average access to be sublinear rather than promising a precise O(1) bound. This version is concise and avoids maintaining a second ordering structure.

#### Doubly linked list plus map

A linked list makes moving an existing entry to the front and evicting the tail a pointer update. The map locates each node. Both structures are needed to keep the operations efficient; using an ordinary object for arbitrary cache keys can collide with inherited property names.

~~~javascript
class ListNode {
  constructor(key, value) {
    this.key = key;
    this.value = value;
    this.prev = null;
    this.next = null;
  }
}

class LinkedLRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.nodes = new Map();
    this.head = new ListNode(null, null);
    this.tail = new ListNode(null, null);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  has(key) {
    return this.nodes.has(key);
  }

  get(key) {
    const node = this.nodes.get(key);
    if (!node) return undefined;
    this._remove(node);
    this._addToFront(node);
    return node.value;
  }

  put(key, value) {
    if (this.capacity === 0) return;
    const existing = this.nodes.get(key);
    if (existing) {
      existing.value = value;
      this._remove(existing);
      this._addToFront(existing);
      return;
    }

    if (this.nodes.size === this.capacity) {
      const oldest = this.tail.prev;
      this._remove(oldest);
      this.nodes.delete(oldest.key);
    }
    const node = new ListNode(key, value);
    this.nodes.set(key, node);
    this._addToFront(node);
  }

  _addToFront(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
  }

  _remove(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }
}
~~~

With a map that provides expected constant-time lookup, the linked-list version has expected O(1) get and put operations. Use the simpler map-based version when the linked-list mechanics are not part of the requirement.

Compare [FIFO and LIFO representations / 队列和栈的表示](#34.%20How%20do%20FIFO%20and%20LIFO%20change%20the%20representation%20of%20pending%20work?%20/%20FIFO%20%E4%B8%8E%20LIFO%20%E6%80%8E%E6%A0%B7%E5%BD%B1%E5%93%8D%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%E7%9A%84%E8%A1%A8%E7%A4%BA%EF%BC%9F) when work is removed in arrival or nesting order. [ECMAScript Map](https://tc39.es/ecma262/2020/#sec-map-objects) specifies observable key iteration order.
## 36. How do ordered inputs enable binary search and two pointers? / 有序输入怎样支持二分查找和双指针？

Use ordering to prove which candidates can be discarded. Binary search shrinks a range around a monotone decision. Two pointers use relationships between positions to rule out a whole set of pairs at each move. / 用有序性证明哪些候选可以排除。二分按单调判断缩小范围，双指针利用位置之间的关系，每次移动时排除一组组合。

### Binary search

Binary search locates a matching item in O(log n) time when the input is sorted in ascending order and comparisons are consistent. This version returns any matching index, or -1 for an empty array or a missing value.

~~~javascript
function binarySearch(values, target) {
  let left = 0;
  let right = values.length - 1;
  while (left <= right) {
    const middle = left + Math.floor((right - left) / 2);
    if (values[middle] === target) return middle;
    if (values[middle] < target) left = middle + 1;
    else right = middle - 1;
  }
  return -1;
}
~~~

For fixed-width integer languages, computing the midpoint as left + (right - left) / 2 avoids overflow in left + right. JavaScript array indices are far smaller than Number's exact-integer limit, but the difference form states the safer general pattern.

---

### Two pointers

**双指针 / Two pointers** uses two positions to reduce repeated scans when the input structure provides an ordering or movement invariant. It is not a general replacement for nested loops; the invariant must justify discarding part of the search space.

#### Two Sum on a sorted array

Returns a pair of indices or null when no pair exists. Equal values at different positions are valid.

~~~javascript
function twoSumSorted(values, target) {
  let left = 0;
  let right = values.length - 1;
  while (left < right) {
    const sum = values[left] + values[right];
    if (sum === target) return [left, right];
    if (sum < target) left++;
    else right--;
  }
  return null;
}
~~~

#### Move zeros to the end

Moves numeric zeroes in place while keeping the order of non-zero values. It returns the same mutated array.

~~~javascript
function moveZeros(values) {
  let next = 0;
  for (let i = 0; i < values.length; i++) {
    if (values[i] !== 0) {
      [values[next], values[i]] = [values[i], values[next]];
      next++;
    }
  }
  return values;
}
~~~

---

[Back to the main question / 返回主问题](#32.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F).
## 37. How do you choose a dynamic programming state and update order? / 动态规划怎样选择状态和更新顺序？

Define a state with all the information its transitions need, establish base cases, then compute prerequisites before dependent states. When an update reuses the same storage, its order determines which version a transition reads. / 状态要包含转移所需的信息，先确定初始条件，再按依赖顺序计算。复用同一份存储时，更新顺序决定转移读到哪个版本。

### Dynamic programming

**动态规划 / Dynamic programming** stores results for overlapping subproblems. Top-down memoization follows the recursive definition; bottom-up iteration computes states in dependency order and can often retain only the state still needed.

#### Fibonacci

For non-negative integer n, naive recursion repeats subproblems and takes O(2^n) time with O(n) call-stack space. The iterative form takes O(n) time and O(1) auxiliary space. These examples use Number; use BigInt when exact results beyond Number's safe-integer range are needed.

~~~javascript
function fibRecursive(n) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (n <= 1) return n;
  return fibRecursive(n - 1) + fibRecursive(n - 2);
}

function fib(n) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (n <= 1) return n;
  let previous = 0;
  let current = 1;
  for (let i = 2; i <= n; i++) {
    [previous, current] = [current, previous + current];
  }
  return current;
}
~~~

#### Climbing stairs (frog jump)

Count ordered sequences of allowed positive step sizes that sum to n. The empty sequence is one way to reach step 0. Require distinct positive integer steps; repeated entries would count the same step size more than once.

~~~javascript
function climbStairs(n, steps) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (!Array.isArray(steps) || steps.some(step => !Number.isInteger(step) || step <= 0)) {
    throw new TypeError('steps must contain positive integers');
  }
  if (new Set(steps).size !== steps.length) throw new RangeError('steps must be distinct');

  const ways = new Array(n + 1).fill(0);
  ways[0] = 1;
  for (let total = 1; total <= n; total++) {
    for (const step of steps) {
      if (total >= step) ways[total] += ways[total - step];
    }
  }
  return ways[n];
}
~~~

This counts order as meaningful: with steps [1, 2], reaching 3 has three sequences: 1+1+1, 1+2, and 2+1. Time is O(nk), where k is the number of allowed steps; space is O(n).

#### 0/1 Knapsack

Choose each item at most once to maximize value within a weight capacity. Iterate capacities downward so the current item cannot be selected again during the same pass.

~~~javascript
function knapsack(capacity, weights, values) {
  if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
  if (!Array.isArray(weights) || !Array.isArray(values) || weights.length !== values.length) {
    throw new TypeError('weights and values must be arrays of equal length');
  }
  if (weights.some(weight => !Number.isInteger(weight) || weight < 0)) {
    throw new RangeError('weights must be non-negative integers');
  }

  const best = new Array(capacity + 1).fill(0);
  for (let i = 0; i < weights.length; i++) {
    for (let remaining = capacity; remaining >= weights[i]; remaining--) {
      best[remaining] = Math.max(best[remaining], best[remaining - weights[i]] + values[i]);
    }
  }
  return best[capacity];
}
~~~

Time is O(nW) and space O(W), for n items and integer capacity W. The zero-filled state means the result may leave capacity unused; it assumes there is no required minimum value or exact-fill constraint.

---

[Back to the main question / 返回主问题](#32.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F).
## 38. Why do partition choices change quicksort costs? / 分区选择为什么会改变快速排序的代价？

Each partition groups values around a pivot. Balanced partitions keep the recursion shallow, while repeatedly skewed partitions make later calls process nearly the original input size. The representation also determines whether the algorithm copies data. / 分区按基准值分组。较均衡的分区使递归较浅，持续偏斜则让后续调用仍要处理接近原规模的数据。表示方式还会决定是否复制数据。

### Sorting

#### Quicksort

This array-building version is easy to inspect, but it is not in-place. With balanced partitions it takes O(n log n) time; an adversarial sequence of pivots can take O(n²) time and O(n) recursive stack space.

~~~javascript
function quickSort(values) {
  if (values.length <= 1) return values;
  const pivot = values[Math.floor(values.length / 2)];
  const lower = [];
  const equal = [];
  const higher = [];
  for (const value of values) {
    if (value < pivot) lower.push(value);
    else if (value > pivot) higher.push(value);
    else equal.push(value);
  }
  return [...quickSort(lower), ...equal, ...quickSort(higher)];
}
~~~

For application code, prefer the built-in sort with an explicit comparator for numeric data: `values.sort((a, b) => a - b)` mutates the array, while `values.toSorted((a, b) => a - b)` returns a sorted copy where supported. Without a comparator, array elements are compared as strings. ECMAScript requires stable sorting; the engine's specific sorting algorithm is an implementation detail. See [ECMAScript 2020, Array.prototype.sort](https://tc39.es/ecma262/2020/#sec-array.prototype.sort).

---

[Back to the main question / 返回主问题](#32.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F).
## 39. Which units should a text algorithm count and compare? / 文本算法应按什么单位计数和比较？

Choose the unit from the behavior you need. Code units support storage indexing, code points represent Unicode values, and grapheme clusters better match many user-perceived characters. Formatting, comparison, and counting should use the same explicit assumptions. / 按任务选择单位。编码单元适合存储索引，码点表示 Unicode 值，字素簇更接近许多用户感知的字符。格式化、比较和计数都应明确所用假设。

### String algorithms

The examples iterate Unicode code points with `Array.from`; that keeps surrogate pairs together. A user-perceived character can contain multiple code points, so grapheme-aware text operations need segmentation and may also need normalization.

#### Palindrome check

~~~javascript
function isPalindrome(value) {
  const characters = Array.from(String(value));
  for (let left = 0, right = characters.length - 1; left < right; left++, right--) {
    if (characters[left] !== characters[right]) return false;
  }
  return true;
}
~~~

#### Longest consecutive character

Returns the first longest run. Empty input returns an empty character and length zero.

~~~javascript
function longestConsecutive(value) {
  const characters = Array.from(value);
  if (characters.length === 0) return { char: '', len: 0 };

  let bestChar = characters[0];
  let bestLength = 1;
  let currentLength = 1;
  for (let i = 1; i <= characters.length; i++) {
    if (i < characters.length && characters[i] === characters[i - 1]) {
      currentLength++;
    } else {
      if (currentLength > bestLength) {
        bestLength = currentLength;
        bestChar = characters[i - 1];
      }
      currentLength = 1;
    }
  }
  return { char: bestChar, len: bestLength };
}
~~~

#### Number formatting (thousand separators)

For display, use locale-aware formatting and specify a locale when output must be stable across machines. The manual version below accepts only strings containing an optional minus sign and decimal digits; use locale-aware formatting for numeric values and localized output.

~~~javascript
function formatNumber(value, locale = 'en-US') {
  return new Intl.NumberFormat(locale).format(value);
}

function formatIntegerThousands(text) {
  if (typeof text !== 'string' || !/^-?\d+$/.test(text)) throw new TypeError('expected an integer string');
  const sign = text.startsWith('-') ? '-' : '';
  const digits = sign ? text.slice(1) : text;
  return sign + digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
~~~

#### Switch ASCII letter case

This example changes only the English ASCII letters A-Z and a-z; other code points are preserved.

~~~javascript
function switchAsciiCase(value) {
  return Array.from(value, character => {
    const code = character.codePointAt(0);
    if (code >= 65 && code <= 90) return String.fromCodePoint(code + 32);
    if (code >= 97 && code <= 122) return String.fromCodePoint(code - 32);
    return character;
  }).join('');
}
~~~

---

[Back to the main question / 返回主问题](#32.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F).
## 40. Why are contiguous scans often faster than linked-list walks? / 为什么连续扫描往往比链表遍历快？

Big-O describes how work grows, but data layout and dependency determine how quickly a processor can obtain that work. A contiguous scan often runs efficiently because its addresses are predictable and independent loads can overlap; a linked-list walk has a dependent pointer chain, but a cache miss does not automatically stop every part of the CPU.

复杂度描述工作量如何随输入增长，数据布局与依赖关系则影响处理器能多快拿到数据。连续扫描通常更容易利用预取、并行访存和 SIMD；链表遍历受逐节点地址依赖限制，但一次 Cache Miss 不等于整个 CPU 必然停摆。

~~~mermaid
flowchart LR
    A[Array element i] -->|known address| A2[Adjacent element i+1]
    A2 -->|regular access can prefetch and overlap| A3[Next independent load]
    L[Current list node] -->|load next pointer| P[Wait for pointer value]
    P -->|only then know address| L2[Next list node]
    L -->|cache miss| Other[Independent CPU work may still continue]
~~~

### Key terms / 核心术语

| Term | Meaning |
|---|---|
| **Memory wall / 内存墙** | 处理器计算能力与内存供数能力之间逐渐拉大的差距，涉及延迟与带宽；它不是固定耗时，也不表示所有程序都受内存限制。 |
| **Latency / 延迟** | 从发出一次内存请求到数据可供使用所需的时间。 |
| **Bandwidth / 带宽** | 多个请求充分重叠时，单位时间能传输的数据量。 |
| **Cache line / 缓存行** | 缓存常用的数据传输与一致性维护粒度；具体大小依处理器而定。 |
| **Spatial locality / 空间局部性** | 访问靠近刚访问过地址的数据。一次缓存填充可能带入扫描很快会用到的相邻值。 |
| **Temporal locality / 时间局部性** | 短时间内重复使用同一数据，使它更可能仍留在缓存中。 |
| **Memory-level parallelism (MLP) / 内存级并行度** | 同时处于未完成状态的独立内存请求数量。 |

Wulf 与 McKee 用“内存墙”描述处理器与内存性能差距的扩大。Intel 优化手册提出的实践方向是让访问尽量命中缓存，或隐藏足够多的延迟以利用内存带宽。两者相关但不同：**延迟**限制一条有依赖的访问链；**带宽**限制整体数据吞吐。 [Wulf 与 McKee（1995）](https://doi.org/10.1145/216585.216588)，[Intel® 64 和 IA-32 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html)。

若一次流式循环平均为每项从内存传输 `s` 字节，可分配给它的有效带宽为 `B`，且循环已受带宽限制，则吞吐上限约为 `B / s` 项每秒。指针依赖链受另一种约束：当前节点到达后才能得知下一地址，因此单条遍历通常无法暴露同等数量的独立请求。这些关系用于识别瓶颈，不是精确耗时公式；缓存命中、计算量、其他请求和具体处理器都会改变结果。

### Why contiguous scans often work well / 连续扫描为什么常常高效

对连续数组区域，下一元素地址可由基址和下标计算。硬件预取器能识别许多规则访问模式；早先的读取尚未完成时，处理器也可能继续发出后续迭代中彼此独立的读取。如果操作、数据类型和编译条件合适，编译器还可用 SIMD 指令并行处理多个值。这些收益都有条件：步长不规则、分支多、指针别名难以排除、指令级并行度不足，或内存带宽已饱和时，预取和向量化都可能帮助有限。[Intel 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html)、[Arm Cortex-A 系列程序员指南](https://documentation-service.arm.com/static/6893ad23e7f7ce6150e88d37)。

链表遍历要先读取当前节点，再从中得到下一节点地址（`node = node->next`）。在当前节点的链接到达之前，处理器通常不知道下一请求发往哪里。这种**指针追逐 / pointer chasing**形成依赖链，常限制单条遍历可利用的 MLP。普通流式预取器较难从中识别规律；特定设计也可能使用软件预取或专用硬件改善访问。

Cache Miss 仍可与独立工作重叠：支持乱序执行的核心可能先执行无关指令，其他独立读取或线程也可能已有请求在途。当缺失数据位于关键依赖路径上，且没有有用的独立工作可继续时，核心才会因等待而停顿。因此，长串依赖未命中会让链表遍历很慢，但不能推断每次 Miss 都冻结全部执行。Linux 官方文档也提醒，链表局部性较差；若简单数组已能满足需求，链表很少是更好的选择。[Linux：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html)。

### Complexity is not elapsed time / 复杂度不等于实际耗时

链表插入或删除只有在**已知相关节点或链接**时才是 O(1)。双向链表持有目标节点即可改动有限个指针；单向链表删除目标节点需要前驱，按位置插到某节点之前也需要前驱（除非表示方式另行提供）。按值或下标查找仍是 O(n)。创建节点还会经过分配器并产生内存流量，而复杂度表通常没有计入这些分配与缓存成本。

数组中间插入需要 O(n) 次元素移动，但移动范围连续规则；对适合的类型还可用优化过的批量操作。它是否快于分配链表节点并改写链接，取决于元素大小、移动成本、是否已知链表位置、分配器、数据是否在缓存中以及操作比例。因此，“链表 O(1) 插入总比数组 O(n) 插入快”不能作为普遍结论。

对象池可降低分配开销，也可能让对象更集中，但它不保证链接顺序与内存地址顺序一致。对象复用、插入顺序和池的设计共同决定实际遍历布局。

### Arrays in C, C++, and JavaScript / 各语言中的数组布局

在 C 中，普通数组的元素连续存储，多维数组按行优先布局（最后一维变化最快）；C++ `std::vector<T>`（专门化的 `vector<bool>` 除外）也保证连续存储。JavaScript `Array` 则由带特殊 `length` 行为的索引属性定义；语言规范不保证它采用同样的 C 式元素布局。引擎可以优化常见的稠密数组，具体表示因实现而异。以 V8 为例，它区分 packed 与 holey 等元素类型。[WG14 C23 草案](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3047.pdf)

JavaScript `TypedArray` 更接近数值数据布局：它以固定元素类型，在二进制数据缓冲区上提供数组式视图。但它仍由运行时管理；不能从 C 数组推断普通 JavaScript `Array` 的机器布局或优化方式。[C++ 草案：`vector`](https://eel.is/c++draft/vector)、[ECMAScript 2024：Indexed Collections](https://tc39.es/ecma262/2024/multipage/indexed-collections.html)、[V8：Elements kinds](https://v8.dev/blog/elements-kinds)。

An intrusive list can remove a separately allocated wrapper. Object placement and dependent loads still determine traversal cost. The Linux example explains [why the kernel embeds its list nodes / Linux 内核为何嵌入链表节点](#41.%20Why%20does%20the%20Linux%20kernel%20embed%20list%20nodes%20in%20their%20objects?%20/%20Linux%20%E5%86%85%E6%A0%B8%E4%B8%BA%E4%BB%80%E4%B9%88%E6%8A%8A%E9%93%BE%E8%A1%A8%E8%8A%82%E7%82%B9%E5%B5%8C%E5%85%A5%E5%AF%B9%E8%B1%A1%EF%BC%9F).

### Related performance surprises / 相关的性能反直觉现象

| 场景 | 机制与适用条件；可继续追问 |
|---|---|
| 小规模线性查找与二分 | 小型连续范围可简单顺序扫描；二分比较次数渐进更少，却跳跃访问不同位置。交叉点取决于数据规模、比较成本与缓存状态。实际输入规模和键分布是什么？ |
| 行遍历与列遍历 | 行优先布局中，遍历末维是连续访问；按列走会跨距访问。规则取决于语言及实际布局。循环顺序是否符合存储顺序？ |
| 伪共享 / False sharing | 不同 CPU 写同一一致性缓存行中的不同变量，也会让对方缓存副本失效。需要并发共享且至少一方写入；只有读取不构成此问题。能否用 `perf c2c` 找出争用缓存行？[Linux 伪共享指南](https://docs.kernel.org/kernel-hacking/false-sharing.html) |
| B+ 树与红黑树 | 面向页的 B+ 树在每页容纳多个分隔键，并通过叶页链接支持范围扫描；指针式红黑树通常每节点组织一个键。取舍取决于主要成本是存储页读取、内存缓存未命中还是更新。哪层存储与查询模式主导？[PostgreSQL B-tree 实现](https://www.postgresql.org/docs/current/btree.html) |
| 无分支与分支预测代码 | 去掉分支可能避开误预测，但也可能执行更多工作或引入数据依赖；预测稳定的分支反而更便宜。实际输入分布和生成指令是什么？ |
| 扁平与节点式哈希表 | 扁平表可把元数据与条目密集组织以便分组探测；节点式表更容易保持元素地址稳定，但常增加指针追逐。删除、扩容、负载因子和引用稳定性都重要。[Abseil Swiss Tables 设计](https://abseil.io/about/design/swisstables) |
| 结构体填充 | 对齐要求会插入填充字节并增大对象；字段顺序也可能影响空间，仍受 ABI 与访问模式约束。`sizeof` 与成员偏移是否显示出实际空间问题？ |
| 增加核心数 | 独立工作可扩展，直到共享内存带宽、一致性流量或同步争用成为瓶颈。增加核心后，负载是计算受限、带宽受限还是争用受限？[Intel 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html)、[Linux 伪共享指南](https://docs.kernel.org/kernel-hacking/false-sharing.html) |

**Related notes / 相关笔记：** [Core Data Structures](#33.%20Which%20data%20structure%20fits%20the%20access%20pattern,%20and%20when%20do%20its%20cost%20bounds%20hold?%20/%20%E5%93%AA%E7%A7%8D%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E9%80%82%E5%90%88%E5%BD%93%E5%89%8D%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F) explains tree structure and list-operation bounds; [Practical Data Structure Implementations](#35.%20How%20can%20an%20LRU%20cache%20find%20an%20entry%20and%20update%20recency%20efficiently?%20/%20LRU%20%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E9%AB%98%E6%95%88%E6%89%BE%E5%88%B0%E6%9D%A1%E7%9B%AE%E5%B9%B6%E6%9B%B4%E6%96%B0%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F) shows an LRU cache locating a list node through a map before moving that known node.

### Sources / 来源

来源核实日期：**2026-10-16**。处理器手册描述特定架构与实现，不代表所有 CPU 都有相同缓存层次、预取行为、缓存行大小或内存级并行度。

- [Wulf 与 McKee，“Hitting the Memory Wall: Implications of the Obvious”（1995）](https://doi.org/10.1145/216585.216588) — 内存墙术语的提出背景与论述。
- [Intel® 64 和 IA-32 架构优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html) — 隐藏延迟、内存带宽、规则预取模式及特定架构优化。
- [Arm Cortex-A 系列程序员指南，Armv7-A](https://documentation-service.arm.com/static/6893ad23e7f7ce6150e88d37) — 缓存延迟隐藏、hit-under-miss 与乱序执行示例；内容特定于处理器系列，不是所有 Arm 实现的保证。
- [Linux 内核：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html) 与 [`include/linux/list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h) — 循环双向结构、内嵌钩子、`container_of`、删除、安全遍历与并发说明。
- [Linux 内核：False Sharing](https://docs.kernel.org/kernel-hacking/false-sharing.html) — 一致性缓存行机制、成立条件与诊断方法。
- [C++ 草案：`vector`](https://eel.is/c++draft/vector) 和 [`list`](https://eel.is/c++draft/list) — 标准容器保证，以及哪些实现细节不能从标准推断。
- [WG14 C23 草案 N3047](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3047.pdf) — C 数组元素布局与多维数组行优先顺序。
- [GCC libstdc++ `stl_list.h`](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/stl_list.h) — 一个标准库实现中，链表节点将 `T` 存在自身节点内的对齐存储。
- [ECMAScript 2024：Indexed Collections](https://tc39.es/ecma262/2024/multipage/indexed-collections.html) 与 [V8：Elements kinds](https://v8.dev/blog/elements-kinds) — JavaScript Array 语义、TypedArray 数据缓冲视图，以及一种引擎的实现选择。
- [PostgreSQL：B-tree 索引](https://www.postgresql.org/docs/current/btree.html) 与 [Abseil：Swiss Tables](https://abseil.io/about/design/swisstables) — 页式树与密集哈希元数据的实际例子。
## 41. Why does the Linux kernel embed list nodes in their objects? / Linux 内核为什么把链表节点嵌入对象？

**Short answer / 简答** — An intrusive list embeds its link hook in the object, so generic operations manipulate the hook rather than a separately allocated wrapper. Linux's `struct list_head` stores `next` and `prev` links in a circular doubly linked list whose sentinel points to itself when empty. / **侵入式链表 / intrusive linked list** 把链接钩子直接嵌在被链接的对象里。Linux 的 `struct list_head` 保存 `next` 和 `prev`；通用链表操作直接修改这些钩子，不需要为每个成员关系另分配包装节点。Linux 实现是带哨兵的循环双向链表：空表的 `list_head` 指向自身。

### Recover the containing object / 还原外层对象

`container_of(ptr, type, member)` 可从内嵌钩子指针还原外层对象。概念上，它从钩子地址减去成员相对结构体起点的字节偏移 `offsetof(type, member)`。因此链表操作只需认识通用钩子，调用方再还原具体对象类型。[Linux：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html)、[Linux `list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h)。

Conceptually, `container_of` recovers the enclosing object by subtracting the hook member's `offsetof` byte offset from the hook's address. This makes the link operations generic, but the recovered objects can still form a dependent pointer chain.

### Link ownership and object lifetime / 链接归属与对象生命周期

```c
#include <linux/list.h>
#include <linux/mutex.h>

struct job {
    unsigned long id;
    struct list_head ready_link;
    struct list_head audit_link;
};

static LIST_HEAD(ready_jobs);
static DEFINE_MUTEX(ready_jobs_lock);

/* Initialize both hooks before first insertion. */
static void init_job_links(struct job *job)
{
    INIT_LIST_HEAD(&job->ready_link);
    INIT_LIST_HEAD(&job->audit_link);
}

/* Caller owns job and ensures it is not already on ready_jobs. */
static void enqueue_job(struct job *job)
{
    mutex_lock(&ready_jobs_lock);
    list_add_tail(&job->ready_link, &ready_jobs);
    mutex_unlock(&ready_jobs_lock);
}

/* This iteration uses the same lock as every writer. */
static void inspect_jobs(void)
{
    struct job *job;

    mutex_lock(&ready_jobs_lock);
    list_for_each_entry(job, &ready_jobs, ready_link) {
        /* Use job->id. */
    }
    mutex_unlock(&ready_jobs_lock);
}

/* job must currently be linked; unlinking does not free it. */
static void dequeue_job(struct job *job)
{
    mutex_lock(&ready_jobs_lock);
    list_del_init(&job->ready_link);
    mutex_unlock(&ready_jobs_lock);
}
```

这段是 Linux 内核风格代码，不是可直接用于普通用户态的可移植 C。示例假定处于允许休眠的上下文，且所有访问 `ready_jobs` 的读者和写者都遵循同一互斥锁。一个钩子同一时刻只能挂入一张链表；`ready_link` 和 `audit_link` 是两种独立关系。摘除 `ready_link` 不会释放 `job`；释放对象前还要摘除其他有效钩子，并确保没有引用者或读者继续使用它。Linux 的 `list_for_each_entry_safe` 会预存下一游标，支持遍历时删除当前项；这里的“safe”不提供并发保护。并发访问通常需要锁；读多写少时可使用遵循正确生命周期与宽限期协议的 RCU 链表接口。[Linux 链表文档：删除与并发](https://www.kernel.org/doc/html/latest/core-api/list.html)。

### When does embedding help? / 何时适合把节点嵌入对象？

当已有对象需保持地址稳定、参与一种或多种频繁变化的关系，且减少每种关系额外包装节点有价值时，侵入式链表很实用。它提供通用链接操作，并通过多个钩子表示多个独立关系。但它**不会**让对象在物理内存中连续，也不会消除节点之间的指针依赖，因此不能解决内存墙。

也不要把非侵入式链表一概说成“对象再包一层指针并分配两次”。例如，`std::list<T>` 的容器元素本身就是 `T`；libstdc++ 的 `_List_node<T>` 将 `T` 放在节点内的对齐存储中，不是另分配一个用户对象再套包装节点，也不需要多追一次 `T*`。C++ 标准约束行为和复杂度，并不规定精确节点布局。[C++ 草案：`list`](https://eel.is/c++draft/list)、[GCC libstdc++ `stl_list.h`](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/stl_list.h)。

Embedding changes ownership and allocation. For traversal cost, see [memory hierarchy and data locality / 内存层次与数据局部性](#40.%20Why%20are%20contiguous%20scans%20often%20faster%20than%20linked-list%20walks?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F).
## 42. How do design principles reduce the cost of change without adding needless abstraction? / 设计原则如何降低变化成本而不过度抽象？

Design principles help identify where a likely change would force unrelated code to change. Use a principle when it points to a concrete coupling cost and a boundary that reduces it; adding interfaces, classes, or extension points without a real source of variation merely moves complexity around. **设计原则用于判断一次可能的变化会不会迫使无关代码跟着修改。只有当原则指出了具体耦合成本，并能据此建立有价值的边界时才应用；没有真实变化点却增加接口、类或扩展点，只会把复杂度挪到别处。**

### What are the SOLID principles, and what does each mean?

**SOLID / 面向对象设计原则** is a mnemonic for five related guidelines:

- **S — Single Responsibility Principle / 单一职责原则**: keep a module cohesive around one responsibility or axis of change.
- **O — Open/Closed Principle / 开闭原则**: make a stable part of the design extensible at expected variation points, rather than editing that core for every new case.
- **L — Liskov Substitution Principle / 里氏替换原则**: a subtype must preserve the behavioral expectations clients rely on from its base type.
- **I — Interface Segregation Principle / 接口隔离原则**: clients should depend only on the operations they need.
- **D — Dependency Inversion Principle / 依赖倒置原则**: high-level policy should not depend directly on low-level details; both should depend on abstractions where that boundary pays for itself.

These guidelines can help isolate changes, but applying all of them mechanically can produce needless interfaces and indirection.

#### Single Responsibility Principle (SRP)

A module should group behavior that changes for the same reason. This is not a rule that every method or data field needs a separate class.

~~~javascript
class UserRepository {
  async findById(id) { /* persistence details */ }
}

class UserPage {
  render(user) { /* presentation */ }
}
~~~

Separating persistence from presentation can help when those concerns change independently. A small component that performs a request and renders a result may still be cohesive if the application has no independent reason to change those pieces.

#### Open/Closed Principle (OCP)

An extension point is useful when a kind of variation is known and likely; it is not practical to close a system against every future change.

~~~javascript
class ShippingCalculator {
  constructor(strategy) {
    this.strategy = strategy;
  }

  calculate(pkg) {
    return this.strategy.calculate(pkg);
  }
}

class ExpressShipping {
  calculate(pkg) { return pkg.weight * 10; }
}

class StandardShipping {
  calculate(pkg) { return pkg.weight * 5; }
}
~~~

A new shipping policy can be supplied without changing the calculator, while the selection and shared contract still need maintenance. See [Strategy in practice](#44.%20When%20does%20a%20design%20pattern%20make%20change%20easier%20to%20understand%20and%20maintain?%20/%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E8%83%BD%E8%AE%A9%E5%8F%98%E5%8C%96%E6%9B%B4%E6%98%93%E7%90%86%E8%A7%A3%E5%92%8C%E7%BB%B4%E6%8A%A4%EF%BC%9F).

#### Liskov Substitution Principle (LSP)

A subtype should preserve the behavioral contract clients expect. For example, if a base type promises that every value can fly, a penguin subtype that throws from `fly` breaks that contract. A narrower abstraction such as `Bird` for shared bird behavior and `FlyingBird` for birds that can fly may model the domain more accurately.

#### Interface Segregation Principle (ISP)

Clients should not be forced to depend on operations they never use. In TypeScript, this can mean separating unrelated capabilities into small interfaces and composing them where needed; there is no universal field-count threshold.

#### Dependency Inversion Principle (DIP)

High-level policy and low-level details depend on an abstraction when that boundary reduces coupling. Constructor injection is one way to supply an implementation; **dependency injection is a technique, not the definition of DIP**.

~~~javascript
class NotificationService {
  constructor(sender) {
    this.sender = sender;
  }

  notify(message) {
    this.sender.send(message);
  }
}

class EmailSender {
  send(message) { /* send email */ }
}

class SmsSender {
  send(message) { /* send SMS */ }
}

const notifications = new NotificationService(new EmailSender());
~~~

The service can use another implementation or a test double through the same contract. Add an abstraction when the variation or test boundary is real.

---

### What are DRY, KISS, and YAGNI?

**DRY, KISS, and YAGNI / 不重复、保持简单、暂不实现未需功能** are practical heuristics. They help manage complexity but should not be interpreted as absolute prohibitions.

#### DRY (Don't Repeat Yourself)

Avoid duplicating the same rule or knowledge in places that must stay synchronized. Similar-looking code can represent different concepts, though; extracting it into one abstraction may couple changes that should remain independent.

#### KISS (Keep It Simple)

Prefer the simplest design that satisfies current requirements. A simple implementation is easier to explain and change; complexity should have a concrete payoff.

#### YAGNI (You Aren't Gonna Need It)

Do not build speculative features before a need is established. Keep the option to add an extension point when a real use case appears, and avoid confusing “not yet needed” with “never needed.”

---

See [frontend architecture boundaries](#43.%20How%20can%20a%20frontend%20architecture%20divide%20presentation%20and%20behavior?%20/%20%E5%89%8D%E7%AB%AF%E6%9E%B6%E6%9E%84%E6%80%8E%E6%A0%B7%E5%88%92%E5%88%86%E5%91%88%E7%8E%B0%E4%B8%8E%E8%A1%8C%E4%B8%BA%E7%9A%84%E8%81%8C%E8%B4%A3%EF%BC%9F) for presentation and deployment ownership examples.

Sources: [Robert C. Martin, The Open-Closed Principle](https://objectmentor.com/resources/articles/ocp.pdf), [Principles and Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf), and [Liskov and Wing, A Behavioral Notion of Subtyping](https://doi.org/10.1145/197320.197383).
## 43. How can a frontend architecture divide presentation and behavior? / 前端架构怎样划分呈现与行为的职责？

Start by deciding who owns data, interaction, and the view. Components give the UI explicit inputs and outputs, and unidirectional data flow helps trace causes of state changes. Micro-frontends add a deployment and ownership boundary when teams need independent releases. / 先确定数据、交互和视图由谁负责。组件为界面定义明确的输入和输出，单向数据流有助于追溯状态变化的原因。团队需要独立发布时，微前端还会引入部署与所有权边界。

### What are common frontend architecture patterns?

These are common design shapes, not a required architecture. Choose based on product boundaries, change frequency, and team ownership.

#### Component-based architecture

A UI can be composed from reusable components with explicit inputs and outputs. State and side effects may live in a component, a hook, or a separate service depending on its lifecycle and reuse needs; they are not inherently owned by every component.

#### Unidirectional data flow

In the classic Flux model, actions pass through a dispatcher to stores, which notify views. Other state libraries use different contracts. The useful goal is to make state changes and their causes traceable; the particular library does not guarantee that by itself.

See [Advanced React](../../frontend/frameworks/advanced-react.md) for React-specific state and component patterns.

#### Micro-frontends

Micro-frontends divide a frontend into parts that can have separate ownership or release paths. Integration can use build-time composition, runtime module loading, iframes, or web components, each with different isolation and deployment properties.

Reach for this when independent teams or release schedules are a concrete requirement and the organization can support the shared navigation, styling, accessibility, observability, and runtime boundaries. For a smaller application, a modular single frontend usually has less coordination and deployment overhead.

**See also:** [Design Patterns in Practice](#44.%20When%20does%20a%20design%20pattern%20make%20change%20easier%20to%20understand%20and%20maintain?%20/%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E8%83%BD%E8%AE%A9%E5%8F%98%E5%8C%96%E6%9B%B4%E6%98%93%E7%90%86%E8%A7%A3%E5%92%8C%E7%BB%B4%E6%8A%A4%EF%BC%9F) for reusable patterns that can support these principles.

[Back to the main question / 返回主问题](#42.%20How%20do%20design%20principles%20reduce%20the%20cost%20of%20change%20without%20adding%20needless%20abstraction?%20/%20%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99%E5%A6%82%E4%BD%95%E9%99%8D%E4%BD%8E%E5%8F%98%E5%8C%96%E6%88%90%E6%9C%AC%E8%80%8C%E4%B8%8D%E8%BF%87%E5%BA%A6%E6%8A%BD%E8%B1%A1%EF%BC%9F).
## 44. When does a design pattern make change easier to understand and maintain? / 何时使用设计模式能让变化更易理解和维护？

A design pattern names a recurring choice about construction, variation, notification, or ownership. Use it when the named boundary makes an actual change easier to localize or explain; then account for the added indirection and lifetime rules. A pattern does not remove a need to define scope, contracts, or authorization. **设计模式概括对象创建、行为变化、通知或所有权中的常见选择。只有当它能把真实变化收拢到更清晰的边界时才使用，并同时考虑新增的间接层和生命周期规则。模式不会替代对作用范围、契约和授权边界的定义。**

### When do you use the Factory pattern?

**工厂 / Factory** centralizes object creation when construction rules or the concrete type should not be repeated at call sites. A simple factory function is useful in JavaScript, but it is not automatically the GoF Factory Method or Abstract Factory pattern.

~~~javascript
function createButton(type) {
  if (type === 'primary') return new PrimaryButton();
  if (type === 'secondary') return new SecondaryButton();
  return new DefaultButton();
}
~~~

Use this when the creation decision belongs in one place or construction has meaningful setup. If construction is already a single uncomplicated expression, a factory can add little value.

---

### When do you use the Singleton pattern?

**单例 / Singleton** constrains access to one instance within a chosen scope. A class-level static instance, for example, is one per loaded class in a JavaScript realm; it is not automatically one instance across workers, processes, duplicated module copies, or machines.

~~~javascript
class Store {
  static instance;

  static getInstance() {
    if (!Store.instance) Store.instance = new Store();
    return Store.instance;
  }
}
~~~

Repeated calls to `getInstance()` share one instance through that accessor; because `Store` has a public constructor, `new Store()` can still create additional instances.

A shared cache, event bus, or connection pool may need one instance per process or module. Consider whether explicit dependency injection or a scoped shared instance is easier to test and reason about. A singleton's global access can hide dependencies and couple tests.

---

### When do you use the Strategy pattern?

**策略 / Strategy** puts interchangeable behavior behind a common contract. It is useful when callers must choose among algorithms or policies; a small conditional is often clearer when there is only one simple branch.

~~~javascript
const strategies = new Map([
  ['express', pkg => pkg.weight * 10],
  ['standard', pkg => pkg.weight * 5],
  ['overnight', pkg => pkg.weight * 20],
]);

function calculateShipping(name, pkg) {
  const strategy = strategies.get(name);
  if (!strategy) throw new RangeError('unknown shipping strategy');
  return strategy(pkg);
}
~~~

Adding a strategy can avoid changing the dispatcher, but the strategy contract and selection rules still need to be maintained. This can support the Open/Closed Principle when the variation is real; it does not make a design closed to every future change. See [Software Design Principles](#42.%20How%20do%20design%20principles%20reduce%20the%20cost%20of%20change%20without%20adding%20needless%20abstraction?%20/%20%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99%E5%A6%82%E4%BD%95%E9%99%8D%E4%BD%8E%E5%8F%98%E5%8C%96%E6%88%90%E6%9C%AC%E8%80%8C%E4%B8%8D%E8%BF%87%E5%BA%A6%E6%8A%BD%E8%B1%A1%EF%BC%9F).

---

### What's the difference between Observer and Publish-Subscribe?

**观察者 / Observer** and **发布订阅 / Publish-Subscribe** both route notifications. In the common distinction, an observer subject knows its observers and notifies them directly; a publish-subscribe broker routes messages by topic, so publishers and subscribers need not know each other. Real libraries can combine these arrangements, so use the concrete API's contract rather than relying on the label.

#### Observer

~~~javascript
class Subject {
  constructor() {
    this.observers = new Set();
  }

  subscribe(observer) {
    this.observers.add(observer);
    return () => this.observers.delete(observer);
  }

  notify(data) {
    for (const observer of this.observers) observer.update(data);
  }
}
~~~

The subject owns the subscriptions. Returning an unsubscribe function makes the lifetime of a listener explicit.

#### Publish-Subscribe

~~~javascript
class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(topic, listener) {
    const subscribers = this.listeners.get(topic) ?? new Set();
    subscribers.add(listener);
    this.listeners.set(topic, subscribers);
    return () => subscribers.delete(listener);
  }

  emit(topic, data) {
    for (const listener of this.listeners.get(topic) ?? []) listener(data);
  }
}

const eventBus = new EventBus();
eventBus.on('user:login', user => { /* update the UI with user data */ });
eventBus.emit('user:login', { name: 'Alice' });
~~~

A broker can reduce direct coupling, but distributed or global event buses can make the flow harder to trace. DOM `EventTarget` is observer-like: listeners register on a target that dispatches events.

See [DOM Manipulation and Events](../../frontend/browser-apis/dom-manipulation-and-events.md) for browser event APIs.

---

See [how to model an editable component tree](#45.%20How%20should%20a%20low-code%20editor%20store%20editable%20structure%20and%20published%20output?%20/%20%E4%BD%8E%E4%BB%A3%E7%A0%81%E7%BC%96%E8%BE%91%E5%99%A8%E6%80%8E%E6%A0%B7%E4%BF%9D%E5%AD%98%E5%8F%AF%E7%BC%96%E8%BE%91%E7%BB%93%E6%9E%84%E4%B8%8E%E5%8F%91%E5%B8%83%E7%BB%93%E6%9E%9C%EF%BC%9F) for a system-design example and [how roles control feature access](#%E8%A7%92%E8%89%B2%E8%83%BD%E6%8E%88%E4%BA%88%E4%BB%80%E4%B9%88%E5%8A%A8%E4%BD%9C%EF%BC%8C%E8%B5%84%E6%BA%90%E6%A3%80%E6%9F%A5%E8%BF%98%E8%A6%81%E5%81%9A%E4%BB%80%E4%B9%88%EF%BC%9F) for a distinct authorization decision.
## 45. How should a low-code editor store editable structure and published output? / 低代码编辑器怎样保存可编辑结构与发布结果？

Keep an editable component tree with typed configuration and stable identity. Derive rendering and published output from that schema so editing, validation, and release can each use the representation appropriate to their lifecycle. / 维护带类型配置和稳定身份的可编辑组件树。渲染和发布结果从该结构派生，让编辑、校验和发布可以各自使用适合其生命周期的表示。

### Separate page content from the editing session / 分开页面内容与编辑会话

A page builder can model a document as a component tree, with each node carrying an ID, type, properties, style, and children. The editor can derive its canvas and side panels from that model, then serialize it for persistence.

~~~javascript
const component = {
  id: 'comp_001',
  type: 'Button',
  props: { text: 'Click me', variant: 'primary' },
  style: { position: 'absolute', top: 100, left: 200 },
  children: [],
};
~~~

Keep document order and visual stacking as explicit concepts. Child order can be one input to rendering, but CSS stacking contexts mean it is not universally equivalent to the final z-order; each stacking context is painted as a unit within its parent context ([CSS 2.2 visual formatting model](https://www.w3.org/TR/CSS22/zindex.html)).

Selection, hover, and panel state belong to the editing session. A selection change can update the inspector without editing the document, saving a draft, or adding an undo step.

~~~javascript
const editor = {
  document: { schemaVersion: 1, nodes: [component] },
  session: { selectedId: null },
};

function selectComponent(state, id) {
  return { ...state, session: { ...state.session, selectedId: id } };
}

const draftJson = JSON.stringify(selectComponent(editor, component.id).document);
~~~

- **Component registry / 组件注册表**: map a validated component type to its renderer and schema.
- **Layer order / 图层顺序**: define how siblings are ordered and translate that order into the chosen rendering model.
- **Undo and redo / 撤销与重做**: store inverse commands or immutable document snapshots; choose based on history size and operation complexity.
- **Collaboration / 协作**: a WebSocket transports updates, but does not resolve concurrent edits. A server-authoritative order, locks, operational transformation, or a CRDT may fit different conflict and offline requirements.

### Publish a validated revision / 发布已校验的修订

Validate a particular document revision against the registry and derive the public output from that revision. Keep the artifact or a versioned rendering recipe tied to its source revision so preview, release, and rollback can refer to the same content. Draft edits and session selections can then continue independently. [Design patterns and change boundaries / 设计模式与变化边界](#44.%20When%20does%20a%20design%20pattern%20make%20change%20easier%20to%20understand%20and%20maintain?%20/%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E8%83%BD%E8%AE%A9%E5%8F%98%E5%8C%96%E6%9B%B4%E6%98%93%E7%90%86%E8%A7%A3%E5%92%8C%E7%BB%B4%E6%8A%A4%EF%BC%9F)
## 46. How does Scrum help a team inspect and adapt work? / Scrum 如何帮助团队检查并调整工作？

**核心回答 / Core answer：** Agile names values and principles that favor collaboration, usable software, customer feedback, and adapting to change; Scrum is one framework that gives a team accountabilities, events, artifacts, and commitments to inspect progress and adjust its next steps. Product Goals, Sprint Goals, and the Definition of Done orient decisions, while a Sprint Backlog plan can change as the Developers learn. A Sprint Review examines outcomes and next adaptations; it is not a release gate. The framework creates opportunities for feedback but does not guarantee good delivery by itself. / 敏捷描述重视协作、可用软件、客户反馈和响应变化的价值与原则；Scrum 则用职责、事件、工件和承诺，帮助团队检查进展并调整下一步。产品目标、Sprint 目标和完成定义为决策提供方向，Developers 可随着学习调整 Sprint Backlog 计划。Sprint Review 检视成果并讨论后续调整，它不是发布审批关卡。框架提供反馈机会，但本身不能保证交付效果。

### Agile principles

The Agile Manifesto values:

- Individuals and interactions over processes and tools.
- Working software over comprehensive documentation.
- Customer collaboration over contract negotiation.
- Responding to change over following a plan.

The items on the right still have value; the Manifesto gives greater weight to the items on the left. Its principles also emphasize frequent delivery, sustainable pace, technical excellence, simplicity, and regular reflection. How a team applies these ideas depends on its product, people, and constraints.

### Scrum framework

Scrum uses empiricism and lean thinking to help a Scrum Team generate value through adaptive solutions. Its defined structure is not a promise that adopting the framework will automatically improve delivery.

#### Roles

The Scrum Guide describes three **accountabilities / 职责** within one Scrum Team; these are responsibilities, not a required set of job titles.

##### Product Owner

Accountable for maximizing product value and effective Product Backlog management. The Product Owner may delegate backlog work but remains accountable for the result.

##### Scrum Master

Accountable for establishing Scrum as defined in the Guide and for the Scrum Team's effectiveness. This includes coaching, helping remove impediments, and supporting the wider organization in its use of Scrum; it does not make the Scrum Master the team's line manager.

##### Developers

The people who create a usable Increment during each Sprint. They create and adapt the Sprint Backlog plan, uphold the Definition of Done, and hold one another accountable as professionals.

#### Events

The five events are the **Sprint**, **Sprint Planning**, **Daily Scrum**, **Sprint Review**, and **Sprint Retrospective**. The Sprint is the container for the other events and activities.

##### Sprint

A fixed-length event of one month or less. Teams choose a duration that supports inspection and adaptation; two weeks is common in some teams but is not prescribed by Scrum. The Sprint Goal provides a coherent objective while allowing the exact work to be clarified as learning occurs.

##### Sprint Planning

The Scrum Team plans why the Sprint is valuable, what can be done, and how the selected work will be completed. The output includes a Sprint Goal and the Developers' plan in the Sprint Backlog.

##### Daily Scrum

A 15-minute event for the Developers to inspect progress toward the Sprint Goal and adapt their plan. The Guide does not require each person to answer a fixed set of status questions. Developers choose a format that serves the purpose and may meet more often as needed.

##### Sprint Review

The Scrum Team and stakeholders inspect the Sprint's outcome and discuss adaptations. It is a working session to inform what to do next, not only a demonstration.

##### Sprint Retrospective

The Scrum Team inspects how the last Sprint went with regard to people, interactions, processes, tools, and the Definition of Done, then identifies useful improvements. It is one of the Scrum events and occurs within the Sprint cadence.

#### Artifacts

| Artifact / 工件 | Commitment / 承诺 | Purpose |
|---|---|---|
| Product Backlog / 产品待办列表 | Product Goal / 产品目标 | An ordered source of work for evolving the product |
| Sprint Backlog / Sprint 待办列表 | Sprint Goal / Sprint 目标 | The Sprint Goal, selected Product Backlog items, and the Developers' plan |
| Increment / 增量 | Definition of Done / 完成定义 | A usable step toward the Product Goal that meets the shared quality measure |

The commitments focus the artifact without replacing it. Multiple Increments may be created during a Sprint; the Sprint Review is not a release gate.

### Common challenges

- **Treating Scrum as a status-report schedule:** the events exist to inspect and adapt work toward goals, not merely to report individual activity.
- **Treating the Sprint Backlog as an unchangeable contract:** the Developers adapt their plan as they learn, while working toward the Sprint Goal. The Product Owner and Developers can clarify and renegotiate scope without endangering that goal.
- **Skipping inspection and improvement:** omitting defined events loses their intended opportunities and means the team is not using the framework as described.
- **Assuming Scrum fits every problem:** choose a way of working that fits the product, feedback cycle, and organizational constraints. Regulated work can also use iterative development when its evidence and control requirements are built into the process.

**See also:** [Interview Tips](#47.%20How%20do%20you%20prepare%20behavioral%20answers%20with%20evidence%20you%20can%20support?%20/%20%E5%A6%82%E4%BD%95%E5%87%86%E5%A4%87%E6%9C%89%E4%BA%8B%E5%AE%9E%E4%BE%9D%E6%8D%AE%E3%80%81%E7%BB%8F%E5%BE%97%E8%B5%B7%E6%A0%B8%E5%AE%9E%E7%9A%84%E8%A1%8C%E4%B8%BA%E9%9D%A2%E8%AF%95%E5%9B%9E%E7%AD%94%EF%BC%9F) for discussing team practices accurately.

Sources: [The Scrum Guide, November 2020](https://scrumguides.org/scrum-guide.html) and the [Agile Manifesto](https://agilemanifesto.org/).
## 47. How do you prepare behavioral answers with evidence you can support? / 如何准备有事实依据、经得起核实的行为面试回答？

Begin with the role's needs and facts from your own experience. Shape one relevant example as context → action you personally took → result or other evidence; describe qualitative outcomes plainly and never invent a metric or someone else's story. Research current role, company, location, and compensation details before the conversation, state skill gaps honestly, and prepare questions that help you understand the work. / 从岗位需求和自己真实经历中的事实开始。选择一个相关例子，按背景 → 个人行动 → 结果或其他证据组织；定性结果应如实描述，不要编造指标或借用别人的故事。面试前调研当前岗位、公司、地点和薪酬信息，坦诚说明技能缺口，并准备能帮助自己了解工作的提问。

### Discussing strengths and weaknesses

#### Strengths

Choose a strength that matters for the role, then support it with one real example. A compact structure is **context → action you took → result or evidence**.

- “I work carefully with edge cases. In [specific situation], I [action I personally took], which led to [verifiable result].”
- “I learn unfamiliar tools by [specific method]. For example, I used that approach to [real task] and [what changed or what I learned].”

Replace each bracketed part with your own evidence. If the result is qualitative, describe what changed without inventing a metric.

#### Weaknesses

**诚实说明一个真实的发展方向，并说明正在采取的步骤。** Choose something you are actively improving and explain how you notice progress. Avoid presenting a disguised strength or claiming a weakness that would prevent you from doing the role's core work.

- “I am still developing [skill]. I have been improving it by [specific practice], and I can now [observable progress].”

### Salary expectations

- Research a current range for the role, seniority, location, and total compensation before the conversation.
- If you are ready to give a number, state a range and the assumptions behind it; leave room to discuss the full package.
- If the responsibilities are not yet clear, ask about the role's level and compensation range before giving a precise expectation.

### Why are you a good fit?

Connect the role's stated needs to evidence you actually have:

1. **Skills match / 技能匹配** — identify the relevant requirement.
2. **Evidence / 事实依据** — give a project, responsibility, or result that demonstrates it.
3. **Motivation / 求职动机** — explain which part of this role you want to work on.

Template: “This role needs [requirement]. In [real example], I [specific contribution] and [result or learning]. I am interested in applying that experience to [specific part of the role].”

### Company research

- Understand the product, users, and the role's team from current company materials.
- Connect your experience to a specific need instead of reciting company slogans.
- If you do not know a detail, say what you have learned so far and ask a focused question.

### Addressing lack of experience

State the gap plainly, then describe related experience and a realistic learning plan. Avoid guaranteeing that you will master an unfamiliar area by a fixed date unless you have a basis for that estimate.

Template: “I have not used [technology] in [relevant context]. I have used [related skill] for [real example], and I would start by [specific way to learn or validate the new system].”

### Questions to ask the interviewer

Prepare questions that help you understand the work. Choose the ones that remain unanswered by the conversation.

**About the role:**

- “What are the most important outcomes for this role in the first few months?”
- “What technical challenges would this person work on?”
- “How do you measure success for the position?”

**About the team:**

- “How does the team approach code review and knowledge sharing?”
- “How are technical decisions made, and who is involved?”

**About growth:**

- “What opportunities are there to deepen or broaden engineering skills?”
- “How does the team support progression for engineers?”

### Closing the interview

Thank the interviewer, restate a specific reason for your interest, and ask about the next step if it has not already been explained. If your questions were answered during the discussion, say so and use the remaining time for a follow-up.

**See also:** [Agile and Scrum](#46.%20How%20does%20Scrum%20help%20a%20team%20inspect%20and%20adapt%20work?%20/%20Scrum%20%E5%A6%82%E4%BD%95%E5%B8%AE%E5%8A%A9%E5%9B%A2%E9%98%9F%E6%A3%80%E6%9F%A5%E5%B9%B6%E8%B0%83%E6%95%B4%E5%B7%A5%E4%BD%9C%EF%BC%9F) for the current Scrum vocabulary used in team-process discussions.
