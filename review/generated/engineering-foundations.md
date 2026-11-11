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

超时只代表调用方没有收到响应；它无法区分请求未到达、事务回滚、事务仍在进行，或提交后只有响应丢失。每次查询或重放前，服务都要再次校验当前账户和主体有权读取这条操作结果。事务提交后，数据库中库存为 0，且存在 reserve-demo-208 与请求指纹 fingerprint-A 绑定的预留记录。客户端使用同一个操作键查记录或按明确的幂等契约重放；API 比较账户、主体与请求指纹后返回已记录结果而不再次扣减。不能为重试生成新键，否则服务端会把它当成另一次购买。键的作用域、保留窗口与未知结果重试规则由[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)专门解释。

操作键记录必须和库存效果处于同一事务；若先扣库存并提交，之后再单独写操作键，二者之间崩溃仍可能造成“效果已发生但重试认不出”。支付服务或消息队列不在这个本地事务中，不能靠 SQL COMMIT 宣称远端副作用也完成。账户报表的数据库到队列边界会用 transactional outbox（事务型发件箱）延伸这一问题，见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 同一库存不变量怎样用于抽奖？

抽奖服务对外提供公开只读的 GET /draws/{campaignId}，返回活动规则、时间与可见状态；已认证参与者以 POST /draws/{campaignId}/entries 提交自己的请求。服务端按当前主体检查活动仍开放、资格和一次参与规则，并使用 (campaign_id, principal_id) 唯一约束及作用域幂等键阻止重复参与。活动已关闭应返回明确 campaign-closed 状态；已有参与记录或其他规则冲突应返回明确 conflict，不让浏览器从通用错误猜结果。抽奖随机性和审计规则须符合活动承诺；统计事件不能决定资格或权威中奖结果。

有限奖品应在同一事务里条件扣减并保存参与、抽取结果与待领取状态；若扣减零行，要按活动规则明确返回库存已用完/未中奖等业务结果，不能假定数据库自动替用户重新抽取。GET /draws/{campaignId}/entries/{entryId} 只能向当前结果所有者返回本人结果与领取状态；单独的 POST /prizes/{prizeId}/claims 再验证中奖记录所有者，只收集履约所需资料并写入履约状态。后台活动管理权限应比公开读取和本人参与更严格。抽奖提交也需使用稳定操作键，并按幂等契约定义保留窗口与重放结果，避免超时后重复参与；通用规则见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。原档案的独特接口流、显式关闭/冲突结果和权限分层已迁入本节；旧入口保留导航，见[归档抽奖 API 规则入口](../../archive/front-end/Deprecated_Interview_Notes/prize-draw-api-invariants.md)。

**接下来：** 此处只说明原子库存写入及本地约束。NULL、连接和分组改变报表查询的方式见[NULL、连接与分组如何改变报表 42 的结果？](#7.%20SQL%20%E7%A9%BA%E5%80%BC%E3%80%81%E8%BF%9E%E6%8E%A5%E4%B8%8E%E5%88%86%E7%BB%84%E4%BC%9A%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E6%8A%A5%E8%A1%A8%2042%20%E7%9A%84%E7%BB%93%E6%9E%9C%EF%BC%9F)；事务隔离、WAL 和崩溃恢复的保证见[事务隔离与 WAL 能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - 条件扣减的并发重检与事务隔离行为：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1，核对于 2026-11-06；此处并发时序明确标为 PostgreSQL 行为。
> - 主键、唯一、外键、CHECK 和 NOT NULL 的持久约束：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)，§5.5，核对于 2026-11-06。
> - SQLite 事务和外键约束：[SQLite Transactions](https://www.sqlite.org/lang_transaction.html) 与 [Foreign Key Support](https://www.sqlite.org/foreignkeys.html)，核对于 2026-11-06。
## 2. 浏览器请求如何到达 HTTP 响应？

Hypertext Transfer Protocol (HTTP，超文本传输协议) 规定调用方怎样描述操作、服务端怎样返回状态与表示；Transmission Control Protocol (TCP，传输控制协议) 或 QUIC 负责承载字节流，Transport Layer Security (TLS，传输层安全协议) 在安全连接上保护通信。看同一个报表请求，应先认清 HTTP 语义，再按是否有可复用缓存、地址和连接追踪网络阶段。HTTP 版本会改变连接复用和多路复用方式，但不会替 application programming interface (API，应用程序接口) 验证身份、授权资源、允许跨源读取或确认超时操作结果。

**案例：** 查看者已登录并获准读取报表 42。此前浏览器收到 `200` JSON、`ETag: "report-42-v8"` 和 `Cache-Control: private, no-cache`，并把该表示保存在自己的私有缓存。用户再次打开页面时，浏览器用旧验证值询问当前表示。图中的某些阶段会因 Service Worker、缓存、DNS 地址或已有连接而跳过；持续更新则需要独立的消息与恢复契约，见[何时选择轮询、SSE、流式 Fetch 或 WebSocket？](#19.%20%E4%BD%95%E6%97%B6%E9%80%89%E6%8B%A9%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)。

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

safe method (安全方法) 的预期语义是不要求改变目标资源状态；这不禁止日志、计数等附带效果。idempotent (幂等) 表示重复执行的预期效果等同执行一次，不要求响应字节相同：第一次 DELETE 可回 204，后续回 404，但资源仍保持不存在。PUT 让目标资源成为请求描述的状态，不必然表示没写的字段都会清空；PATCH 是否幂等取决于补丁操作和接口约定；POST 通常不具幂等性。方法语义不能独自说明连接中断后副作用是否已经提交；未知结果需用业务请求标识确认，见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

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

**接下来：** 若页面与 API 不同源，浏览器何时允许脚本读取响应由[浏览器安全边界](#6.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AE%89%E5%85%A8%E6%8E%A7%E5%88%B6%E5%88%86%E5%88%AB%E4%BF%9D%E6%8A%A4%E4%BB%80%E4%B9%88%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C%EF%BC%9F)说明；若要连续接收报表更新，则选取[实时传输与恢复方式](#19.%20%E4%BD%95%E6%97%B6%E9%80%89%E6%8B%A9%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)。

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
ETag: "report-42-v7"

{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
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

### 如何用条件 PATCH 防止覆盖别人更新？

客户端先读取报表 42，服务为当前表示发出强 ETag（实体标签）`"report-42-v7"`，客户端保存它和基线表示：

~~~http
GET /api/reports/42 HTTP/1.1
Host: reports.example
Accept: application/json
~~~

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "report-42-v7"

{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

之后用户把交付方式切为下载，并删除可选备注。此资源只接受 JSON Merge Patch（JSON 合并补丁），所以请求声明媒体类型 `application/merge-patch+json`，并带上刚读到的强 ETag：

~~~http
PATCH /api/reports/42 HTTP/1.1
Host: reports.example
Content-Type: application/merge-patch+json
If-Match: "report-42-v7"

{"delivery":{"channel":"download"},"note":null}
~~~

Merge Patch 的对象成员按名称递归合并：未出现的成员保持，`null` 表示删除成员，数组整体替换。应用补丁后的中间表示仍有旧 `recipients`，因为该成员在补丁里被省略；本合成 API 另规定下载模式不保存收件人字段，业务规范化随后移除它，并验证最终表示。若 `channel` 是 `email`，最终表示必须含至少一个合法收件人；不合法的最终文档整笔拒绝。Merge Patch 里的 `null` 不能同时表示“字段存在且值为空”；若资源必须保留显式 JSON null，应为该字段另定表示或选择别的补丁格式。

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "report-42-v8"

{"id":42,"title":"Monthly summary","delivery":{"channel":"download"}}
~~~

表单只序列化当前模式字段：切到 `download` 时不提交隐藏的 `recipients`。服务端通过该模式的领域规则移除不适用字段，因此它既遵守“补丁省略字段表示保持”的通用规则，也返回不含旧收件人的规范表示。若后来切回 `email`，一次新的补丁可把整个收件人数组替换为 `["editor@example.test","audit@example.test"]`；数组元素不是独立增删操作。

版本判断必须和写入处在一个原子条件里。可以在事务中锁定并检查版本、合并和验证，然后执行版本条件更新；也可以把合并后的文档连同预期版本交给数据库条件更新：

~~~sql
UPDATE reports
SET document = :validated_document,
    version = 8
WHERE report_id = 42
  AND tenant_id = :authorized_tenant
  AND version = 7
RETURNING document, version;
~~~

只有影响一行的事务提交，服务才返回新表示和 ETag。若版本条件不成立，事务不能写入任何补丁内容。不能先在事务外读到 v7、随后无条件更新：两次并发请求都可能检查 v7 后依次覆盖对方。

假设用户甲和乙都读到 v7。甲先提交后，当前表示成为 v8；乙仍用 v7 的编辑提交时，服务返回 412 Precondition Failed（前置条件失败），不自动覆盖、不自动重放：

~~~http
HTTP/1.1 412 Precondition Failed
Content-Type: application/problem+json

{"type":"https://api.example/problems/version-mismatch","title":"The report changed","status":412}
~~~

乙的客户端保留自己的草稿和 v7 编辑基线，重新读取 v8，再把基线、用户草稿与服务器当前表示进行比较；用户确认合并后才以新 ETag 再提交。若请求没有 `If-Match`，此合成端点选择 428 Precondition Required（要求前置条件）；这是一项端点政策。客户端在提交编辑时携带所保存的强 ETag；服务端能验证它是否以强比较匹配当前表示，但不能证明调用方真的曾读取过它。此端点不接受 `W/"…"` 弱标签或 `*`：本合成政策要求逐版本比较，不把“资源存在”当作编辑基线。授权仍先于更改；412 不能替代对象授权结果。

这里选 JSON Merge Patch，不把 JSON Patch（JSON 操作补丁）当成同一语法：后者的 `application/json-patch+json` 正文是带 `add`、`remove`、`replace`、`move`、`copy` 或 `test` 的操作数组，数组元素和 `null` 按操作路径处理。服务应公开自己接受的媒体类型，例如通过 `Accept-Patch`，调用方也不能仅凭 HTTP 方法名猜补丁语义。

### 201 创建资源和 202 接受作业有什么区别？

`POST /api/reports` 可创建一条报表资源记录，返回 `201 Created` 和 `Location: /api/reports/44`。如果新资源的 `status` 是 `queued`，201 表示资源记录已经建立，不表示报表成品已生成。若请求创建的是独立长作业，账户报表案例使用 `POST /v1/accounts/acct-17/reports`，客户端预先生成 `Idempotency-Key: report-demo-208`；成功受理时，`202 Accepted` 的 `Location` 和正文 `statusUrl` 都指向 `/v1/jobs/job-demo-731`。如果整个响应丢失，客户端用相同请求体和幂等键重发 POST，数据库返回同一个已持久化 job 与状态 URL；同键对应不同规范化请求则冲突，不能猜测 job ID。收到 URL 后再 `GET /v1/jobs/job-demo-731` 查询。202 表示已受理，不表示成功完成。具体事务和映射见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 分页怎样给出明确结束条件？

集合可能很大或持续变化，契约须规定页大小、确定性排序和结束信号。本例默认 `limit=2`、最大 100，按 ID 升序；`next_cursor` 是必返回字段，最后一页明确返回 JSON `null`。

~~~http
GET /api/reports?limit=2 HTTP/1.1
Host: reports.example
Accept: application/json
~~~

~~~json
{"items":[{"id":41,"title":"Monthly overview","status":"ready"},{"id":42,"title":"Monthly summary","status":"ready"}],"next_cursor":"opaque-token-A"}
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

这两页使用固定的三条演示数据：第一页 `[41, 42]` 续到 ID 42 之后，第二页 `[43]` 以 `null` 明确结束；只有客户端看见该结束标记才停止。短页不总表示没有后续数据。下面的内存复现把不透明 token 映射为偏移量，只适用于这组不变的演示数据：如果第一页后删除 ID 41，偏移量仍跳过两条，第二页会漏掉 ID 43。生产中的移动集合可把游标绑定筛选条件、授权范围、过期时间和最后一条记录的稳定复合键（如 `(created_at, id)`），下一页按键续读并每页重新授权；若要求固定快照，则必须让后续请求继续读取同一个快照。并列时间戳时，键集游标要同时保存两个排序键。

> [!example] 读完三条报表的分页回放
> 在这组固定数据中，ID 升序且页大小为 2：第一批是 `[41, 42]`，第二批是 `[43]`，返回 `next_cursor: null` 后停止。内存复现用偏移量映射 token；它不演示可变集合中的 keyset 或快照分页。若服务器因资源上限只返回 1 项但仍有后续数据，只凭短页就停止会漏项。运行代码会生成不透明 token。

### OpenAPI 怎样描述实际运行契约？

OpenAPI 记录操作路径、参数、媒体类型、成功与错误响应及 schema，使人和工具可据此调用服务。框架可从请求/响应模型生成结构；自定义异常处理器也要在相应操作里声明错误响应。只有运行时错误和 OpenAPI 都匹配，客户端才不会按一份服务实际不返回的契约生成分支。检查时要按操作核对真实路径、状态码、媒体类型、Problem `type`、分页字段是否必填以及 schema 是否允许 `null`。

下面的 FastAPI 复现定义裸应用前缀 `/api`，演示 GET/POST、验证、分页和 OpenAPI；它不实现上一节的 PATCH、Merge Patch 或 `If-Match`。PATCH 合同使用 `/api/reports/42` 和 `Monthly summary` 的表单表示；可运行 fixture 是独立的最小数据集，GET 42 固定返回 `Service health`，只验证 GET/POST 映射，不证明 PATCH 表示或并发写入。复现也没有身份认证、租户授权或数据库并发唯一性，不是可直接部署的安全报表服务。正常请求和失败的输入输出已在正文展示，无需运行这段代码才能理解相应契约。

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
> 此示例用内存中的偏移量映射演示游标边界；进程重启后令牌会失效，也未绑定筛选条件、排序或身份。生产集合可使用基于索引的键集游标，并对每一页重新授权。页面内容由这三条记录计算，不代表性能测量结果。

### API 返回的链接怎样告诉客户端可继续做什么？

REST 的 Hypermedia as the Engine of Application State（超媒体作为应用状态引擎，HATEOAS）约束要求客户端从服务端表示中发现当前可用的状态转移。客户端仍需理解媒体类型和关系名，但不必仅凭报表 ID 拼出每个目标 URL。API 可以在报表表示中按自己的契约返回链接：

~~~json
{
  "id": 42,
  "links": [
    { "rel": "self", "href": "/api/reports/42" },
    { "rel": "download", "href": "/api/reports/42/download" }
  ]
}
~~~

React 客户端可以按关系查找详情地址并渲染链接。下面假设 `self` 关系已在 API 表示契约中定义，`href` 是同源站点根路径；只有契约明确允许时才跟随异源地址，不能把当前站点的认证信息盲目附到异源请求上。客户端不再根据 `id` 自行构造 `/api/reports/${id}`。

~~~tsx
type ApiLink = { rel: string; href: string };
type Report = { id: number; links: ApiLink[] };

function ReportDetailsLink({ report }: { report: Report }) {
  const self = report.links.find(link => link.rel === "self");
  return self ? <a href={self.href}>查看报表详情</a> : null;
}
~~~

普通链接适合安全导航，例如读取详情。链接本身若只给出 `href`，并没有说明取消报表等写操作应使用什么 HTTP 方法和请求体；这类动作应按 API 明确声明的 affordance（操作描述）或另行定义的契约发送，不能把有副作用的操作伪装成 `<a>`。单页应用可由路由接管内部导航，但路由仍需按它自己的加载和历史规则提交地址；服务端返回链接不会自动配置 React Router。

### 兼容演进需要显式规则

新增可选响应字段通常可兼容会忽略未知字段的客户端，但严格解码器或生成代码可能拒绝它。删除字段、改变字段类型或含义、把可选请求字段改为必填、改变 Problem `type`、调整分页结束标志，都可能破坏调用方。应公开兼容政策，检查重要调用方，并为不兼容变更安排版本切换或迁移窗口；不存在唯一强制的版本化方案。

**接下来：** 本章描述调用方可观察的接口结构；HTTP 方法、缓存与状态码的通用语义见[浏览器请求如何到达 HTTP 响应？](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F)，副作用未知后的结果查询和重试见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - 错误正文的类别标识、状态、标题、详情和扩展字段：[IETF RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)，§3–§4，2023-07；核对于 2026-11-06。
> - 400、401 challenge、403、404、409、422、201 与 202 的 HTTP 语义：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§9、§11.6.1、§15，2022-06；428 和 429 则分别见 RFC 6585 §3–§4；核对于 2026-11-09。
> - 操作、参数、媒体类型、响应和 schema 的接口描述：[OpenAPI Specification v3.2.1](https://spec.openapis.org/oas/v3.2.1.html)，2026-09-10，§4–§5；核对于 2026-11-06。代码环境当前生成 3.1.0；运行时版本由 `app.openapi()['openapi']` 决定，规范文件描述契约但不保证实现遵循它。
> - 页大小、请求间参数一致、不透明 page token 和结束信号：[Google AIP-158, Pagination](https://google.aip.dev/158)，2019-02-18，Guidance；核对于 2026-11-06。
> - FastAPI 请求模型、响应模型和自定义错误处理：[FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)、[Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)、[Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)，官方文档核对于 2026-11-06；错误类型映射已在列明版本的本地运行环境核对。
> - REST 超媒体约束及由表示提供状态转移：[Roy Fielding, Architectural Styles and the Design of Network-based Software Architectures, §5.1.5](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，2000；核对日期：2026-11-06。
> - 安全的 `GET` 方法与 HTTP 方法语义：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§9.2.1，2022-06；核对日期：2026-11-06。
> - 条件更新与陈旧 ETag： [IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.1) §13.1.1（`If-Match` 必须用强比较）和 §15.5.13（412），2022-06；核对于 2026-11-09。 [IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html#section-3) §3 定义 428，2012-04；它只用于此端点所选择的缺少前置条件响应。该 RFC §4 定义 429，并规定 429 响应不得被缓存。
> - PATCH 的整组变更原子应用及 `Accept-Patch`： [IETF RFC 5789, PATCH Method for HTTP](https://www.rfc-editor.org/rfc/rfc5789.html#section-2) §2、§3.1，2010-03；核对于 2026-11-09。
> - `application/merge-patch+json` 的成员省略、`null` 删除和整体数组值语义：[IETF RFC 7396, JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396.html#section-2)，§2，2014-10；核对于 2026-11-09。JSON Patch 的操作媒体类型见 [IETF RFC 6902](https://www.rfc-editor.org/rfc/rfc6902.html)，§3–§4，2013-04。
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

缓存命中会绕过数据库谓词，因此先查当前成员资格，再访问带范围的缓存。此例缓存键是 `(tenant_id, subject, report_id)`：租户乙不能拿租户甲的缓存副本，且每次 API 请求都会先重查当前成员。固定所有权是这个精简示例的假设；若报表可以迁移租户或分享权限会变，就要在命中路径复验对象访问条件，或确保权限变更同步使缓存失效。参见[如何控制数据库缓存的新鲜度？](#12.%20%E6%80%8E%E6%A0%B7%E7%BC%93%E5%AD%98%E6%95%B0%E6%8D%AE%E5%BA%93%E8%AF%BB%E5%8F%96%E5%B9%B6%E8%AF%B4%E6%98%8E%E9%99%88%E6%97%A7%E7%AA%97%E5%8F%A3%EF%BC%9F)。

### 后台任务如何继续执行相同的访问政策？

排队时先按该任务的实际动作授权，再保存服务端创建的可信任务记录。消息只带不透明 `job_id`；worker 用该 ID 从可信存储读取租户、请求人和资源，不从任意消息载荷接受租户或报表编号。worker 是否要在执行时重新检查成员资格取决于产品定义：若成员移除后应停止工作，就复验当前权限；若已受理任务按提交时权限继续，则把那项授权决定作为可审计状态持久化。

下面的复现仅演示“读取一个已经存在的报表”任务，因此 `enqueue_read_job` 只需要 `report:read`。高成本报表导出或重算必须另查 `report:export` 等独立动作，或者明确定义其权限组合；不能从 `reader` 自然推出。账户报表作业的幂等受理、outbox 发布和队列确认见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)；队列确认分别见[发布者确认和消费者确认分别证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

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

**接下来：** 本章负责服务端把主体、动作和租户内资源联系起来；浏览器跨源读取、Cookie 自动发送和脚本执行见[浏览器安全控制分别保护什么信任边界？](#6.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AE%89%E5%85%A8%E6%8E%A7%E5%88%B6%E5%88%86%E5%88%AB%E4%BF%9D%E6%8A%A4%E4%BB%80%E4%B9%88%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C%EF%BC%9F)。网络入口容量与攻击流量准入见[Web 服务如何限制拒绝服务的影响？](#29.%20Web%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%8B%92%E7%BB%9D%E6%9C%8D%E5%8A%A1%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F)。

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

WebSocket 握手也不能用 CORS 响应字段授权。浏览器会发送 Origin；服务端应按允许来源校验握手、认证连接，并对敏感消息继续授权。双向消息和断线恢复见[何时选择轮询、SSE、流式 Fetch 或 WebSocket？](#19.%20%E4%BD%95%E6%97%B6%E9%80%89%E6%8B%A9%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)。

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

API 只有在 UPDATE 返回一行后才执行 INSERT；零行、作用域操作键冲突或其他写入错误都要显式 ROLLBACK。零行或作用域键冲突后，先回滚这个尝试，再在新事务按当前授权范围查询键并比较指纹；同键同指纹返回已提交结果，同键异指纹冲突，确认没有该键后才报告 SKU 不存在或售罄。提交之后若客户端连接断开，数据库行仍说明是否存在 reserve-demo-208；不能把“客户端超时”当成数据库自动回滚的信号。若 COMMIT 响应丢失，沿[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)的同键流程查询已提交结果，或以同键安全重放；唯一约束只能帮助裁决并发写入，不能单独给出重放响应。

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

**接下来：** SQL 约束与索引决定哪些业务状态可写、哪些访问路径可用，见[如何用约束保护业务规则并为读取建立索引？](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F)。当服务用 ORM 请求数据库时，session、事务与连接的持有时间见[如何限定 ORM Session 并诊断连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。

> [!info]- 来源
> - 隔离级别异常定义、PostgreSQL 18 每语句快照、更新等待重检与 Serializable 重试：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1–13.2.3，核对于 2026-11-06；本地双连接并发实跑版本为 PostgreSQL 14.24，未在 PostgreSQL 18 实跑。
> - MVCC 版本可见性与 VACUUM：[PostgreSQL 18, Introduction to MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html)，§13.1，核对于 2026-11-06。
> - WAL 先持久日志再写数据页、提交确认不依赖所有数据页已写回、崩溃重做与基础备份加日志的时间点恢复：[PostgreSQL 18, WAL Introduction](https://www.postgresql.org/docs/18/wal-intro.html)，§28.3，[WAL Configuration](https://www.postgresql.org/docs/18/wal-configuration.html)、[Asynchronous Commit](https://www.postgresql.org/docs/18/wal-async-commit.html) 及 [Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/18/continuous-archiving.html)，核对于 2026-11-06。
> - SQLite 的本地事务与日志模式：[SQLite Transactions](https://www.sqlite.org/lang_transaction.html) 与 [Write-Ahead Logging](https://www.sqlite.org/wal.html)，核对于 2026-11-06。
> - 课程 ARIES 推导：[Mohan et al., ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging)；关联原始课程页[WAL 与 ARIES 的逐步恢复例题](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md)。
> - CAP 的网络分区边界：[Gilbert and Lynch, Brewer’s conjecture and the feasibility of consistent, available, partition-tolerant web services](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf)；两阶段提交的预备状态限制：[PostgreSQL 18, PREPARE TRANSACTION](https://www.postgresql.org/docs/18/sql-prepare-transaction.html)，核对于 2026-11-06。
## 10. InnoDB 怎样用索引记录、旧版本与日志处理库存事务？

**案例：** 合成库存中，SKU-7 全局只剩一件。两个会话都尝试为 acct-17 预留；会话 A 先读到 available=1，会话 B 更新并提交后，A 的普通 SELECT 仍可能读到旧值。要正确理解结果，需要沿着 InnoDB 索引定位行、多版本并发控制（MVCC）可见版本、当前写锁和崩溃日志各走一遍。

本文使用 MySQL 8.4、InnoDB、autocommit=1；并发例显式设为 REPEATABLE READ。持久性演算假设 binary log（二进制日志）已启用、innodb_flush_log_at_trx_commit=1、sync_binlog=1，且操作系统与存储设备正确兑现 flush（刷入持久存储）。它们是推演条件，不是本机 MySQL 实测。本仓库的通用事务页使用 PostgreSQL 例子；该页的 SQL 并发与日志描述不能直接当作 InnoDB 的锁范围。

~~~mermaid
flowchart TD
    SQL[SQL 谓词] --> Index[索引访问路径]
    Index -->|普通 SELECT| Snapshot[快照版本：read view 与 undo]
    Index -->|UPDATE| Update[当前读]
    Index -->|SELECT FOR UPDATE| LockingRead[当前读]
    Update --> Lock[按访问路径取得索引锁]
    LockingRead --> Lock
    Lock -->|UPDATE 修改记录| Page[写页修改并记录 redo]
    Page --> Commit[提交：prepare、binlog 决策、InnoDB 完成]
    Page -. 提交前意外退出 .-> Crash[崩溃恢复：redo 前滚，再保留或撤销]
    Commit -. 提交期间或之后意外退出 .-> Crash
~~~

### 查询先走哪棵 InnoDB 索引？

先创建最小的全局 SKU 库存与预留表。SKU-7 的 available=1 是全局库存，预留记录才带 acct-17；所以 acct-17 是这次预留的账户，不是 SKU 库存归属。其它几行只用于展示一次范围锁。MySQL 8.4 中 InnoDB 表的主键是 clustered index（聚簇索引），叶子节点保存完整行。secondary index（二级索引）的叶子项保存二级键列和主键值；若查询需要的列不都在二级索引中，存储引擎再用主键回到聚簇索引取行。

~~~sql
CREATE TABLE inventory (
    sku_id INT NOT NULL PRIMARY KEY,
    warehouse_id VARCHAR(16) NOT NULL,
    available INT NOT NULL CHECK (available >= 0),
    note VARCHAR(64) NOT NULL
) ENGINE = InnoDB;

CREATE INDEX inventory_by_warehouse_stock
    ON inventory (warehouse_id, available);

CREATE TABLE reservations (
    request_key VARCHAR(64) NOT NULL PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL,
    sku_id INT NOT NULL,
    status VARCHAR(16) NOT NULL,
    FOREIGN KEY (sku_id) REFERENCES inventory(sku_id)
) ENGINE = InnoDB;

INSERT INTO inventory VALUES
    (7,  'W-1', 1, 'last unit'),
    (10, 'W-1', 5, 'synthetic range row'),
    (11, 'W-1', 4, 'synthetic range row'),
    (13, 'W-2', 2, 'synthetic range row'),
    (20, 'W-2', 1, 'synthetic range row');
~~~

~~~mermaid
flowchart LR
    Q[SQL 谓词] --> Index[选择索引访问路径]
    Index -->|主键| Clustered[聚簇索引记录即完整行]
    Index -->|二级键| Secondary[二级项含键列和主键]
    Secondary -->|还要其他列| Clustered
~~~

WHERE sku_id = 7 用主键唯一定位 SKU-7 的完整行。若查 WHERE warehouse_id='W-1' AND available >= 1，可能先走 inventory_by_warehouse_stock 的有序范围，再用每个二级项中的 sku_id 回到聚簇索引取 note。若投影的列都包含在二级索引和主键中，计划可能覆盖查询而省去回表；最终索引是否被使用仍由优化器和实际统计信息决定。

### 普通读为什么能看见已过时库存？

在 REPEATABLE READ（InnoDB 默认级别）下，同一事务里的普通非锁定 SELECT 使用由第一次一致性读建立的 read view。它为查询判断哪些已提交版本可见，不会锁住被读记录。若某行后来被其他事务更新，undo 保存了重建旧版所需的信息，普通读可以沿版本链还原到快照值。它还会看见本事务自己已经写入的变更。

~~~mermaid
flowchart LR
    Read[普通 SELECT] --> View{最新行版本对 read view 可见?}
    View -->|是| CurrentVersion[直接读取该版本]
    View -->|否| Undo[沿 undo（回滚日志）重建可见旧版]
    Undo --> OldVersion[读取重建出的快照版本]
~~~

下面的两会话顺序明确指定版本；SQL 推演以 SKU-7 初值 1 开始：

~~~sql
-- 会话 A
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT available FROM inventory WHERE sku_id = 7;
-- 第一次一致性读建立快照，结果 1。

-- 会话 B
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
UPDATE inventory
SET available = available - 1
WHERE sku_id = 7 AND available > 0;
-- 更新 1 行，自己的当前值变为 0。
INSERT INTO reservations VALUES
    ('reserve-42', 'acct-17', 7, 'reserved');
COMMIT;
~~~

会话 B 提交后，会话 A 再执行：

~~~sql
-- 会话 A，仍在原事务和原 read view 内
SELECT available FROM inventory WHERE sku_id = 7;
-- 普通一致性读仍是 1；undo 提供快照所需旧版。

SELECT available FROM inventory
WHERE sku_id = 7
FOR UPDATE;
-- 锁定读是 current read，看到最新已提交值 0，并锁定该记录。

UPDATE inventory
SET available = available - 1
WHERE sku_id = 7 AND available > 0;
-- 条件不再成立，影响 0 行；不会把库存扣成负数。
-- 影响 0 行就不插入预留记录；只有扣减 1 行的事务才创建 reservation。
COMMIT;
~~~

普通 SELECT 得到 1 并不说明数据库允许 A 继续按 1 扣减。UPDATE 和 FOR UPDATE 是 current read（当前读）/写操作，围绕可写的当前记录协调锁；A 的更新条件会在实际写入处对当前值求值，结果为零行。若 B 尚未提交而 A 先申请 SKU-7 的排他锁，A 会等待持锁事务提交或回滚，再按可用的当前版本继续处理。普通读的快照与当前写路径是两种视图，混在同一事务时要清楚自己正在用哪一种。

### 唯一命中与范围扫描为什么锁不同？

锁落在索引记录和索引间隙上，不是抽象的 SQL 行集合上。本例用完整主键精确找到已存在的 SKU-7；这次搜索只锁该主键记录，不需要锁它前面的间隙：

~~~sql
START TRANSACTION;
-- 唯一命中：SKU-7 的主键记录锁
SELECT available FROM inventory
WHERE sku_id = 7
FOR UPDATE;
COMMIT;
~~~

完整唯一键命中现有行时，搜索不需要锁索引记录前方的间隙；若排他锁定通过二级索引搜索，InnoDB 还会锁对应的聚簇索引记录。REPEATABLE READ 下，范围搜索和索引扫描可以使用 next-key lock（临键锁）：它把一个索引记录锁与该记录之前的 gap lock（间隙锁）组合起来。这里用两个新会话明确观察事务锁；上一个例子已经结束并提交，不再持有任何锁。A 明确开启事务并锁住主键范围，B 再插入该范围内的新行：

~~~mermaid
flowchart LR
    Write[UPDATE] --> Current[current read（当前读）]
    LockingRead[SELECT FOR UPDATE] --> Current
    Current --> Lock[按访问路径取得索引锁]
~~~

~~~sql
-- 会话 A；明确使用 REPEATABLE READ，autocommit=1
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- 显式事务一直保持到 COMMIT/ROLLBACK
START TRANSACTION;
SELECT sku_id FROM inventory
WHERE sku_id BETWEEN 10 AND 20
FOR UPDATE;
-- 结果包含 10、11、13、20；记录 20 的前间隙 (13, 20) 受保护，A 暂不结束事务。

-- 会话 B；明确使用 REPEATABLE READ，单条 INSERT 在 autocommit=1 下执行
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
INSERT INTO inventory VALUES (15, 'W-1', 2, 'insert in protected gap');
-- 因 A 仍持有范围锁而等待。

-- 会话 A
COMMIT;
-- A 释放锁后，B 的 INSERT 才能继续并提交。
~~~

这段演算以 REPEATABLE READ 和主键范围访问为前提；sku_id 是主键，优化器可用该索引定位范围。sku_id=15 落在受记录 20 的 next-key lock 保护的前间隙 (13, 20)，所以 B 等 A 结束后才能插入。若 A 回滚也会释放锁，B 随后继续。间隙锁的用途是阻止匹配范围出现幻行，不代表该 SQL 已锁住整张表。

唯一索引的部分复合键不等于完整唯一命中；若 UNIQUE 是 (warehouse_id, sku_id)，只给 warehouse_id 条件仍须扫描多个条目，可能锁范围。实际锁范围还取决于执行计划选中的索引、谓词和隔离级别，因此排查等待要先用 EXPLAIN 看访问路径，再检查 InnoDB 锁信息；不能仅凭 SQL 文本里的 WHERE 子句推断只锁住命中的业务行。READ COMMITTED 下搜索扫描通常不使用这些 gap locks，但外键与重复键检查仍可能使用。

### 崩溃时 redo 和 undo 各做什么？

redo 记录数据页修改的恢复信息，让启动恢复能把尚未写回表空间的变更前滚。undo 保存旧行值或回滚所需信息：一致性读用它重建快照版本；事务回滚和崩溃后回滚未提交事务也用它撤销未完成工作。它们服务的方向不同：redo 解决页修改怎样恢复，undo 解决旧版本可见性与未提交变化怎样撤销。

崩溃演算从独立状态开始：SKU-7=1，且没有 reserve-42。要判断事务是否成功，MySQL 8.4 不只看客户端是否收到 COMMIT 响应。InnoDB 先准备事务，服务器把完整事务及 XID 写入并按 `sync_binlog=1` 同步 binlog，再让 InnoDB 完成提交。若此时崩溃，启动恢复从 binlog 找到已持久的完整提交决策，并完成相应的 prepared 事务；若没有该决策，未提交事务会回滚，已 prepare 的事务也会因 binlog 中没有其 XID 而回滚。因此“客户端没收到响应”仍可能恢复为已提交，决策边界是可恢复的 binlog 提交记录。

~~~mermaid
flowchart LR
    Write[UPDATE] --> Redo[redo 记录页修改]
    Commit[COMMIT 请求] --> Prepare[InnoDB prepare]
    Prepare --> Binlog[写入并同步 binlog 提交决策]
    Binlog --> EngineCommit[InnoDB 完成提交]
~~~

假设这一事务把 SKU-7 从 1 扣到 0，并在同一事务插入 reserve-42：

| 崩溃前的恢复决策 | 数据页可能已写入的内容 | 恢复后结果 |
| --- | --- | --- |
| binlog 中有完整、可恢复的持久提交决策，即使客户端没收到响应 | redo 可恢复未全部刷入表空间的页修改 | 保留为已提交；若仍 prepared 则完成，available=0 且有 reserve-42 |
| binlog 中没有完整、可恢复的提交决策 | redo 可能先恢复部分页修改 | 回滚未提交事务（已 prepare 的事务也因无 XID 而回滚），available=1 且无 reserve-42 |

~~~mermaid
flowchart TD
    Crash[意外退出] --> RedoRecover[redo 前滚页修改]
    RedoRecover --> Recover{恢复时的 InnoDB 事务状态}
    Recover -->|已提交| KeepCommitted[保留已提交状态]
    Recover -->|未 prepare 且未提交| Rollback[用 undo 回滚未提交事务]
    Recover -->|仍 prepared| BinlogCheck[按完整 binlog XID 检查提交决策]
    BinlogCheck -->|XID 存在| FinishPrepared[完成 prepared 事务]
    BinlogCheck -->|XID 不存在| Rollback
~~~

所以 redo 不等同于“只记录已经提交的业务行”：恢复可能先应用页变更，再根据 binlog 的提交决策完成 prepared 事务或用 undo 回滚。设置 `innodb_flush_log_at_trx_commit=1` 后，InnoDB 在每个事务提交时写并把 redo 刷入持久存储；`sync_binlog=1` 让 binlog 在提交前同步。两者共同确定这里使用的耐久性边界，但仍依赖操作系统、文件系统、控制器与设备兑现刷盘；它们不替代备份，也不保证整个磁盘或故障域丢失后还能恢复。时间点恢复还需要适用的备份和连续二进制日志。

若要看库存不变量如何在单条条件更新和幂等记录中原子成立，见[两个请求争夺最后一件库存时，怎样保证只预留一次？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)；隔离级别与 WAL 的通用概念也在[事务隔离与 WAL 能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)中。

> [!info]- 来源
> - MySQL 8.4 REPEATABLE READ 的第一次一致性读快照、普通读不加锁：[InnoDB Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html)，§17.7.2.3，核对于 2026-11-09。
> - undo 用于构造旧版本；聚簇与二级索引的记录结构：[InnoDB Undo Logs](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html)，§17.6.6；[InnoDB Row Formats](https://dev.mysql.com/doc/refman/8.4/en/innodb-row-format.html)，§17.10，核对于 2026-11-09。
> - 完整唯一键命中、gap 与 next-key 的边界以及 REPEATABLE READ 范围扫描：[InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)，§17.7.1；按二级索引排他搜索时也锁对应聚簇记录：[Locks Set by Different SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)，§17.7.3；显式事务中的 `FOR UPDATE` 锁持续到 COMMIT/ROLLBACK：[Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html)，§17.7.2.4；隔离级别与锁定语句：[Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)，§17.7.2.1，核对于 2026-11-09。
> - redo 前滚、未提交事务回滚：[InnoDB Recovery](https://dev.mysql.com/doc/refman/8.4/en/innodb-recovery.html)，§17.18.2；启用 XA 两阶段提交与 `sync_binlog=1` 后以 binlog 中完整 XID 决定恢复时完成 prepared 事务：[The Binary Log](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html)，§7.4.4；每事务 flush 的 innodb_flush_log_at_trx_commit 与复制配置的 sync_binlog：[InnoDB System Variables](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html)，innodb_flush_log_at_trx_commit，核对于 2026-11-09。
## 11. 怎样限定对象关系映射会话并排查连接池耗尽？

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

**接下来：** Session/事务决定一次数据库访问怎样借用连接；缓存则影响哪些读取到达数据库以及读到的版本新不新。见[怎样缓存数据库读取并说明陈旧窗口？](#12.%20%E6%80%8E%E6%A0%B7%E7%BC%93%E5%AD%98%E6%95%B0%E6%8D%AE%E5%BA%93%E8%AF%BB%E5%8F%96%E5%B9%B6%E8%AF%B4%E6%98%8E%E9%99%88%E6%97%A7%E7%AA%97%E5%8F%A3%EF%BC%9F)。请求截止时间与拒绝/重试预算见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - Session 的身份映射、工作单元、flush、事务边界与首次连接借用：[SQLAlchemy 2.0, Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)，示例以 2.0 API 编写；官网在 2026-11-06 同时列出 2.1.8 为当前版本、2.0.57 为 2.0 维护版本。当前版本文档见 [SQLAlchemy 2.1, Session Basics](https://docs.sqlalchemy.org/en/21/orm/session_basics.html)。
> - QueuePool、pool_size、max_overflow、等待和进程 fork 边界：[SQLAlchemy 2.0, Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)；当前版本对应的 [SQLAlchemy 2.1, Connection Pooling](https://docs.sqlalchemy.org/en/21/core/pooling.html)。
> - LIMIT 分页需要唯一排序，且不同页的排序必须稳定：[PostgreSQL 18, LIMIT and OFFSET](https://www.postgresql.org/docs/18/queries-limit.html)。
> - 每请求 Session 的 Web 模式：[FastAPI, SQL (Relational) Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)，核对于 2026-11-06。
> - QueuePool 1 槽的等待/超时复现与 flush 回滚验证使用 SQLAlchemy 2.0.44、SQLite 3.51.0；另在 PostgreSQL 14.24、SQLAlchemy 2.0.44 和 psycopg2 上执行本页两条读取路径，验证账户隔离、同时间戳跨页、季度边界和连接归还。
> - 归档 EF Core 示例只用于对照对象/请求作用域：[ASP.NET Core 与 EF Core 示例](../../archive/back-end/ASP.NET-Core.md)。
## 12. 怎样缓存数据库读取并说明陈旧窗口？

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

**接下来：** ORM Session 与连接池决定回源数据库的借出压力，见[如何限定 ORM Session 并排查连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。高成本报表任务和故障后的确定结果见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

> [!info]- 来源
> - Redis cache-aside 的 cache-first、miss 回源、TTL 与更新失效：[Redis cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/)，核对于 2026-11-06；该页将 TTL 描述为受限陈旧窗口，跨数据库一致性方案属于应用设计。
> - Redis 的 SET 过期参数、DEL、TTL 与锁机制：[Redis Commands](https://redis.io/docs/latest/commands/)；按 Redis 官方当前文档核对于 2026-11-06。
> - 释放租约时比较锁 token 并原子删除，避免删除其他持有者的锁：[Redis Distributed Locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)；该页也列出 Redis 8.4 的 `DELEX ... IFEQ` 与较早版本 Lua 写法。
> - 报表展示的失效竞态、主体授权与 job 状态读取边界是本章应用设计；没有部署 Redis 服务做在线故障测试。
## 13. 单库接近容量上限时，怎样分片并在搬迁中保持唯一写入者？

**案例：** 合成报表服务保存账户的报表与作业。报表 42 属于 acct-17；列表、状态更新和幂等记录通常都按账户读取或写入。单库容量与维护窗口开始吃紧时，目标是把不同账户放到多个独立数据库，同时保证报表 42 在扩容搬迁时不会被两个数据库同时接受写入。

图里展示的是已知 account_id=acct-17 的写请求：先验证主体权限，再查 owner 与 epoch；当前所有者还会校验写入代次。若请求只有 report_id，先解析它所属的账户，再按该账户授权和查路由，不向所有分片广播。本文这张请求图只约定写入的 fencing：

~~~mermaid
flowchart LR
    Req[报表 42 写请求] --> Auth[验证 acct-17 权限]
    Auth --> Route[读取 owner 与 epoch]
    Route --> Send[请求携带目标与 epoch]
    Send --> Fence{请求目标、所有者状态与 epoch}
    Fence -->|epoch 匹配且开放| Work[在当前所有者执行写事务]
    Fence -->|epoch 不匹配| Reject[stale-route，刷新路由]
    Fence -->|epoch 匹配但暂时关闭| Retry[暂时拒绝，可重试]
~~~

迁移由控制流程负责取得可衔接的快照与日志坐标、收口旧写入和切换所有者：

~~~mermaid
flowchart TD
    Snap[取得一致快照及日志坐标 S] --> Backfill[把快照回填到 D]
    Snap --> Retain[保留 S 之后 acct-17 的已提交 CDC]
    Backfill --> Replay[按源端顺序应用 acct-17 的变更]
    Retain --> Replay
    Replay --> Gate[停止接收新 B 写入，收口已开始事务]
    Gate --> Freeze[B/7 冻结事务取得 ownership 锁并提交]
    Freeze --> L[记录冻结提交后的源日志位置 L]
    L --> CatchUp[D 从已应用坐标续追 acct-17 数据至 L]
    CatchUp --> Verify[D 追到 L 并核对]
    Verify --> Switch[目录条件切换为 D/8]
    Switch --> Open[D/8 开始接收写入]
~~~

路由只回答“数据在哪个分片”，不替代授权。每次写入仍须校验当前主体能否访问 acct-17 的报表；若只带 report_id，先解析资源所属账户再授权。迁移要解决的是写所有权、数据追平和陈旧路由，不是改变这项权限判断。

### 先决定哪些操作必须待在同一个分片

shard key（分片键）是把记录归到某一分片的稳定字段。本例选 account_id：按一个账户列出报表、查询幂等结果和更新作业状态时，都能从请求中的账户键直接路由到一个分片。报表 42 和同账户的作业记录留在一起，账户内事务仍是单库事务。

这个选择也带来约束：若一张表的唯一键只在账户内唯一，账户键应包含在唯一索引或业务写入范围里；跨账户全局唯一编号需要独立分配器、可验证的命名空间，或调用方提供足够大的唯一键。不能把每库各自的 UNIQUE 误当作全局唯一。

分片与复制解决不同问题。分片把不同键的主数据分布到多个数据库以增加总容量；复制让同一数据有多个副本，可用于故障恢复或读取扩展，但不会自动把单个热账户的写入摊开。复制副本是否可读、读到多旧、主副本如何选举，仍是单独的复制契约。

若请求只携带 report_id，而路由需要 account_id，服务必须先从目录查所属账户，或把稳定路由键编码进 ID；不能为了查一个路由而无条件向所有分片广播。任意跨账户搜索会变成 scatter-gather（散播后汇总）：查询扇出到多个分片，再合并结果，尾延迟和失败面都随参与分片增加。跨分片事务也不能依赖单个 SQL COMMIT：要接受分布式协调成本，或重构业务边界并使用可恢复的分步流程。通用隔离、复制与两阶段提交的边界见[事务隔离与 WAL 能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 固定取模为何在加节点时大幅搬家？

先用一个可手算的合成哈希说明映射成本：令 h(acct-n) = n，分片编号从 0 开始；这只是教学输入，不是生产哈希算法。三个分片时，余数 0、1、2 分别映射到 A、B、C；加入 D 后变成四个分片，余数 0、1、2、3 分别映射到 A、B、C、D。

~~~text
账户   h(key)   % 3 的路由        % 4 的路由
17       17      17 % 3 = 2 -> C   17 % 4 = 1 -> B
20       20      20 % 3 = 2 -> C   20 % 4 = 0 -> A
21       21      21 % 3 = 0 -> A   21 % 4 = 1 -> B
35       35      35 % 3 = 2 -> C   35 % 4 = 3 -> D
49       49      49 % 3 = 1 -> B   49 % 4 = 1 -> B
52       52      52 % 3 = 1 -> B   52 % 4 = 0 -> A
65       65      65 % 3 = 2 -> C   65 % 4 = 1 -> B
70       70      70 % 3 = 1 -> B   70 % 4 = 2 -> C
82       82      82 % 3 = 1 -> B   82 % 4 = 2 -> C
~~~

这组九个账户中八个换了目的地。因为除数从 3 变成 4，同一键重新取模后可能得到不同余数；余数没变时仍指向原来的分片，acct-49 的余数都为 1，所以仍在 B。固定取模计算便宜、映射简单，适合分片数长期稳定或能整体重建数据的系统；若直接增加数据库就要求搬迁大量键。

consistent hashing（一致性哈希）把节点和键映射到一个循环哈希空间，每个键归给顺时针遇到的第一个节点。以下把哈希值直接写作 0 到 99 的玩具圆环；环上点位是人为给定的已哈希结果，方便逐个核算，不是生产哈希函数。

~~~text
初始节点 token（环上位置）：A=0，B=33，C=66；越过 99 后回到 A=0
加节点后：     A=0，D=20，B=33，C=66
区间约定：      前一 token 不含，当前 token 含；点位相等时归当前 token

账户点位   加节点前    加入 D=20 后
17            B             D
20            B             D
21            B             B
35            C             C
49            C             C
52            C             C
65            C             C
70            A             A
82            A             A
~~~

D 接管旧 B 区间中从 A=0 到新 token D=20 的点，区间为 (0, 20]，端点 20 归 D。acct-17 因此从 B 搬到 D；另外只有 acct-20 也移动。两种方案使用同一组九个账户：固定取模搬 8/9，一致性哈希环搬 2/9。这个小样本只演示映射差异，不能作为负载均衡测量；真实数据若集中在一个区间，迁移比例也会偏离均匀期望。

virtual node（虚拟节点）让每个物理节点在环上拥有多个 token，通常能减少少量节点时的区间大小偏差，并让扩容时只搬新节点负责的若干范围。它不能解决一个 acct-17 本身压垮单节点的问题：同一账户仍映射到同一所有者。若拆出该账户内部的报表或事件键，点查与写入可能分散，但账户汇总和跨子键事务也会跨分片。热点须由访问限额、独立租户容量、缓存或改造业务分区键解决，不能只增加 token。

range partitioning（范围分区）按账户 ID、时间或其他有序键的区间分配，适合范围扫描、局部排序和按范围归档；连续新键或单调递增时间可能把热点压到边界分片，范围变更还要重新平衡。哈希分片更容易均匀地点查，却会打散按键范围的局部性。选择要从主要访问路径、事务范围和热点分布推出来，而不是只看各分片行数。

### 复制数据时怎样保持一个写所有者？

用 acct-17 从 B 搬到 D 的一次迁移定义明确合约。每个账户路由目录记录 owner、epoch（路由代次）和状态；每个写入都必须经能执行代次 fencing（栅栏拒绝）的写入口，不能允许业务服务绕过路由直连任意分片。epoch 单调增加，旧值永不复用。

| 阶段 | 路由与数据状态 | 业务写入结果 |
| --- | --- | --- |
| 稳定期，epoch 7 | 目录指向 B；D 没有 acct-17 的权威副本 | B 接受 epoch 7 |
| 快照回填，坐标 S | B 继续服务；一致快照包含 acct-17 截至 S 的业务数据提交，D 回填账户数据并保留 S 之后该账户的 CDC 增量，回填完成后按提交顺序应用 | B 接受业务写；D 只应用 acct-17 业务数据复制，不接业务写 |
| 停止接收新写 | 写入口不再准入新事务；已经准入、尚在等待 ownership 锁的事务仍可能排在冻结事务之前并先拿锁提交，迁移会等它们结束 | 冻结事务取得锁前，先取得该锁的旧写可提交并计入后续 L；暂停期新请求可重试 |
| 冻结 B/7，取得 L | 迁移事务取得与业务写相同的 ownership 行锁，标记 B/7 冻结并提交；L 是冻结提交后的源日志位置，覆盖此前所有已提交业务写；D 从自身最后应用位置续追至 L 的 acct-17 业务数据并核对 | 冻结提交后才取得锁的旧写看到 frozen 并中止；从此没有分片可提交业务写 |
| 路由已切 D/8，目标未开放 | 目录条件更新 B/7→D/8；B 保持冻结，D 尚未开放写入口 | D/8 请求暂时拒绝、可重试；B 上的本地冻结状态也可暂时拒绝，客户端刷新目录后改发 D/8 |
| D/8 开放 | D 的 ownership 行和写入口接受 epoch 8；新路由读也指向 D | 只有 D 接受 epoch 8 |

快照坐标 S 表示快照已经包含 acct-17 截至 S 的所有业务数据提交；D 只保留和应用位置在 S 之后的 acct-17 业务变更，不会复制其他账户的数据。源日志坐标可能因其他账户的写入继续前进，但它们不属于本次回填。ownership 状态是迁移控制记录，不作为 B 的业务数据复制到 D；切换时由控制流程单独把 D 的权威状态设为 D/8。每笔业务写先锁定并核对 B 的 ownership 行，再在同一事务改账户数据；停止新写入口后，已准入但尚在锁队列的事务仍可能先于冻结事务取得锁并提交，也会纳入 L。冻结事务拿到该行锁并提交后，后取得锁的旧事务看到 frozen 而中止。D 在回填后已从 S 之后逐步应用部分增量；冻结后只需从自身最后应用位置按源端顺序续追 acct-17 业务数据到 L，不会重复应用整个 (S, L]。请求中的目标分片与 epoch 必须和权威 owner 状态匹配；路由缓存只提供位置提示，不能作为写授权或 fencing。

表中的“新路由读改到 D”只指目录切换后按新 owner 查询的读；本写入协议不声称能拦截仍使用缓存 B/7 的读，也不保证这种旧路由读的新鲜度。

只有能核对权威 owner/epoch 的入口发现请求目标或代次不匹配时，才返回 stale-route（路由过期），客户端再取目录并按稳定幂等键重试。若被冻结的 B 只看见本地 `B/7/frozen`、无法核对当前目录，它可以只返回暂时不可用；客户端随后刷新目录。epoch 匹配但 owner 尚未开放时同样返回可重试暂停，不把冻结误报成路由过期。非幂等操作超时后不能盲目重放；必须先查询结果或使用本地唯一操作键。刷新路由也不能跳过每次请求的授权检查。

此合约选择“复制追平 + 短暂写屏障 + 单写者切换”，没有让应用同时双写 B 与 D。若切换后发现校验或路由错误，只有 D 从开放 epoch 8 写入口以来没有提交过业务写入，才能走快速回切：先冻结 D 的写入口并排空已开始的事务，再核对截至冻结点的 D 端提交记录；确认没有 epoch 8 业务提交后，保持 D 继续冻结，条件更新目录从 D/8 切回 B/9，再开放 B。核对与目录切换之间不能重新开放 D，否则会出现检查后又产生新提交的竞争。epoch 递增是为了让持有 epoch 7 或 8 的旧调用都失效。D 一旦提交过业务写入，直接切回旧 B 会丢失这些新提交。此时只能先把 D 的新变更可靠地反向追到 B，再在另一道屏障下切回更高代次，或保持 D 为权威并向前修复。仅保留一份旧快照不构成可回滚数据。

Vitess 的公开 resharding 流程也把复制、追赶、校验和切换流量分开；本章的 epoch 与拒绝条件是一个帮助说明唯一写所有者的教学合约，不代表任何数据库开箱即有此机制。生产实现必须明确由哪一层执行 fencing、读写屏障如何与在途事务同步，以及切换后回滚数据从哪里来。

若要继续看单库里的写冲突如何收口，可读[两个请求争夺最后一件库存时，怎样保证只预留一次？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)；事务隔离与预写日志见[事务隔离与 WAL 能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - 一致性哈希环、token 区间、加入节点时只影响邻接范围、虚拟节点缓解区间负载偏斜：[DeCandia 等，Dynamo: Amazon’s Highly Available Key-value Store，SOSP 2007](https://cdn.amazon.science/ac/1d/eb50c4064c538c8ac440ce6a1d91/dynamo-amazons-highly-available-key-value-store.pdf)，§4.2，pp. 199–200；本文取模和 token 数值为合成教学输入，不复述论文中的生产参数。
> - 新分片先复制、校验并追平，切换时暂停写入：[Vitess 25.0 Sharding](https://vitess.io/docs/25.0/reference/features/sharding/)，Resharding，页面更新于 2026-04-14；本文的 epoch、写屏障和回滚条件是用于证明单一写者的示例合约，不声称 Vitess 文档提供完全相同的 fencing API。
## 14. 请求超时后如何确认结果并安全重试？

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

HTTP 202 Accepted 是另一种显式状态：API 确认任务已受理，但没有表示已完成。账户报表契约没有按幂等键查询的 GET；若 202 响应丢失，客户端用相同 `report-demo-208` 和相同请求正文重放 POST，服务返回已存在的 `job-demo-731` 与状态 URL，再 GET 该已知 URL。连接断开不会自动取消已经持久接受的 job；需要取消时使用明确的取消请求。完整作业生命周期见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

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

**接下来：** 账户报表把幂等键、202、outbox 和后台尝试组合成一个可长期查询的流程，见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。队列发布确认与消费者 acknowledgement 的 broker 语义归[发布者确认和消费者确认分别证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)，连接借用预算归[如何限定 ORM Session 并排查连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。

> [!info]- 来源
> - HTTP 幂等方法与 202 受理语义：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§9.2.2、§15.3.3，核对于 2026-11-06。
> - 副作用、超时、重试安全与请求令牌：[AWS Builders’ Library, Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)，核对于 2026-11-06。
> - timeout、backoff 与 jitter：[AWS Builder Center, Timeouts, retries, and backoff with jitter](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter)，原文 2019-12-05，核对于 2026-11-06。
> - deadline 传播和协作式取消：[gRPC Deadlines](https://grpc.io/docs/guides/deadlines/)，核对于 2026-11-06；具体行为仍取决于各 API。
## 15. 怎样设计一个可持久查询的账户报表？

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


数据库提交与队列发布是两个系统的写入，不能放进一个普通数据库事务。若先提交 job 后直接发布，进程可能在两步之间崩溃，导致永远无人处理的任务；若先发消息再提交，数据库回滚后队列会出现不存在的任务。outbox 把 job 和待发布记录一起提交；relay 读取并重试发布，只有按所选 broker 的契约验证发布确认、路由与所需持久性条件后才更新 outbox。relay 若在 broker 接收后、更新 outbox 前崩溃，可能再次发布，所以 worker 按 job ID 幂等领取；已确认的 outbox 行也要按保留策略清理。发布者确认和消费者 ACK 是两个独立边界；即使 relay 记录 `published`，worker 也可能已经领取任务甚至写入终态。数据库事务不覆盖 broker，也不覆盖对象存储。[队列确认页](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)详解 broker 语义。

> [!example] job-demo-731 的一次正常完成
> 在这个明确的顺序示例中，relay 先验证所选 broker 契约并更新 `outbox=published`，之后 worker 才领取；因此这一时刻 `job=queued`、等待槽占用 1。worker 原子领取后，job 变成 `running`、attempt=1，等待槽归还。worker 写私有对象并提交结果引用后，job 才变成 `succeeded`；消费者随后按 broker 契约确认消息。真实系统中 worker 可能在 relay 更新 `published` 前就已领取，因此 outbox 状态、job 状态和消费者确认不能互相推导。

### 工作进程重试怎样避免旧结果覆盖新结果？

worker 领取任务时，以条件更新检查状态仍为 `queued`，递增 attempt 并设置有界租约，同时释放这个排队轮次的等待槽。另一个当前 attempt 仍持有任务时，重复投递不能另起并行工作，应按所选队列契约延后或确认重复消息。worker 崩溃后，恢复器用数据库当前时间检查 `lease_expires_at`，再按 `job_id` 和 attempt 做条件接管：先检查 `cancel_requested`；若已请求取消，直接写 `cancelled`，无需争用槽位。否则只有恢复任务取得一个新的共享等待槽，才能在同一数据库事务中把 job 改回 `queued` 并写入新的 `pending` outbox 发布意图；relay 持续重发该意图直到满足选定 broker 契约。若无槽，写入可查询的 `capacity_exhausted` 终态，但不能把已取消任务写成容量失败。该闭环确保只改 job 行不会让消息凭空重新可达；新旧重复消息都由条件领取规则消重。

attempt fencing（尝试号栅栏）以单调递增的 attempt 号隔离新旧 worker；每次 attempt 用不同、只创建一次的对象键，例如 `reports/job-demo-731/attempt-2.csv`。先将私有对象写入该键，再用 compare-and-set（比较并交换，CAS）条件更新，比较 `job_id`、`status='running'`、当前 `attempt` 和 `cancel_requested=false`。只有恰好更新一行，才提交 `succeeded` 和对象引用并让结果对用户可见；零行表示接管、取消或终态已先提交。worker 不以 `lease_expires_at` 到期时刻单独拒绝自己，胜负由这些持久条件更新的提交顺序决定。对象写入与数据库仍是两个持久系统；上传后进程崩溃可能留下未引用对象，但垃圾回收不能只按“当前无引用”立即删除：只有 attempt 已被接管或 job 已终结、数据库确认无引用，并且有上界的上传时限和额外安全宽限都已过去，才可回收。即使已失效的旧 worker 仍晚到上传，其对象也不能获得有效结果引用；后续清理仍需处理这类迟到的孤儿对象。S3 的 `If-None-Match: *` 是一种防止同名对象被覆盖的条件写法；本设计依赖的是“每次尝试使用不同键，且仅由数据库当前 attempt 引用”，并不要求选 S3。

具体时序：worker A 领取 attempt 1 后停顿，租约到期但恢复器尚未接管；此刻 A 仍可能先提交成功。若恢复器先提交接管事务，job 变回 `queued` 并新增 outbox 意图，随后 B 领取 attempt 2；A 再恢复时，`WHERE attempt = 1 AND status = 'running'` 更新零行，不能引用自己的对象。若 B 已发布结果引用，A 的不同对象键也不能覆盖它。对象是否可见由数据库当前 attempt 的条件提交决定，租约到期时间本身不作栅栏。

取消只是请求停止，并非证明计算已停止。API 将 `cancel_requested=true` 持久化；若 `queued` 任务仍占有当前排队轮次的槽位，API 可用条件状态转移将其置为 `cancelled` 并释放该槽，之后到达的重复消息只按权威终态处理。领取与取消若同时竞争同一行，条件状态更新决定唯一结果：取消先提交时，worker 不能再领取；领取先提交时，任务转为 `running`，worker 随后检查取消标志。若 `running` 任务收到取消后 worker 崩溃，恢复器过期接管时先写 `cancelled`，不会重新排队或因槽位不足写容量失败。运行中的 worker 还要在有界数据页之间以及发布结果前检查。worker 的完成更新与取消终态更新都比较当前 attempt 和取消字段：如果取消先提交，当前尝试不再能转为成功；若成功终态先提交，后到的取消请求返回当前终态。浏览器断开只结束连接；202 已持久接受的 job 会继续，只有向 `DELETE /v1/jobs/{id}` 显式请求取消才改变任务状态。202 之前尚未被接受的请求级工作可以在断开后结束。

### 何时应排队，怎样设容量边界？

若代表性报表稳定满足调用方截止时间和尾部时延目标，同步接口更简单：校验输入、执行有界查询、返回 CSV，无需 queue、outbox relay、worker、状态轮询和结果清理生命周期。任务可能超过请求预算、必须在断连后可查，或突发流量需要与 API 执行隔离时，才选择异步路径。队列能保存等待和隔离故障，但不会凭空增加处理能力。

沿用[容量与背压页](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)的估算：64 个 worker 槽、准入目标 7 次/秒、30 个任务的短时突发，以及共享上限 240 个已接受未开始任务；应用连接池总上限是 200。若把峰值 20 次/秒持续按平均 6 秒处理，平均需要约 `20 × 6 = 120` 个并发 worker；64 个槽不能长期消化该到达率，因此准入规则要限流/拒绝，等待队列也不能无界增长。未开始任务包括 outbox 中尚未发布的任务。若 broker 暂时不可用，已接受任务仍占槽；槽已满时 API 必须在 **202 之前**返回过载错误。数据库不可用时无法持久接受任务，也不能声称已受理。

> [!info] 用平均到达率估算并发，不等于压测结果
> Little's law（利特尔法则）给出稳态关系：平均在途任务数约等于平均到达率乘以平均处理时长。若 20 次/秒持续到达且每项平均 6 秒，`20 × 6 = 120` 是近似并发需求；它不包含长尾、突发与失败重试，不能替代压测和限流。

部署与运行时保留以下检查：API、relay 与 worker 的任务表结构兼容，使升级期间旧任务仍可完成；按本例分开的 7 天结果与终态后 14 天状态/幂等元数据策略清理；限制重试数、对象上传时长和每次工作时长；监测 API 接受时延、pending outbox 的最老等待时间、数据库中最老 `queued` job 年龄、broker 最老消息年龄与深度、活跃 worker 槽、任务完成分位数、连接池等待与 SQL 耗时、对象存储用量、重试、取消和终态结果。broker 队列指标正常不能证明数据库中没有积压；`pending outbox` 或 `queued` 年龄持续增长都表示处理路径跟不上。发布时保留回滚路径，并考虑已经按旧 schema 接受的任务。


**继续阅读：** [数据库约束与索引](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F)说明唯一键与查询路径；[事务隔离与 WAL](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)说明数据库内提交边界；[数据访问与连接池](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)说明每个请求/attempt 的 ORM 与连接生命周期；[HTTP 协议与 WebSocket](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F)说明客户端状态查询的传输边界；[可观测性、服务目标与事件响应](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)说明阶段指标。更长的设计检查清单见[AI 系统设计案例](../../ai-engineering/systems/ai-system-design-interview-questions.md)。

> [!info]- 来源
> - `202 Accepted` 表示已接受但尚未完成的 HTTP 语义：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§15.3.3，核对于 2026-11-06。
> - 同一数据库事务内的提交边界、唯一约束和并发行为：[PostgreSQL 18, Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html)、[Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) 与 [Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，核对于 2026-11-06。
> - 数据库与消息通知的双写故障、outbox 重复发布及消费者幂等：[AWS Prescriptive Guidance, Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)，核对于 2026-11-06。
> - 发送端 publisher confirms 与消费端 acknowledgements 是两个独立边界；RabbitMQ 的 unroutable/持久消息行为：[RabbitMQ 4.4, Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)，核对于 2026-11-06；本架构只要求按最终选择的 broker 契约确认。
> - 按对象名防止覆盖的条件写入示例：[Amazon S3, Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)，核对于 2026-11-06；S3 只是可选实现。
> - 从需求、约束与运行目标选择架构：[Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework)，核对于 2026-11-06。
## 16. 报表任务的发布确认、消费者确认与业务完成各证明什么？

账户 acct-17 为 report 42 发起导出时，请求幂等键为 report-demo-208，并在 application programming interface（应用程序接口，API）的数据库事务里创建 job（任务）job-demo-731 和 outbox（事务发件箱）行，同时预留一个等待槽。这里的等待槽是数据库维护的排队准入额度，不是 RabbitMQ prefetch 或 BullMQ lock：每个尚未领取的逻辑排队轮次占一个槽，接管重排时重新预留，领取时归还，重复 delivery 不增槽。report 42 也可由只读 API 路径查询；读状态码与异步 job 的状态或结果对象提交是不同的用户结果，不能互相代替。relay（转发进程）再把工作意图发布到 broker（消息代理）。publisher confirm（发布者确认）覆盖 relay 到 broker 的接收边界；consumer acknowledgement（消费者确认，常写作 ACK）覆盖 broker 到 worker（工作进程）的交付处理边界；job 的 succeeded 状态和私有对象引用才是应用对用户作出的业务完成记录。

~~~mermaid
sequenceDiagram
    participant A as API / database
    participant R as Outbox relay
    participant B as RabbitMQ broker
    participant W as Report worker
    participant O as Private object storage
    A->>A: 同事务写 job + pending outbox + 预留一个数据库排队额度
    R->>B: mandatory 发布载荷 {job_id=job-demo-731}
    alt 消息不可路由
        B-->>R: basic.return（关联本次发布）
        B-->>R: publisher confirm ack
        R->>A: intent 保持 pending，修复路由后再试
    else 到达已验证的目标拓扑
        B-->>R: 无关联 return + publisher confirm ack
        R->>A: 仅标记对应 intent 为 published
        B->>W: 投递 job ID
        W->>A: 只对 queued 条件领取；attempt + 1；释放等待槽
        W->>O: 上传 attempt 隔离的临时对象
        W->>A: 条件提交 succeeded + object key
        A-->>W: 事务提交
        W->>B: consumer ACK
    end
    Note over R,B: confirm 丢失时 relay 可能重发；confirm ack 本身不表示已路由
    Note over W,B: commit 后 ACK 丢失时消息可能重投
    Note over R,W: 实际 delivery 可能早于 outbox 的 published 回写；published 不是 worker 条件领取的前置状态
~~~

图中的两条回路是分布式系统的正常不确定区间：网络故障可能让一方已完成操作、另一方却没收到确认。持久 outbox 避免应用数据库提交与 broker publish（发布）的双写空档；幂等业务更新负责接住重复消息。没有共享的分布式事务时，不应把这称作 exactly-once（恰好一次）。

### 发布者确认只回答 broker 是否接收

publisher confirm 覆盖 publisher（发布者）到 RabbitMQ 的通信。它不知道 worker 是否已收到、确认或完成消息。如果 broker 接收了 publish，但 confirm 在网络中丢失，relay 无法区分“broker 未收到”和“broker 已收到但回复丢失”，重发便可能为同一 job 产生重复载荷。outbox 每次调度意图有独立唯一 ID，relay 用这个 ID 更新相应的发布状态；消息载荷只需 job ID。

confirm 的含义还受消息和 queue（队列）类型影响。RabbitMQ exchange（交换器）通过 binding（绑定）把 publish 路由到 queue（队列）；publisher confirm 不是路由保证，消息被 exchange 接受并不一定已进入预期 queue。mandatory 发布要求不可路由消息以该次 publish 的 basic.return 返回，应将它与 publisher confirm ack 联合判断：4.4 中不可路由消息会先 basic.return、再收到 confirm ack，因此“有 confirm ack 且没有关联 return”才能说明至少路由到了某个 queue。它仍不证明该 queue 是业务目标；exchange、binding 和备用 exchange 必须按明确拓扑预先验证。若 routing contract 由其他 broker/机制保证，则按该契约检查路由结果。durable message/queue（持久消息/队列）与副本类型也决定 broker 按什么配置确认承担责任；不要把另一种 queue 的保证套用过来。

outbox relay 可以按此顺序推进：读取一条未发布 outbox 意图，发布它所指向的 job ID；只有所选路由契约通过（例如 mandatory publish 已收到 confirm ack，且没有关联的 basic.return）后，才标记这个 intent 自己的 outbox 行已发布。confirm 状态未知或出现 return 时保留意图并报告发布/路由故障，修复后重试；重复 publish 可能得到相同逻辑 job 的消息，RabbitMQ 不在这里替应用去重。数据库事务和 RabbitMQ 事务不是一个原子事务；重复消息可接受的前提是 consumer（消费者）按持久 job 状态幂等处理。账户报表如何把 job、outbox 和等待槽同事务提交见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 消费者在业务结果持久后才 ACK

给 job-demo-731 的 delivery（消息投递）载荷只带稳定 job ID，不带 attempt。worker 只对数据库中的 `queued` 状态且 `available_at` 已到的任务做 conditional claim（条件领取）：在同一数据库事务中把状态改为 `running`、生成新的 attempt（尝试号）并释放等待槽。若当前 job 行还没有此字段，支持延迟重试时就在该行持久增加 `available_at`；初次排队的时间可立即到期，重试则以数据库时间判断。重投消息只是查询权威 job 的线索，不能自己生成 attempt。

先区分领取时遇到的重复 delivery：

- `queued` 且 `available_at <= clock_timestamp()` 表示排队轮次已到可领取时间，worker 可竞争条件领取；只有一个事务能领取成功。若 `available_at` 仍在未来，旧轮次早到的重复 delivery 不能提前启动 attempt；只有在后续 outbox/定时发布已持久安排到期唤醒时才可 ACK，否则应延后或不 ACK。
- `running` 且租约未过期表示已有当前 attempt，重复 delivery 不能另起并行工作。因为本例有持久租约恢复器，数据库能在过期后条件接管、重新预留槽并写新 outbox；因此确认该恢复路径持续运行后，可 ACK 这条重复消息。若没有独立且持久的恢复路径，就延后或不 ACK，不能单凭 `running` 丢掉唯一唤醒消息。
- 已持久终结的 `succeeded`、`failed` 或 `cancelled` job 不再需要这条 delivery，可 ACK。
- `running` 已过期也不表示当前 worker 可以自助领取新代次。租期到期只让数据库恢复器有资格尝试接管；它必须先赢得条件更新，再把任务改回 `queued`、预留新槽并写入新的 outbox intent。随后消息唤醒的 worker 才能领取新 attempt。

attempt 来自数据库的胜者更新，不能信任可能重复、延迟或过期的 queue message（队列消息）。结果对象写入后，只有当前 attempt 的条件更新提交 `succeeded` 和对象 key，才向 broker 发 consumer ACK。用户读取结果仍要经 API 做授权，不能因 message 已被 ACK 就把对象公开。

成功条件必须把当前状态、attempt 和取消请求一起放进更新谓词，且对象已经写好后才提交：

~~~sql
UPDATE report_jobs
SET status = 'succeeded', result_object_key = :object_key
WHERE job_id = :job_id
  AND status = 'running'
  AND attempt = :attempt
  AND cancel_requested = FALSE;
~~~

若更新一行，先提交事务，再 ACK。**完成 UPDATE 返回零行是另一条分支，不能与“领取时收到重复 delivery”混为一谈。** worker 重新读取权威 job/outbox：若已是 `succeeded`、`failed` 或取消终态且清理策略已持久，当前 delivery 已无待办工作，可 ACK。若恢复器已把旧 attempt 持久转为 `queued`，且槽位与新 outbox 意图同事务提交，旧 delivery 可 ACK；relay 只会在其 `available_at` 到期后发布，早到消息也不能越过领取时间条件。若后继 worker 已把状态领取为更大的 `running` attempt，则只有在该 claim 已提交且租约恢复路径独立持久时才 ACK 旧 delivery。恢复器的接管尚未提交、或仍为 `queued` 但新 outbox/槽位尚未持久时，不能 ACK；若当前 attempt 仍在运行且恢复器不能保证后续重排，也不能 ACK。只有 `cancel_requested` 尚未写成持久取消终态时，不能把旧 worker 的失败返回或已上传对象当作成功；应完成取消状态和清理/保留策略，或交给有持久保证的恢复流程，再按 broker 契约 ACK。

| 失败时点 | broker 可能采取的动作 | 应用要保持的条件 |
|---|---|---|
| broker 已接收 publish，confirm 未到 relay | relay 重发，同一 job ID 可能有多条消息 | 对当前持久 job/attempt 的完成更新只能有一个赢家 |
| worker 在持久结果前崩溃，delivery 尚未 ACK | RabbitMQ 连接或 channel 关闭后可重新排队未 ACK delivery | 重投仅触发读取权威 job；有效租约内不能另起 attempt，过期后仍须等恢复器条件接管并持久重排 |
| 数据库已提交 succeeded，worker 发 ACK 前崩溃 | delivery 可再次到达另一个 worker | 后继 worker 查到 job 已终态/attempt 已失效，不得重复业务副作用，再 ACK 重复消息 |
| worker 先 ACK，再提交结果前崩溃 | broker 可删除这条 delivery，不会再因它自动重投 | 若没有独立的持久恢复扫描，job 可能滞留；canonical 报表设计由数据库租约恢复器条件接管并通过新 outbox 重排，因此该恢复依赖数据库而非 broker |

若成功提交了对象但数据库事务未能提交，可能留下不可见的孤儿对象；以 attempt key 命名并在无引用、任务终态和宽限期满足后清理。若数据库已提交成功但 ACK 丢失，重复 handler 应通过终态 job、attempt fencing（尝试栅栏校验）或 operation key 得到“已完成/重复”而不是再次发布或覆盖结果。数据库提交、ACK 与恢复器抢占的状态谓词由 report job 设计章负责，本篇只解释 broker 交界。

### 重试、并发窗口与顺序会改变负载

RabbitMQ 4.4 使用手动确认时，未确认 delivery 在其 channel（通道）或 connection（连接）关闭后可自动 requeue（重新排队）；这是 RabbitMQ 的行为，不能无条件推广到所有 broker。automatic acknowledgement（自动确认）模式在发送后就视为已交付，可提高吞吐，但应用还没处理就断线时会失去工作。对需要可靠完成的报表任务，选择手动 ACK 并把 ACK 放在业务持久化之后；若依赖数据库租约扫描恢复被提前确认的任务，要把恢复器视为独立的正确性机制。

RabbitMQ 4.4 的 consumer prefetch（消费者预取上限）默认按单个 consumer（消费者）计算，而不是整个 channel（通道）：例如一个 consumer 设 prefetch=4，就最多有四条它自己的 delivery 未 ACK；同一个 channel 上若有三个 consumer，总数可以达到 12。RabbitMQ 4.3 起全局 per-channel QoS 已弃用且默认禁用。prefetch 同时影响 worker 的并行量、进程内排队和内存，不应设置为无限而不评估容量。

失败重试要有边界。worker 遇到可重试的瞬时错误时，不能只把原 delivery 延迟重投，因为 job 若仍为 `running`，条件领取不会启动下一 attempt；应用须以当前 attempt 为条件，同事务持久设置 `status=queued`、`available_at=next_retry_at`、重新预留等待槽并写新的 pending outbox 意图。relay 只在 `available_at` 到期后发布；领取谓词也要求数据库当前时间已到，早到的旧 delivery 只检查状态，不能绕过退避。只有新 outbox 与重试时间都已持久后，原 delivery 才可 ACK。不可重试错误或尝试耗尽时先持久写 `failed` 终态，再 ACK。无法映射到有效 job 的格式错误消息进入可观测 dead-letter queue（死信队列，DLQ），不要无限重排。若业务要求每个账户按顺序更新，必须明确顺序的键范围，并用单一有序分区、序号条件更新或串行化保证；first in, first out（先进先出，FIFO）名称不自动保证多个 worker 的业务完成顺序。

### BullMQ 的租锁失效为什么会让任务重复执行？

另一种常见实现是 BullMQ 6.5.3：Redis 保存 BullMQ 的调度状态和 job lock；在本例中，PostgreSQL 的 canonical 报表行仍是业务状态、attempt、租期与结果引用的权威来源，BullMQ 只负责唤醒和调度。每个持久 outbox 发布意图有自己的稳定 ID，relay 用安全字符集的 UUID 意图 ID 生成 `outbox-${intentId}`，作为 BullMQ custom job ID；消息载荷仍只带 canonical job ID `job-demo-731`。同一意图重发时复用调度 ID；租约恢复写入新 outbox 意图时使用新调度 ID，避免保留中的旧 BullMQ job 阻挡合法唤醒。BullMQ 6.5.3 custom job ID 不能含冒号、也不能只由数字组成；外部业务 operation key（如 `report-demo-208:notify:v1`）不是 BullMQ job ID。job 保留期间重复添加相同调度 ID 会被忽略；移除后可再次添加，所以它仍不代替 canonical 数据库和请求幂等记录。

BullMQ worker（工作进程）领取 job 后，队列会为它持有有时限的 lock（锁），并周期续租。进程异常退出、Redis 连接中断，或 Node.js 事件循环被长时间 CPU 工作阻塞，都可能令续租错过 lockDuration；stalled checker（停滞任务检查器）发现锁已过期后，会把 job 放回 waiting 让 worker 重跑。BullMQ 文档把这类语义称为 at-least-once（至少一次），即同一 job 可能被处理超过一次。Stalled 次数上限由 maxStalledCount 控制，6.5.3 文档默认值为 1；普通处理器抛错的 attempts/backoff 与 stalled 次数上限是两条重试路径。要观察 stalled 事件并让 CPU 密集型任务及时让出事件循环。增加锁时长会延长真正崩溃后的发现时间，缩短锁又会放大调度抖动导致的重投，不能把时间配置当成业务幂等。

即使 worker 丢失 Redis 锁，它已经开始的远端请求或对象写入也不一定会停止；稍后另一个 worker 可能拿到同一 job。Redis lock 只决定 BullMQ 何时重投，不授予或撤销报表业务写权限；对同一个 job-demo-731，外部意图和结果提交仍按 canonical 数据库状态检查 `status=running`、当前 attempt、`cancel_requested=false`。该合同中租约到期只允许恢复器尝试接管，接管状态变更提交前旧 attempt 仍可能赢得条件更新；它不同于下文独立 PostgreSQL 示例的严格到期拒绝写入。触发外部效果前使用稳定业务操作键，例如请求键 report-demo-208 对应的 `report-demo-208:notify:v1`；本地 outbox 绑定 job、attempt、请求摘要和上述 canonical 状态栅栏。远端应按稳定操作键与相同请求摘要去重，并公开保留期限或按键查询：查询确认效果完成时记录完成、不再发送；结果仍未知（包括查询不可用），但远端保证该键同摘要在期限内去重时，才用同键同摘要重试；结果仍未知且没有仍有效的去重保证，或摘要不一致、期限已过时，保留未知并人工对账。写对象时则用包含 attempt 的不可变路径，只让当前有效 attempt 的数据库事务提交对象引用。一般未知结果边界见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

### SQL job 表怎样短时领取并阻止过期 worker 回写？

如果任务状态本来就在 PostgreSQL，worker 也可以直接轮询 job 表。PostgreSQL 的 FOR UPDATE SKIP LOCKED（跳过已锁行）会跳过当前被其他事务锁住的行；官方将它列作适合多个消费者竞争 queue-like（类似队列的）表的机制，不适合作为一般读取的一致视图。领取事务只负责选一行、写 running 状态、递增 attempt 代次并设 lease_until，然后立即提交。worker 在事务外执行昂贵任务；心跳只延长仍属于自己的未过期租约。

下面是可在 PostgreSQL 14+ 的 psql 会话运行的独立 SQL 合成任务演示，使用 `pg-job-demo-42`，不复用上面 RabbitMQ/报表示例的 `job-demo-731`。本例明确选择严格租期合同：到期本身就终止旧 attempt 的写权限，即使接管尚未发生；这与前述 canonical 报表合同“到期仅允许恢复器尝试接管、由状态变更提交栅栏旧 attempt”是两种不同取舍，产品实现应选定一种并贯穿使用。临时表只在当前连接中存在，退出 psql 会话后才消失。领取语句作为各自的短事务提交。写外部意图、完成和续租时，都先按稳定 job ID 锁定行，再由下一条语句使用新鲜 `clock_timestamp()` 检查状态、attempt 与未过期租约；不能让一个带时间谓词的 `SELECT FOR UPDATE` 等锁后沿用锁前判定：

> [!example]- PostgreSQL 领取、租约栅栏与外部意图
> ~~~sql
> CREATE TEMP TABLE report_jobs (
>   job_id text PRIMARY KEY,
>   status text NOT NULL,
>   attempt integer NOT NULL DEFAULT 0,
>   available_at timestamptz NOT NULL,
>   lease_until timestamptz,
>   result_key text
> );
> INSERT INTO report_jobs(job_id, status, attempt, available_at)
> VALUES ('pg-job-demo-42', 'queued', 0, clock_timestamp() - interval '1 second');
>
> CREATE TEMP TABLE job_effect_outbox (
>   operation_key text PRIMARY KEY,
>   job_id text NOT NULL REFERENCES report_jobs(job_id),
>   attempt integer NOT NULL,
>   request_sha256 text NOT NULL,
>   payload text NOT NULL
> );
>
> -- Worker A：领取提交后才在事务外计算。返回 attempt=1。
> WITH candidate AS (
>   SELECT job_id
>   FROM report_jobs
>   WHERE (status = 'queued' AND available_at <= clock_timestamp())
>      OR (status = 'running' AND lease_until <= clock_timestamp())
>   ORDER BY available_at, job_id
>   LIMIT 1
>   FOR UPDATE SKIP LOCKED
> )
> UPDATE report_jobs AS j
> SET status = 'running',
>     attempt = j.attempt + 1,
>     lease_until = clock_timestamp() + interval '30 seconds'
> FROM candidate AS c
> WHERE j.job_id = c.job_id
> RETURNING j.job_id, j.status, j.attempt, j.lease_until;
>
> -- 为了不等待 30 秒，演示中把 Worker A 的租期置为已过期。
> UPDATE report_jobs
> SET lease_until = clock_timestamp() - interval '1 second'
> WHERE job_id = 'pg-job-demo-42' AND attempt = 1;
>
> -- Worker A 已过期但 Worker B 尚未接手：严格租期检查返回 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-1', lease_until = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 1
>   AND lease_until > clock_timestamp()
> RETURNING job_id, status, attempt;
> COMMIT;
>
> -- Worker B 接手过期任务。返回 attempt=2，旧代次不再拥有提交权。
> WITH candidate AS (
>   SELECT job_id
>   FROM report_jobs
>   WHERE (status = 'queued' AND available_at <= clock_timestamp())
>      OR (status = 'running' AND lease_until <= clock_timestamp())
>   ORDER BY available_at, job_id
>   LIMIT 1
>   FOR UPDATE SKIP LOCKED
> )
> UPDATE report_jobs AS j
> SET status = 'running',
>     attempt = j.attempt + 1,
>     lease_until = clock_timestamp() + interval '30 seconds'
> FROM candidate AS c
> WHERE j.job_id = c.job_id
> RETURNING j.job_id, j.status, j.attempt, j.lease_until;
>
> -- 本例的外部操作键固定属于 pg-job-demo-42。请求摘要是该 JSON 正文原始字节的 SHA-256。
> -- Worker A 已过期；attempt 检查失败，插入 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> WITH current_attempt AS (
>   SELECT job_id, attempt
>   FROM report_jobs
>   WHERE job_id = 'pg-job-demo-42'
>     AND status = 'running'
>     AND attempt = 1
>     AND lease_until > clock_timestamp()
> )
> INSERT INTO job_effect_outbox(operation_key, job_id, attempt, request_sha256, payload)
> SELECT 'pg-job-demo-42:notify:v1', job_id, attempt,
>        'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c',
>        '{"jobId":"pg-job-demo-42","reportId":42,"type":"report.ready"}'
> FROM current_attempt
> ON CONFLICT (operation_key) DO NOTHING
> RETURNING operation_key, attempt;
> COMMIT;
>
> -- Worker B 的当前 attempt 持有未过期租约，意图只插入一次，返回 1 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> WITH current_attempt AS (
>   SELECT job_id, attempt
>   FROM report_jobs
>   WHERE job_id = 'pg-job-demo-42'
>     AND status = 'running'
>     AND attempt = 2
>     AND lease_until > clock_timestamp()
> )
> INSERT INTO job_effect_outbox(operation_key, job_id, attempt, request_sha256, payload)
> SELECT 'pg-job-demo-42:notify:v1', job_id, attempt,
>        'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c',
>        '{"jobId":"pg-job-demo-42","reportId":42,"type":"report.ready"}'
> FROM current_attempt
> ON CONFLICT (operation_key) DO NOTHING
> RETURNING operation_key, attempt;
> COMMIT;
>
> -- 同键重放必须核对正文摘要；只有 true 才是相同请求。
> SELECT operation_key,
>        request_sha256 = 'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c' AS same_request
> FROM job_effect_outbox
> WHERE operation_key = 'pg-job-demo-42:notify:v1';
>
> -- Worker A 迟到完成：先锁行，再重新读租期/代次；attempt 不匹配，返回 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-1', lease_until = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 1
>   AND lease_until > clock_timestamp()
> RETURNING job_id, status, attempt;
> COMMIT;
>
> -- Worker B 完成：先锁行，再由下一条 UPDATE 检查新鲜租期；返回 1 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-2', lease_until = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 2
>   AND lease_until > clock_timestamp()
> RETURNING job_id, status, attempt, result_key;
> COMMIT;
> ~~~

回放结果为：首次领取 attempt=1；A 到期但 B 尚未接手时，严格租期完成更新返回 0 行；之后过期接手为 attempt=2，A 的过期意图写入与迟到完成仍各返回 0 行，B 的当前意图写入和完成各返回 1 行，摘要查询为 true。前文 canonical 报表合同则允许到期至接管提交前由旧 attempt 与恢复器竞争状态写入；两者彼此独立。若租约续期写成另一个 UPDATE，也必须同时要求 job ID、running 状态、当前 attempt 匹配且旧 lease_until 尚未过期；否则已过期 worker 能在接手后再次“续活”。远端副作用仍按三种结果处理：查询确认完成则记录完成并停止发送；结果仍未知（查询不可用也算未知）但远端保证同键同摘要在保留窗内去重，才可重试原键；结果仍未知且无有效保证、摘要冲突或期限过了，就人工对账。SQL 领取避免维护独立 Redis job 状态，但会以轮询和行锁增加主数据库负担，需监控领取扫描、锁等待和空轮询。

代次栅栏只能阻止旧 worker 覆盖 job 行，不会撤回它已经发出的外部请求。worker 写本地外部意图时，必须在同一短事务锁住 job 行、校验 `status=running`、当前 attempt 和未过期租约，再写入唯一 operation_key 与请求摘要；冲突时读取既有行，摘要相同才可视为同一意图，摘要不同则隔离处理。relay 仍可能在远端成功后、写下本地发送回执前崩溃。结果未知时先按原操作键查询：查询确认效果已完成，就持久记完成并停止发送；结果仍未知但远端保证相同键、相同摘要在保留窗内去重，才可同键重试；结果仍未知且没有仍有效的同键同摘要去重保证、摘要不符或远端保留窗已过，就维持未知并人工对账。数据库内唯一键只防止重复创建本地意图，不会自动让远端调用只发生一次。

### 观测每个交接点，不能只数 ACK

单独记录 publish 尝试、confirm/return、queue depth 和 oldest-message age、unacked 数、重投、重试、ACK、DLQ、job succeeded/failed 及对象引用提交。oldest-message age 持续增长表示结果延迟，即使队列还在接受消息。broker 继续接收并不代表 worker 有容量；worker 发 ACK 也只表示应用确认到达选择的处理边界，不等于用户后来成功下载了报告。更完整的事故定位见[如何从报表服务信号定位发布故障？](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)。

> [!info]- 来源
> - RabbitMQ 官方 [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms) 与[发布何时确认](https://www.rabbitmq.com/docs/confirms#when-will-published-messages-be-confirmed-by-the-broker)、[Reliability Guide](https://www.rabbitmq.com/docs/reliability)，checked 2026-11-06：确认方向相互独立、mandatory/unroutable 的 `basic.return` 在 confirm ack 前、手动/自动 ack、未确认消息在 channel/connection 关闭后的重排、publisher 重试与确认语义。latest release 为 RabbitMQ 4.4.0，见[官方 Release Information](https://www.rabbitmq.com/release-information)。
> - RabbitMQ 4.4.0 官方 [Consumer Prefetch](https://www.rabbitmq.com/docs/consumer-prefetch)，checked 2026-11-06：RabbitMQ 默认 false 的 QoS 标记对应每个 consumer 独立上限；global per-channel 模式在 4.3 起弃用并默认禁用。见[发布信息](https://www.rabbitmq.com/release-information)核对当前 4.4.0 版。
> - RabbitMQ 官方 [Publishers](https://www.rabbitmq.com/docs/publishers) 与 [Consumers](https://www.rabbitmq.com/docs/consumers)，checked 2026-11-06：publisher confirms、不可路由消息检测、消费者预取和并发交付。具体保证仍由已配置的 exchange、queue 类型、持久性、副本和客户端库决定。
> - 数据库 outbox、幂等键和 report job attempt 是应用级机制，见[请求超时后的结果确认](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)和[持久报表任务](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。
> - BullMQ 6.5.3 官方文档（checked 2026-11-09）：[Important Notes](https://github.com/taskforcesh/bullmq/blob/v6.5.3/docs/gitbook/bull/important-notes.md)、[Stalled Jobs](https://github.com/taskforcesh/bullmq/blob/v6.5.3/docs/gitbook/guide/workers/stalled-jobs.md)、[Retrying failing jobs](https://github.com/taskforcesh/bullmq/blob/v6.5.3/docs/gitbook/guide/retrying-failing-jobs.md)、[Job IDs](https://github.com/taskforcesh/bullmq/blob/v6.5.3/docs/gitbook/guide/jobs/job-ids.md)。这些语义适用于本段标出的 BullMQ 6.5.3；job ID 去重仍受其保留/自动移除边界约束。该版本 custom ID 还不能含冒号或仅由数字组成，因此示例使用带字母前缀的安全意图 ID。
> - PostgreSQL 14 官方 [SELECT 与锁定子句](https://www.postgresql.org/docs/14/sql-select.html) §SELECT、[显式锁](https://www.postgresql.org/docs/14/explicit-locking.html) §13.3.2，checked 2026-11-09：SKIP LOCKED 会跳过无法立即取得的行锁，适用于 queue-like 并发领取。代次/租期状态设计和远端幂等是应用层契约。
## 17. Webhook（回调通知）接收方如何验证并可靠受理？

报表 42 生成完成后，报表服务要通知另一个服务；对方可能短时不可用、响应可能在网络中丢失，请求也可能被重复发送。安全交接因此有两个独立判断：签名验证“请求是否由持有共享密钥的一方生成且字节未被改动”，持久去重“这个逻辑事件是否已受理”。单有签名不能阻止有效请求被重放，单有事件 ID 也不能证明发送者身份。

在这条路径中，发送端用 transactional outbox（事务发件箱）记录待通知事件，接收端用 inbox（收件箱）持久保存已受理事件，再异步处理。

以下采用**明确的合成 HMAC（基于哈希的消息认证码）合约**，只用于教学，不兼容 Stripe、GitHub 或其他提供方的 webhook。合约定义 eventId 为稳定逻辑事件 ID，重试时不变；attemptId 是一次应用层 HTTP 投递尝试 ID，每次新发送都换一个。事件正文、签名原文字节、时间戳、字段格式、旋转窗口和重试响应都由本合约定义，不把某个提供方的规则拼进来。`v1` 是签名串格式版本，本例只定义 `report.ready` 的一种载荷形状，不另带事件 schemaVersion。所有域名、密钥和报表字段都是合成示例。

~~~mermaid
flowchart TD
    T[业务事务提交 report 42 + outbox eventId] --> S[发送端构造 attemptId、时间戳和签名]
    S -->|HTTPS + 原始正文| V[接收端验证原文、签名和时钟窗口]
    V -->|验证失败| X[4xx；不写入受理记录]
    V -->|验证成功| I[(事务写 inbox（收件箱）+ 处理 outbox)]
    I -->|提交后才回| A[202 Accepted（已接受）]
    I --> W[异步处理进程]
    W -->|稳定操作键或对账| E[外部业务效果]
~~~

图中 202 Accepted 只证明接收方已持久接受事件，不能证明异步处理或外部效果已经完成。该区别与[报表任务中发布确认、消费者 ACK 和业务完成的边界](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)相同。

### 一次通知从业务提交到签名请求怎样走？

报表完成事务同时写入业务状态和发送端 outbox（事务发件箱）行。该行保存稳定的 eventId、事件类型、签名前的完整 UTF-8 正文原字节和待发送状态；业务事务提交后 relay（转发进程）才会发送它。重试始终使用这些不可变原始字节，不重新解析和序列化，否则空白、字段顺序或数字表示变化都会改变签名输入。

本合成请求的正文如下。代码围栏中的这行 JSON 本身是完整正文，计算时不包括 Markdown 围栏，也不额外附加换行：

~~~json
{"eventId":"evt-report-42-ready-001","type":"report.ready","reportId":42,"createdAt":"2026-11-09T04:00:00Z"}
~~~

发送端将本次尝试的时间、键版本和两个 ID 放入单值 ASCII 请求头，签名覆盖这些字段与原始正文：

~~~http
POST /hooks/reports HTTP/1.1
Host: receiver.example.test
Content-Type: application/json
X-Webhook-Key-Id: demo-k2026-02
X-Webhook-Timestamp: 1794196800
X-Webhook-Event-Id: evt-report-42-ready-001
X-Webhook-Attempt-Id: att-001
X-Webhook-Signature: v1=00ddffad798719283b3f470bfdae27dafb1e4a9b3710cdc118e75a1657c29b6f
Content-Length: 108

{"eventId":"evt-report-42-ready-001","type":"report.ready","reportId":42,"createdAt":"2026-11-09T04:00:00Z"}
~~~

假设接收方已经提交事件但 202 响应丢失。10 分钟 1 秒后，发送端用同一 eventId 和完全相同的 108 个正文字节再发一次，但生成新的 attemptId、时间戳和签名。服务端当前时间假设为 2026-11-09T04:10:01Z：请求头时间代表这一次发送，正文 createdAt 仍是事件创建时间，不能拿它代替签名时钟。正文创建时间虽已超过 5 分钟，新的投递仍在时间窗内：

~~~http
POST /hooks/reports HTTP/1.1
Host: receiver.example.test
Content-Type: application/json
X-Webhook-Key-Id: demo-k2026-02
X-Webhook-Timestamp: 1794197401
X-Webhook-Event-Id: evt-report-42-ready-001
X-Webhook-Attempt-Id: att-002
X-Webhook-Signature: v1=f03542e0a28e53585db5107e10147457ae5cd8a71596dffd5dda16d06ccc650c
Content-Length: 108

{"eventId":"evt-report-42-ready-001","type":"report.ready","reportId":42,"createdAt":"2026-11-09T04:00:00Z"}
~~~

演示密钥是 synthetic-demo-secret-never-use-outside-example，不是可部署凭据。签名输入由 UTF-8 编码的合约版本、keyId、十进制时间戳、eventId、attemptId 五项 ASCII 字段组成，字段间以单个 LF（换行字节 0x0A）分隔；最后一个字段后再有一个 LF，然后直接拼接原始正文：

~~~text
UTF8("v1" + LF + keyId + LF + decimalTimestamp + LF + eventId + LF + attemptId + LF) || rawBody
signature = lowercase_hex(HMAC-SHA-256(secret[keyId], signingInput))
~~~

ID 只允许 1–128 个 ASCII 字母、数字、句点、下划线或连字符；时间戳用不带前导零的十进制 Unix 秒。HTTPS 保护传输通道；HMAC（基于哈希的消息认证码）验证请求完整性与共享密钥持有者身份，但不加密正文，也不替代接收方的事件类型、租户或资源授权检查。

### 接收方先验哪一份字节和时间？

第一步，网关设正文大小上限，应用保留 HTTP entity body（HTTP 正文）的原始字节；不能先解析 JSON、规范化后再验签。发送端不发 `Content-Encoding`，合约接收未压缩表示且拒绝出现该字段的请求；中间层不得解压、重写或重序列化签名正文。固定 HTTP/1.1 示例用 `Content-Length: 108` 标明 108 个正文八位组，长度字段不参与签名。重复或格式错误的签名头返回 400；未知 keyId 返回通用 401，与签名不匹配共用响应，避免暴露当前密钥集合。两类 401 使用同一个 `WWW-Authenticate: Webhook-HMAC realm="report-webhooks"` challenge，并带 `Cache-Control: no-store`。该 auth-scheme（HTTP 认证方案）只是本篇明确的合成私有协议名称；面向公开互操作标准化时，应发布方案说明并按 RFC 9110 注册。由于它通过自定义请求头而非 `Authorization` 携带凭据，端点所有响应均带 `Cache-Control: no-store`。

第二步，接收方按选中的密钥对精确签名输入计算 HMAC，用常数时间比较等长摘要，再检查发送时间是否在服务端当前时间的 ±300 秒内。生产时钟需同步。通过验签后，验证器从本端点服务端密钥注册表中的 `(endpointId, keyId)` 映射取得 sourceId（发送来源 ID），而不是从未经签名的来信身份字段取得它；同一发送方轮换前后的旧、新 keyId 映射到同一个稳定 sourceId。每个共享密钥只授权给一个 endpointId 与 sourceId 作用域；不同接收端点或授权域不得复用同一密钥值，因为签名原文不含 URL 或 endpointId。

第三步，解析 JSON 并验证业务授权。本合成端点只定义一种 `report.ready` 载荷形状；`v1` 仅指签名串版本，不是载荷版本。此例映射的 sourceId 只获准发送 `report.ready`，且只获准通知 report 42；检查头与正文 eventId 相同、必需字段和 UTC `createdAt` 有效，并确认签名时间戳严格早于 `createdAt` 加 30 天。未获准的事件类型或报表返回 403，不写入 inbox。发送端只在 outbox 首次提交时设置 createdAt，此后不可改写；在截止时刻前签发的有效尝试可在时间窗和最大请求时限内到达。

| 输入变化 | 本合约的判断 | 状态写入 |
| --- | --- | --- |
| 签名头重复或格式错误 | 请求结构无效 | 不写 inbox，返回 400 |
| 未知 keyId、签名不匹配或发送时间超出 ±300 秒 | 使用同一通用认证失败响应 | 不写 inbox，返回带 challenge 的 401 |
| 已验签的来源无权发送该事件类型或报表 ID | 身份已知但业务授权失败 | 不写 inbox，返回 403 |
| 已签名请求的时间戳大于或等于 event createdAt + 30 天 | 超出固定投递截止时间 | 不写 inbox，返回 410 Gone |
| 完整验证通过，`(sourceId, eventId)` 已有已提交行且摘要相同 | 已持久受理事件的重放；attemptId 不参与事件去重 | 返回重复受理 202，不新增处理意图 |
| 完整验证通过，`(sourceId, eventId)` 尚无已提交行 | 即使是时间窗内旧签名，也可能是首次到达或前次事务未提交 | 执行首次持久受理事务；只有提交后才返回 202 |
| 完整验证通过，唯一键已存在但正文摘要不同 | 同一逻辑事件 ID 不能替换载荷 | 隔离并告警，返回 409 |

认证失败响应对未知 keyId、摘要错误和时间窗错误使用相同状态、challenge 和通用正文，不把失败原因写入可外部枚举的错误字段：

~~~http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Webhook-HMAC realm="report-webhooks"
Cache-Control: no-store
Content-Type: application/problem+json

{"type":"https://receiver.example.test/problems/invalid-webhook-authentication","title":"Webhook authentication failed","status":401}
~~~

±300 秒是本合成协议为减少旧签名重放机会而选的时间窗，不是所有 webhook 的通用参数。接收方时钟偏移过大可能拒绝合法请求；发件方若误把正文 createdAt 填作请求头的发送时间戳，迟到的合法重投也会越窗。这里的发送端规则明确规定：每次新 HTTP 尝试都使用新的 attemptId、当前时间戳和签名，正文与 eventId 保持不变。真实提供方的重试签名时间规则必须按其官方协议逐项实现。

### 为什么验签后还要持久去重再应答？

持久 inbox（收件箱）以 `(sourceId, eventId)` 为唯一键，保存验签后的原始正文 `raw_body`（字节列）、正文摘要、接收时间和处理状态；处理 outbox 以外键引用该 inbox 行。异步 worker 可从数据库恢复出完整输入，不能只拿摘要后再向已返回 202 的发送方索要正文。若使用不可变对象引用代替字节列，必须在提交受理事务前保证对象已写成、可读且引用已持久；否则返回 503。已完成处理后可按保留政策删除正文，但去重摘要墓碑仍须覆盖允许的重试窗口。原文可能含敏感数据，访问与保留要受控，日志不记录原文。首次受理时，在同一个数据库事务中写 inbox 和处理 outbox：

1. 尝试插入 inbox 行，保存稳定 eventId、正文摘要、原始字节、接收时间和处理状态。
2. 若唯一键由本次事务插入，同一事务再插入待处理 outbox 行，唯一键继续使用 `(sourceId, eventId)`，意图引用 inbox 行而不复制一份可漂移的载荷。
3. 若唯一键已由此前提交的事务占用，读取持久行并比较摘要；摘要相同则返回重复受理，不再创建处理任务；摘要不同则隔离并告警，返回 409。
4. 并发首次请求由数据库唯一约束裁决：若先行事务提交，后行检查已提交正文；若先行事务回滚，另一事务可完成首次插入。不能仅凭时间窗或相同签名推断事件已受理。
5. 事务提交后才返回 202。数据库暂时不可写或正文/引用无法持久化时返回 503，发送端可重试。

这样重复投递不会产生第二条业务处理意图。HMAC 身份认证与事件去重仍是两个判断：一个经过正确验签、但已处理过的事件，要回 2xx 让发送端停止重试；一个无效签名的请求即使碰巧带有已见过的 eventId，也不能靠去重记录绕过验证。

本合成发送端把正文的 createdAt 作为固定事件创建时间，并把自动投递和人工重放的总截止时间固定为 createdAt 加 30 天；任何新尝试的签名时间戳都必须严格小于该值，等于截止时刻也算过期，Retry-After 不得延长期限。自动尝试最多 12 次；人工重放不会重置期限。接收端按已验证正文计算去重墓碑，至少保留到 createdAt 加 30 天、300 秒签名窗口、最大 HTTP 请求时限和清理余量之后。这样允许截止前签发、在协议窗口及时到达的尝试首次受理，也让已受理事件在所有允许的重试结束前保持去重记录。窗口和请求时限过后，接收端不承诺 inbox 墓碑还在；它只保证 webhook 受理去重，不保证后续外部效果不重复。

| 外部副作用结果 | 处理方式 |
| --- | --- |
| 按原 operation key（业务操作键）查询确认已完成 | 持久记录完成，不再发送 |
| 结果仍未知（包括查询不可用），且远端明确保证相同操作键、相同规范化请求摘要在保留窗内去重 | 只在该保证仍有效时，以原键和原摘要重试；保持原事件状态并继续对账 |
| 结果仍未知且没有仍有效的同键同摘要去重保证，或摘要不一致、保留窗已过 | 保持结果未知并人工对账，不换新键自动重发 |

不能用 webhook 的 30 天期限替代远端接收方自己的幂等期限；通用的未知结果与安全重试边界见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

| 崩溃时点 | 接收端的持久事实 | 后续行为 |
| --- | --- | --- |
| 首次受理事务提交前 | inbox 和处理 outbox 都不存在，不能回 202 | 合法重试进入首次持久受理 |
| inbox 与处理 outbox 同事务提交后、202 送达前 | 原正文、摘要和处理意图都已持久 | 重试先完整验签；同键同摘要识别为重复，返回 202 而不重复排队 |
| 202 已送达、worker 尚未完成 | inbox 含可恢复原文，outbox 含待处理意图 | worker 从持久输入继续；202 不代表业务完成 |
| 外部副作用可能完成、本地完成记录未提交 | 结果未知 | 按上表查询、同键同摘要有效期重试或人工对账 |

若对方需要维护事件顺序，载荷还必须有提供方定义的序号和资源范围；本合约没有定义全局或逐报表顺序，接收方不能按到达顺序推断业务顺序。

### 发送端怎样重试、停止和人工重放？

发送端把业务事件和 outbox 先提交，再由 relay 投递。收到 2xx 后，发送端将该事件的交付标为完成；连接超时意味着“可能没收到，也可能已收但响应丢失”，所以继续以相同 eventId 和原始正文重试。每次新应用层发送创建新的 attemptId，并用当前密钥、新时间戳重签；在发出网络请求前，先持久写入该 attemptId、keyId、签名时间、发送状态与 eventId 的关联。这样崩溃恢复可追踪潜在已发尝试及其 keyId；只有已持久记录的成功响应才算确认，若没有确认且无法证明请求尚未发出，一律按结果未知处理，并按同一 eventId 安全重试或对账。控制面也能按已撤销 keyId 找出受影响的未确认事件。单次 attempt 的传输层重发仍使用同一组签名头。

此合成发送端选择有限 exponential backoff（指数退避）和随机抖动：首次重试约 1 秒，逐步加倍到 15 分钟上限；最多自动发送 12 次。relay 在发送前检查当前时间，签名时间戳须严格早于正文 createdAt 加 30 天；到达或越过截止时间时停止自动和人工投递。200–299 表示接受；408、429、5xx 及传输结果不确定按重试处理。429 依 RFC 6585 不得由缓存存储，可返回合法 Retry-After；发送端只在建议的下一次发送仍严格早于固定截止时间时遵从，如果等待会到达或越过截止时间，事件转为需处理状态并停止自动发送。其他 4xx 作为契约或载荷错误进入需处理状态，不无限重试。3xx 不自动跟随，按端点或签名目标配置错误转需处理；未列出的响应也不擅自重试。实际产品要按目标服务能力、最大延迟和积压容量选值。本政策是本地合约，不是 HTTP 或各 webhook 提供方统一规定的调度。

达到自动重试上限后，持久保留原事件和失败原因，告警并等待修复。操作员只可在同一绝对截止时间前人工重放，继续用原 eventId 与正文，但生成新 attemptId 并重新签名；若先前已受理，这次就只补回确认、不重复排队；若此前从未提交收件记录，这次就是首次受理。截止时刻及之后不再发起重放。若业务需要再执行一次新动作，应产生新的逻辑事件 ID，并用 causationId 指向原事件；改掉原 ID 来绕过去重会掩盖重复副作用。

### 密钥轮换和撤销怎样覆盖在途请求？

合成协议用 keyId 选择接收方持有的密钥，并把该 ID 一起签名；旧、新 keyId 都映射到同一 sourceId。正常轮换时先把新密钥分发给接收方，让它短期同时接受旧、新两个 ID；确认接收端实例已更新后，发送端开始用新 ID 发送。此合约的 outbox 保存未签名正文，每次发送都用当前密钥即时签名，所以旧密钥的重叠期只需覆盖仍在运行的旧发送端和已经发出的旧签名请求。等旧发送端下线并记录所有旧发送实例签名时间戳的最大值；只有当每个仍可能接收旧请求的实例时钟都已晚于该最大时间戳加 300 秒，并且最大在途请求处理时限也已过，才撤掉旧密钥；不能仅从最后一次发送起等待 300 秒，因为接收端时钟可能落后，生产中还要将已知时钟偏差计入安全余量。重试积压不必继续延长重叠期。若实现把已经签名的请求预先排入队列，则须在过期前重签或等这些旧签名失效后再撤旧键。新旧密钥分别审计，不把值写进配置库以外的部署文件或日志。

若旧密钥疑似泄漏，先确认新 keyId 已预先可用，再停止旧发送端并撤掉旧 keyId。若尚无可用新密钥，立即撤销旧键并暂停该端点交付，待生成、分发和部署新键后再恢复；这段时间不能为了可用性继续接受已泄漏的密钥。旧签名请求会被拒绝；普通 4xx 策略通常将它停在需处理状态，因此部署控制面还要按被撤销的旧 keyId 查找未确认事件，将它们重新调度为新 attemptId、原 eventId 和原正文，由新密钥重新签名，但仍须通过原有的严格截止时间检查，不能因撤键重置期限。若旧请求其实已受理但响应丢失，唯一键会把新投递识别为重复；已确认 2xx 的事件保持完成，不要重放。时间窗限制签名可用时间，密钥撤销限制密钥本身；二者都不能删除已受理的 inbox 行，也不能自动撤销已经发生的外部业务效果。

### 怎样观察交接有没有卡住？

发送端将 eventId、每次 attemptId 与 keyId 的关联、目标端点标识、投递次数、响应类别、下次尝试时间和事件年龄写入受限的投递记录；接收端记录 eventId、attemptId、keyId、时间偏移、验签结果、重复命中或载荷摘要冲突，以及 inbox 到业务终态的时延。不要记录 HMAC 密钥、完整签名头、Authorization 头或原始正文；正文可能包含个人或业务数据。告警需能从一个事件 ID 追到重试和最终状态，但不把签名/正文复制到日志。

若验签错误增长，先分辨密钥版本、时钟偏移、正文是否在中间层被重写及密钥撤销时间；若签名通过但 inbox 年龄增长，瓶颈在持久处理阶段而不是认证。由此读者能知道发送端交付、接收端受理和外部业务完成是三个独立状态。

> [!info]- 来源
> - HMAC 是共享密钥和哈希函数构造的消息认证码：[IETF RFC 2104, HMAC](https://www.rfc-editor.org/rfc/rfc2104.html)，§2，1997-02；HMAC-SHA-256 的算法标识与一致性测试向量：[IETF RFC 4231](https://www.rfc-editor.org/rfc/rfc4231.html)，§3–§4，2005-12。核对于 2026-11-09。本章拼接格式、字段名、窗口、去重和重试均为明确的合成应用协议，RFC 不定义它，也不能据此声称与某一 webhook 提供方兼容。
> - 401 必须带适用的 `WWW-Authenticate` challenge，挑战用法及新 auth-scheme 注册/缓存考虑见 [IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§8.4（Content-Encoding）、§11.1、§11.6.1、§15.5.2、§16.4.1–§16.4.2；本文合成 `Webhook-HMAC` challenge 使用 `Cache-Control: no-store`。同 RFC 的 202、410 Gone 和 Retry-After 通用语义见 §10.2.3、§15.3.3、§15.5.11；429 的定义、`Retry-After` 可选提示及不得缓存见 [IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，§4。本文具体分类与次数属于合成发送端政策。核对于 2026-11-09。
## 18. 怎样用 Kafka 分区保序、推进偏移并安全接手？

**案例：** 合成报表服务为 reportId 42 产生 queued、rendered、ready 三个事件，在线投影维护当前状态；值班排查时，还要能从保留的日志重建投影。Kafka 可让同一键的记录落在同一分区并按追加顺序读取，但异步工作线程仍可能乱序写入投影；本例会把业务状态应用顺序与 offset 恢复位置分别说明，也不把 Kafka 的边界误当成外部数据库事务。

~~~mermaid
flowchart TD
    API[报表服务] -->|key=report-42| Part[report-events 的一个分区]
    Part --> Log[分区内追加日志与记录位置]
    Log --> C1[同一 consumer group 的消费者]
    C1 --> Apply[串行应用或按 seq 约束写入]
    Apply --> DB[外部数据库投影已提交]
    DB --> Prefix[推进该分区的连续完成前缀]
    Prefix --> Commit[提交前缀后的下一个 offset]
    Group[组协调器与成员代次] -->|分配/撤销分区| C1
    Replay[独立重建 group] -->|读取保留日志| Log
~~~

reportId 是分区键；本例的 API 按该键顺序发出一个报表的状态事件。主投影和重建投影使用不同 consumer group（消费者组），所以两者各自保存读取位置，不会彼此抢消息。分区数量、键到分区的映射方式和生产者的发送顺序是这个案例的输入契约。

### 哪个顺序由分区保证？

Kafka topic（主题）拆成多个 partition（分区），每个分区是独立追加的有序日志。分区内的 offset（偏移）是记录的位置；两个分区之间没有天然的全局顺序。Kafka producer（生产者）可用 key（消息键）让相同键的记录通常经同一分区计算路径发送；同一 reportId 因此可以保持同分区顺序。这个顺序是 broker（消息代理）实际追加顺序，不会自动替业务判断“哪个事件先发生”。

固定本例为三个分区、一个生产者按业务序号串行发送，并启用 producer idempotence（生产者幂等）：

~~~text
report-events / partition 0
offset 40  report-42  seq=1  queued
offset 41  report-42  seq=2  rendered
offset 42  report-42  seq=3  ready

report-events / partition 1
offset 18  report-17  seq=1  queued
offset 19  report-17  seq=2  ready
~~~

消费者组把每个分区分配给组内一个活跃消费者；例如 C1 负责分区 0 和 1，C2 负责分区 2。组外的第二个重建 group 可以独立从分区 0 的 offset 0 开始，前提是该位置仍在保留窗口内。若活跃分区数是 3，组内添加第 4 个消费者不会制造第 4 路分区并行度，它会暂时没有分区。

“相同 key”本身也有边界：增加 topic 分区数可能改变默认消息键到分区的映射，扩分区前后的同一 reportId 就可能落到不同分区。此时新分区里的追加记录不能凭 offset 自动排在旧分区已有事件之后。若业务要求跨扩容仍严格保序，应使用显式兼容的路由版本、按键迁移状态，或在消费端校验业务序号并处理断档。多生产者并发时，谁先写入分区由实际到达顺序决定；业务事件若有权威顺序，还要由上游序列号或单一写入路径表达。

### 提交的 offset 为什么是“下一个要读的位置”？

Kafka 存储的 committed offset（已提交偏移）代表恢复后要读的下一个位置。处理完 offset 40 后，提交 41；提交 40 会让恢复从 40 再读一次。概念上，提交 43 表示本例中 40、41、42 已全部完成。offset 数字不要求对应用可见的记录连续：日志压缩可移除 41；消费者使用 `read_committed` 时也看不到已中止事务的记录。因此连续前缀按实际交付的记录顺序判断，不是等待每个整数 offset。

若应用把同一分区的多条记录派给异步工作线程，完成顺序可能与提交顺序不同：

~~~text
已交付：40、41、42
工作完成：41 ✓，42 ✓，40 仍在运行
可安全提交的下一个位置：40
等 40 也完成：40 ✓，41 ✓，42 ✓
可安全提交的下一个位置：43
~~~

41 和 42 先完成，不代表 40 已经产生外部效果。此刻提交 43 会让崩溃恢复跳过仍未完成的 40。每个分区要维护“按交付顺序已完成、且没有未完成记录挡在前面的前缀”；可以串行处理，或按分区并行但只推进到最早未完成的已交付记录之前。若 poll 交付 40 和 42，而 41 已被日志压缩移除（或在 `read_committed` 下因事务中止而不可见），40 完成、42 未完成时，可提交 41 作为下一个位置；恢复从 41 扫描时会跳过缺失的记录并交付 42。此时不能直接提交批次末的 43；等 42 也完成后才可提交 43。整数缺口本身不表示工作丢失，越过仍未完成的记录才会丢失工作。

连续前缀只限制恢复位置，不会替数据库安排业务效果的先后。若 40 是 `queued`、41 是 `rendered`，并行任务可能先把 41 写成 `rendered`，再把 40 写成 `queued`；提交仍停在 40 也不能撤销已经发生的状态倒退。稳定 `event_id` 的去重只识别同一事件的再次投递，40 和 41 是不同事件，不能靠去重解决乱序。若每一步状态转换都必须执行，应按 reportId 串行应用，或并行准备数据后依业务序号顺序提交。以下另设一个只存完整状态快照的投影：已预置 `report_id=42`、`last_seq=0`（非 NULL），每条事件都携带可替代当前状态的完整快照；因此允许跳过中间状态，并用条件更新拒绝较旧序号。SQL 用命名绑定参数表示：

~~~sql
UPDATE report_projection
SET status = :status, last_seq = :seq
WHERE report_id = :report_id AND last_seq < :seq;
~~~

按本例的乱序完成次序，应用 41（seq=2）把行改为 `rendered/2`，应用 42（seq=3）改为 `ready/3`；随后应用 40（seq=1）因 `last_seq < 1` 不成立而影响 0 行，状态仍是 `ready/3`。由于旧完整快照已被较新快照覆盖，这个零行结果是成功无操作；但 offset 40 仍要等这项无操作完成后才能推进前缀并提交 43。条件更新只保证快照不倒退，不会执行被跳过的状态转换；若每个转换都有业务副作用，应使用前述顺序应用。事件 ID 去重仍可处理相同事件重投，但不替代顺序约束。

### 崩溃发生在处理与提交的哪一边？

假设 group 当前 committed offset 为 40，要把事件 40 写成数据库中的报表状态：

| 崩溃点 | 数据库状态 | Kafka 恢复位置 | 后果 |
| --- | --- | --- | --- |
| 数据库事务先提交，Kafka offset 尚未提交 | 数据库已应用事件 40 | 仍从 40 读 | 事件 40 重做；稳定 event_id/inbox 可消除同一事件的重复效果，完整快照也可由 last_seq 条件让重放成为无操作 |
| Kafka 先提交 41，数据库尚未提交事件 40 | 数据库没有事件 40 的效果 | 从 41 读 | 事件 40 被跳过，投影缺少一次更新 |

所以普通外部数据库消费者通常在业务事务成功后再提交 offset，接受“至少一次”以及重放，并让数据库按稳定 event_id 原子去重。若先提交 Kafka offset，就必须接受处理失败时的丢失窗口，不能称为安全交付。提交 offset 和业务效果若位于两个系统，二者之间总有先后；普通 Kafka commit 不会替外部数据库建立原子事务。

### 再均衡怎样拒绝旧成员的提交？

成员加入、离开或超时会触发 rebalance（再均衡），组协调器据当前成员重新分配分区。另看一个独立的 classic group protocol（经典组协议）调度：代次 5 只有 C1 持有分区 0，已提交 offset 为 40；新成员 C2 加入后，组进入代次 6，把分区 0 交给 C2。交接有两种结果：

| C1 在撤销时的状态 | C1 对 offset 40 的处理 | C2 接手位置 |
| --- | --- | --- |
| 协调器尚未撤销旧代次；C1 在撤销回调停止派发新工作，完成 40 并成功同步提交 41 | 已提交位置成为 41 | C2 从 41 读取 |
| 协调器已撤销旧代次；C1 的提交 41 被 fencing 拒绝 | 已提交位置仍为 40 | C2 从 40 读取并重放事件 40 |

撤销回调中的排空和提交有边界：只有仍获准的旧成员才能成功提交；失权后不能再假定有一次提交机会。若事件 40 已先写入数据库而 offset 41 未提交，C2 会重放它，数据库仍需用 event_id 或序号条件处理重复。

这个 fencing（栅栏拒绝）只保护 Kafka 组成员与 offset 提交。event_id 只阻止同一事件重复产生效果；前成员后台任务执行的另一个事件仍可能第一次写入数据库。若业务要求分区失权后的旧任务不能再写，目标数据库必须在同一事务内核验当前 ownership epoch 并应用业务更新，或在新所有者接手前确认所有旧任务已完成/停止。若投影只保存完整快照，可用上一节的 last_seq 条件阻止旧快照覆盖新快照，但这不执行每一步转换。只捕获 Kafka 的 CommitFailedException 不能回滚已经提交的 SQL。

官方 Java 客户端提供 ConsumerRebalanceListener 的分区撤销与分配回调；具体重平衡协议有 classic 和 consumer 两种，4.1 文档中的提交请求携带 group generation 或 member epoch。本文只推演组管理的所有权与 offset fencing，不假定不同协议的回调时序相同，也不固定一个再均衡耗时。

### 回放能重建到哪里？

在线投影用稳定的 consumer group 保存进度，从当前 offset 持续追事件。历史重建可以新建 group，并把每个分区的下一读取位置与初始快照一起保存；新表从该位置向后重算。如果只是复用在线 group 并重置 offset，会改变在线投影的恢复点。切换读取前选定每分区 next-offset 向量 T。T[p] 表示下一要处理 offset；投影在 T 的状态应恰好包含已交付且 offset < T[p] 的记录，不能把 consumer 已提交位置直接当作异步数据库效果已完成的证明。先让在线投影完成所有 `< T[p]` 的外部效果并暂停在 T，再让重建表也只应用到 `< T[p]`、不处理 `>= T[p]`，核对两边在 T 的状态后切读。新 group 以 T 为恢复位置继续消费；`>= T[p]` 的事件仍须在 Kafka 保留窗口内，随后由新投影处理。这样比较的是同一组每分区边界上的状态，而不是任意时刻的表行数。

回放范围受 retention（保留）策略限制。若旧 offset 已超出仍保留的日志范围，设置 earliest 只能从“当前最早可读记录”开始，不能复活已删除事件；若使用日志压缩，同一键的旧状态事件可能被保留为较新值所替代。需要完整历史时，应把容量与保留窗口按最慢重建速度设计，或备份快照并从其对应的 offset 接续重放。

Kafka 的事务可把 Kafka 输出 topic 的记录与被消费分区的 offset 一起提交；读者用 read_committed 隐藏中止事务的输出。这能支持 Kafka 到 Kafka 的原子处理，但没有将一个 MySQL/PostgreSQL 写入纳入同一事务。数据库输出仍需本地事务写入业务效果和 inbox/outbox（收件箱/发件箱），或由目标数据库保存并原子推进消费位置。更一般的确认与重试语义见[报表任务的发布确认、消费者确认与业务完成各证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

若要继续看账户报表持久任务的本地提交边界，见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

> [!info]- 来源
> - 分区内全序、一个组内每分区由一个消费者承接、consumer position 是下一个记录 offset：[Apache Kafka 4.1 Design](https://kafka.apache.org/41/design/design/)，Consumer Position；键的语义分区：[Apache Kafka 4.1 Design](https://kafka.apache.org/41/design/design/)，Distribution。
> - 按 key 选择分区的 producer 行为：[Apache Kafka 4.1 Producer Configs](https://kafka.apache.org/41/configuration/producer-configs/)；扩分区后同键路由变化是基于默认哈希分区映射的推论，具体仍取决于 producer partitioner。
> - Producer retry 可能让后发 batch 先于重试 batch 写入；producer idempotence 与顺序配置边界：[Apache Kafka 4.1 Producer Configs](https://kafka.apache.org/41/configuration/producer-configs/)，retries 与 partitioner.class。
> - Java 消费者提交的 offset 应是下一个读取位置；再均衡撤销/分配回调与失去分区后的 commit 失败：[Apache Kafka Java Client 4.1.2 KafkaConsumer Javadoc](https://kafka.apache.org/41/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html)，Offset commit 与 ConsumerRebalanceListener。
> - classic generation 与 consumer member epoch 均进入 offset commit 协议：[Apache Kafka 4.1 Protocol](https://kafka.apache.org/41/design/protocol/)，OffsetCommit Request。
> - Kafka 输出记录和消费位置可共处 Kafka 事务；外部系统需要共同参与才能原子提交：[Apache Kafka 4.1 Design](https://kafka.apache.org/41/design/design/)，Using Transactions。
> - `read_committed` 下的可见记录、offset 超范围时的 earliest/latest/none 策略与消费者故障导致分区重新分配：[Apache Kafka 4.1 Consumer Configs](https://kafka.apache.org/41/configuration/consumer-configs/)；日志压缩与分区保留：[Apache Kafka 4.1 Topic Configs](https://kafka.apache.org/41/configuration/topic-configs/)；本章的报表 42 业务序号、并发完成次序、数据库去重字段、`last_seq` 投影条件和对齐切读的 offset 向量是合成应用合约。
## 19. 何时选择轮询、SSE、流式 Fetch 或 WebSocket？

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

还要估计连接数、更新频率、消息大小、后台休眠行为和服务端连接容量。一名客户端每秒两次轮询约 2 请求/秒，一万名客户端约 20,000 请求/秒；这只估计请求数，不代表 CPU、网络或数据库开销相同。容量与准入见[Web 服务如何限制拒绝服务的影响？](#29.%20Web%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%8B%92%E7%BB%9D%E6%9C%8D%E5%8A%A1%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F)。

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

SSE 可以自动重连，WebSocket 需要应用自己重连，Fetch 也要由应用重新发请求；它们都不能证明数据库副作用是否提交，也不能恢复服务进程内丢失的任务状态。遇到未知完成结果，应查稳定的状态资源，见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - SSE 线格式、EventSource 重连、Last-Event-ID 更新、204 停止重连与事件解析：[WHATWG HTML Living Standard, Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)，§9.2，按 2026-11-05 版本核对。
> - Fetch 请求与响应体、取消和流处理：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，§2、§4；[Streams Standard](https://streams.spec.whatwg.org/)，§4；持续维护规范，核对于 2026-11-06。
> - 浏览器 WebSocket API：[WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/)，§2；握手和消息帧：[RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)，§4–§5；HTTP/2 承载扩展：[RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)；HTTP/3 扩展：[RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)，均核对于 2026-11-06。
> - Node.js `ws` 服务端广播：[ws README, Server broadcast](https://github.com/websockets/ws#server-broadcast)，核对于 2026-11-06。库文档描述该实现，不是协议规范。
## 20. 何时选线程、进程或异步 I/O？

**案例：** 报表服务接到 acct-17 的导出任务，需要读数据库、格式化几万行并写出压缩文件。数据库响应期间主要在等 I/O；格式化若占住一颗 CPU 很久，则会拖慢同一执行路径上的其他请求。选线程、进程或异步 I/O，要先看工作是在等什么、要共享什么，以及停止它时谁负责释放资源。

~~~mermaid
flowchart TD
    Report[账户报表任务] --> Wait{当前主要在等 I/O？}
    Wait -->|是| Async[异步 I/O：等待时让其他工作继续]
    Wait -->|否，CPU 计算很久| CPU{需要独立地址空间/故障隔离，或运行时线程不能并行计算？}
    CPU -->|是| Process[独立进程：消息或显式共享内存]
    CPU -->|否| Thread[工作线程：共享地址空间；并发修改需同步]
    Async --> Limit[仍要限制在途任务和等待队列]
    Thread --> Limit
    Process --> Limit
~~~

图里的决定顺序是：先确认是否有长时间 CPU 计算，再选择执行边界。异步 I/O 让等待中的任务不必独占一个线程，但不会让 CPU 计算自动并行；线程与进程也不会自动形成有界的任务队列。

### 进程、线程和异步 I/O 各自拥有哪种边界？

在常见操作系统模型中，process（进程）是资源与保护边界，通常有自己的虚拟地址空间；thread（线程）是进程里的执行路径。同一进程的线程共享地址空间中的堆、全局数据和许多句柄，但每个线程仍有自己的寄存器状态和栈。进程间通常用管道、套接字、消息或显式映射的共享内存通信。进程可通过显式配置共享部分资源，因此“进程绝不共享”也不准确。

| 选择 | 报表服务里的合适工作 | 付出的责任 |
| --- | --- | --- |
| 异步 I/O | 等待数据库查询、网络响应或异步文件 I/O | 等待期间仍有任务、连接和缓冲区；必须限制并发 |
| 工作线程 | CPU 密集型转换；或确实需要共享同一进程状态 | 共享可变状态需同步；线程池及其排队量需有界 |
| 独立进程 | 易崩、需要独立生命周期或独立地址空间的计算 | 消息/序列化、独立内存和启动成本；必须管理子进程退出。不可信代码还需要操作系统权限隔离 |

并发（concurrency）是多个任务在一段时间内交替推进；并行（parallelism）是多个处理单元同时执行指令。单线程事件循环可以在一个请求等待 I/O 时处理另一个请求，因此能有并发；一个很长的同步回调仍会堵住这条线程。要让 CPU 计算并行，需要工作线程或其他执行资源，但能否提速还取决于语言运行时、数据交换和负载大小。Node 的运行时选择见[Node.js 如何在事件循环、worker 与进程之间调度工作？](#21.%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

阻塞 I/O 会让调用线程等操作完成或可以继续；非阻塞 I/O 在暂时无法继续时迅速返回，但一次返回可能只表示“目前没数据”；异步 I/O 则让调用方提交操作，并在稍后收到完成结果。异步 API 描述调用关系，不表示底层必定由某个工作线程执行：网络 I/O 可由操作系统就绪通知驱动，某些文件或加密工作则可能使用运行时的线程池。

### 共享计数为什么会丢更新？

竞态（race condition）是结果取决于并发操作顺序。count += 1 看起来是一条语句，概念上却是读、加一、写回三个步骤。若两个线程都先读到 10，再各自写 11，最终还是 11；预期的 12 丢了一次更新。对共享不变量，选择一条明确的所有权规则：锁、原子操作、单一写入者消息循环，或数据库约束。数据库中的库存不能靠进程内锁在所有服务副本间保护。

以下例子把一个 32 位计数器放进共享内存，用 Atomics.add 将读—改—写变成原子操作。每个工作线程（worker thread）加 100,000 次，因此两者结束后应为 200,000。

~~~javascript
// 保存为 counter.cjs；使用 Node.js v26.11.1 运行
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
      else reject(new Error('worker exited with code ' + code));
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

本机运行输出 200000。它验证了这段小程序在该 Node 版本中的结果，不证明增加 worker 就会线性提速。

### 等待环何时才构成死锁？

在每类资源只有一个实例的模型里，deadlock（死锁）等价于资源等待图出现环：例如线程 A 持有互斥锁 R1 并等 R2，线程 B 持有 R2 并等 R1。若资源有多个可互换实例，等待图出现环只是必要线索，不足以单独证明死锁。经典资源分配模型还列出互斥、持有并等待、不可抢占和循环等待四个条件；在这个模型中打破任一条件即可消除此类死锁。它们不是判断任意慢请求的打勾清单：请求等待 I/O 或 Promise 未完成本身不构成死锁，先找出实际的资源与依赖关系。浏览器中等待 fetch 的 Promise 不会持有 DOM 独占锁，event loop 可在其 pending 期间运行其他代码；但真实依赖环、永不完成的 Promise 或资源耗尽仍可能让应用停滞。全局一致的锁顺序和短临界区可以拆掉许多锁环；不要在持锁期间等待不确定时长的网络调用。

### 取消信号能证明什么？

取消（cancellation）通常只是要求任务在安全检查点停止。代码需要观察信号、停止提交新副作用，并通过 finally 或等价清理机制释放自己拥有的资源。若取消的是等待方，底层线程、数据库操作或远端请求可能仍在执行；已经提交的写入也不会因此回滚。调用方应以持久化的业务结果确认副作用，而不是把“本地任务已取消”当成“操作没有发生”。

**接下来：** 本章区分执行资源和共享状态；Node 章节把这些边界落实到 isolate、worker 和进程。异步作业何时接受、重试或显式取消见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - 进程与线程的资源、地址空间、线程状态模型：[POSIX.1-2024, General Information](https://pubs.opengroup.org/onlinepubs/9799919799/functions/V2_chap02.html)，核对于 2026-11-06。
> - Linux/POSIX 线程共享内存、取消点及取消类型：[Linux man-pages, pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)，核对于 2026-11-06。
> - Node worker 并行计算与共享内存：[Node.js v26.11.1, worker_threads](https://nodejs.org/download/release/v26.11.1/docs/api/worker_threads.html)；计数程序于该版本重放，输出 200000。
> - Node 文件 API 的异步执行方式：[Node.js v26.11.1, File system](https://nodejs.org/download/release/v26.11.1/docs/api/fs.html#threadpool-usage)，核对于 2026-11-06。
> - 经典资源分配死锁的互斥、持有并等待、不可抢占与循环等待条件：[Coffman, Elphick, and Shoshani (1971), “System Deadlocks”](https://doi.org/10.1145/356586.356588)，核对单实例资源等待环的适用边界。
## 21. Node.js 如何在事件循环、工作线程与进程之间调度工作？

**案例：** API 收到导出 acct-17 报表的请求：先用数据库网络连接取数据，再压缩输出；同一服务还要接其他用户请求。异步 I/O 能让线程在等待数据库或网络时处理别的工作，不能让一段长时间的 JavaScript 汇总循环自己让路。遇到 CPU 阻塞时才考虑工作线程；需要独立内存或故障边界时考虑进程。

~~~mermaid
flowchart TD
    Request[API 请求] --> Main[主进程中的 JavaScript isolate]
    Main -->|等待网络 I/O| Kernel[操作系统 I/O]
    Main -->|所选 API 的后台工作| Pool[libuv 工作线程池]
    Main -->|CPU 密集型 JavaScript| Worker[有界 worker_threads 池]
    Main -->|隔离或独立生命周期| Child[子进程]
    Child -->|多进程 HTTP 入口| Cluster[cluster：多个 Node 进程]
    Worker --> Main
    Pool --> Main
    Main --> Queue[限制任务数与等待队列]
~~~

### 默认的 JavaScript 执行路径是什么？

Node.js 进程中的每个 JavaScript isolate（隔离环境）有自己的 JavaScript 执行线程和事件循环。主线程运行请求处理器；异步操作完成后，回调再回到相应 isolate 的事件循环执行。一个长同步 JSON 变换会占住主线程，延迟这个进程里其他请求的回调。异步并不等于“所有工作都交给另一个线程”；worker thread（工作线程）指 Node 的工作线程 API，和 cluster 启动的工作进程不同。

网络 I/O 通常由操作系统异步机制推进；libuv（Node.js 使用的跨平台异步 I/O 库）协调部分后台工作。Node.js v26.11.1 文档说明，回调式与 Promise 式文件系统 API（fs.FSWatcher 除外）使用 libuv 工作线程池，部分加密和压缩 API 也使用该池，完成后的 JavaScript 回调仍回到事件循环。具体 API 的实现契约不同，因此不要把“异步”直接等同于“线程池”。例如，适合大量等待的场景优先使用 Node 的异步 I/O；worker_threads 主要解决 CPU 密集型 JavaScript，并不替代高效 I/O。

### 该把计算放在哪种执行资源上？

| 选择 | 适合报表服务的情况 | 隔离和共享边界 |
| --- | --- | --- |
| 主事件循环上的异步 API | 等数据库、网络或异步文件操作 | 等待不占住 JS 调用栈；同步计算仍会阻塞当前 isolate |
| worker_threads | 大块 CPU 密集型 JavaScript，且能按任务切分 | worker 有独立 isolate 和堆；可发消息、转移 ArrayBuffer 或共享 SharedArrayBuffer，共享时要用 Atomics 等同步 |
| child_process | 工作有独立地址空间、可独立重启或需要更强故障隔离 | 使用 IPC（进程间通信）等显式通信；内存不与父进程自动共享；默认以相同 OS 用户运行，可访问该用户获准的文件和网络，不是安全沙箱 |
| cluster | 在同一机器上用多个 Node 进程提供 HTTP 服务 | 每个 worker 是进程；进程内会话或缓存不自动共享，退出和重启要由应用或进程管理器处理 |

不要为每个小请求新建一个线程或进程。重复计算应交给有界 worker 池，并限制等待队列；否则只是把事件循环前的无界等待移到 worker 前。进程选择也要计入消息传输、启动时间、独立连接池和每进程内存。操作系统层面的比较见[何时选线程、进程或异步 I/O？](#20.%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)；具体槽位与连接预算见[如何估算并限制异步工作管线？](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)。

若报表只是等待数据库，直接使用异步数据库驱动，额外线程只会增加调度和连接管理成本。若从已取回的数据计算摘要会持续占用主事件循环，就交给有界 worker 池。若扩展可能崩溃或需要独立生命周期，可用子进程隔开地址空间和故障生命周期；子进程不会自动隔离文件、网络或其他操作系统权限。运行不可信代码还需要真实的操作系统权限隔离，本章不实现这部分。cluster 是让多进程接受 HTTP 连接的一种部署方式，不保证吞吐量线性增长；数据库、内存和磁盘也仍是共享的机器资源。

### 子进程怎样接收一个计算任务？

下面的 CommonJS 示例用 fork() 启动同一文件作为子进程，通过 IPC 发送 Fibonacci 输入并取回结果。它展示进程边界，不是生产任务队列：没有排队上限、重复任务保护或 supervisor 级别的重启策略。

~~~javascript
// 保存为 report-child.cjs；使用 Node.js v26.11.1 运行
const { fork } = require('node:child_process');

function fib(n) {
  let a = 0;
  let b = 1;
  for (let i = 0; i < n; i++) [a, b] = [b, a + b];
  return a;
}

if (process.argv[2] === 'worker') {
  process.on('message', ({ n }) => {
    process.send({ result: fib(n) });
  });
} else {
  const child = fork(__filename, ['worker']);
  child.once('error', error => {
    console.error(error);
    process.exitCode = 1;
  });
  child.once('message', ({ result }) => {
    console.log(result);
    child.disconnect();
  });
  child.send({ n: 10 });
}
~~~

输出 55。使用真实 CPU 计算时，应该复用有界进程或 worker 池，而不是每个报表都启动一个新进程。

cluster 让多个 Node 子进程监听同一服务端口。下面延续同一报表服务，重点是每个 worker 的进程隔离；若把会话或进程内缓存放在这些 worker 里，请求落到另一个 worker 时就看不到同一份状态。

~~~javascript
// 保存为 cluster-report.cjs；使用 Node.js v26.11.1 运行
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
    response.end('report API');
  }).listen(8000);
}
~~~

该服务要用外部状态存储、明确的连接路由或消息机制解决跨进程状态共享。任何多进程部署还需要健康检查、滚动退出和重启策略；怎样排空 Node HTTP 请求见[Node.js 服务如何排空并关闭？](#24.%20Node.js%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E6%8E%92%E7%A9%BA%E5%B9%B6%E5%85%B3%E9%97%AD%EF%BC%9F)。

若使用 PM2 管理集群，可用 pm2 start app.js --name api -i max 启动、pm2 list 或 pm2 monit 观察、pm2 reload api 请求滚动重载。PM2 对 stop、restart、reload 默认先发送 SIGINT，等待 `kill_timeout`（默认 1600 ms）后仍未退出就发 SIGKILL；可用 `PM2_KILL_SIGNAL` 改信号。reload 超时也可能退化为 restart。应用应处理部署实际发来的信号并在强杀前完成排空；用户态会话也不能默认留在单进程内存里。

> [!info]- 来源
> - Worker 线程适用 CPU 工作、消息与共享内存边界：[Node.js v26.11.1, worker_threads](https://nodejs.org/download/release/v26.11.1/docs/api/worker_threads.html)，核对于 2026-11-06。
> - 子进程 IPC 与 fork()：[Node.js v26.11.1, child_process](https://nodejs.org/download/release/v26.11.1/docs/api/child_process.html)，示例于该版本重放，收到结果 55。
> - 多进程共享 HTTP 端口及 worker 生命周期：[Node.js v26.11.1, cluster](https://nodejs.org/download/release/v26.11.1/docs/api/cluster.html)，核对于 2026-11-06。
> - 文件系统哪些 API 使用 libuv 线程池：[Node.js v26.11.1, File system](https://nodejs.org/download/release/v26.11.1/docs/api/fs.html#threadpool-usage)；加密、压缩和 DNS 的 API 边界见 [crypto](https://nodejs.org/download/release/v26.11.1/docs/api/crypto.html)、[zlib](https://nodejs.org/download/release/v26.11.1/docs/api/zlib.html)、[DNS](https://nodejs.org/download/release/v26.11.1/docs/api/dns.html)，核对于 2026-11-06。
> - PM2 Cluster mode 的 reload 回退与进程关闭责任：[PM2, Cluster Mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/)；启动、查看和重载命令见 [PM2 Quick Start](https://pm2.keymetrics.io/docs/usage/quick-start/)，核对于 2026-11-06。
> - PM2 默认 SIGINT、`kill_timeout` 后 SIGKILL 和 `PM2_KILL_SIGNAL` 配置：[PM2, Graceful Start/Shutdown](https://pm2.keymetrics.io/docs/usage/signals-clean-restart/)、[PM2 Environment Variables](https://pm2.keymetrics.io/docs/usage/environment/)，核对于 2026-11-06。
## 22. Node.js 事件循环阶段与微任务队列如何交互？

一个报表请求先排定定时器，再等数据库读回调；两者何时运行取决于当前 JavaScript 操作、event loop（事件循环）阶段和队列。不要只记一个跨所有上下文的“异步先后顺序”：CommonJS 与 ES module 顶层执行中的 nextTick 和 Promise 排序不同，定时器也只承诺最早可运行时间，不是精确截止时刻。

~~~mermaid
flowchart TD
    subgraph loop[libuv 事件循环阶段]
        Timers[Timers：到期定时器] --> Pending[Pending callbacks]
        Pending --> Poll[Poll：I/O 事件]
        Poll --> Check[Check：setImmediate]
        Check --> Close[Close callbacks]
        Close --> Timers
    end
    Operation[CJS 普通 JavaScript 调用返回] --> Tick[清空 nextTick 队列]
    Tick --> Micro[清空 Promise / queueMicrotask 队列]
    Micro --> LoopNext[事件循环继续]
~~~

这张图概括普通 CommonJS JavaScript 操作返回到 Node 调度点后的处理顺序：idle、prepare 是内部阶段；nextTick 和微任务不属于 libuv 的阶段。ES module 求值和正在排空的微任务队列有不同上下文，不能用图中的一条箭头替代后面的条件说明。

### I/O 回调、定时器和 setImmediate() 何时推进？

Node 使用 libuv（Node.js 的跨平台事件循环与异步 I/O 库）管理计时器和 I/O 回调。常见阶段包括 timers、pending callbacks、poll、check 和 close callbacks。poll 取回 I/O 事件并执行相关回调；setImmediate() 在 check 阶段运行；定时器只在给定延迟门槛之后变为可运行，繁忙的回调仍会让它晚于门槛才得到执行。

从 Node.js 20 所用的 libuv 1.45.0 起，定时器在每轮 poll 后运行；较早版本还会在 poll 前运行。不要依赖主模块中 setTimeout(fn, 0) 和 setImmediate(fn) 的固定顺序。在 I/O 回调里排定两者时，setImmediate() 在 check 阶段先运行。

~~~javascript
// save as timers.cjs; output order for the first pair may vary
const fs = require('node:fs');

setTimeout(() => console.log('top-level timeout'), 0);
setImmediate(() => console.log('top-level immediate'));

fs.readFile(__filename, () => {
  setTimeout(() => console.log('timer after I/O'), 0);
  setImmediate(() => console.log('immediate after I/O'));
});
~~~

上例中两条带 top-level 的输出允许不同顺序；I/O 回调中则先输出 immediate after I/O。如果一次同步回调执行 120 ms，即使 setTimeout(..., 100) 已到门槛，它也要等该回调结束才能运行。给 API 设服务端截止时间时，应使用明确的 deadline（截止时间）和可取消操作，不把定时器当作严格准点机制。

### nextTick 与 Promise 微任务的顺序为何会变？

nextTick 队列是 Node 管理的队列；Promise reaction 和 queueMicrotask() 使用 microtask（微任务）队列。在普通 CommonJS 顶层或 callback 返回到 Node 的调度点时，当前 JavaScript 操作先完成，Node 随后处理 nextTick，再排空微任务。ES module 顶层求值本身处于微任务处理中，所以顶层排入的 Promise 和 queueMicrotask 先于 nextTick。

| 代码所在上下文 | 下面三个回调的输出顺序 |
| --- | --- |
| CommonJS 顶层 | nextTick → promise → microtask |
| ES module 顶层 | promise → microtask → nextTick |

保存并分别运行：

~~~javascript
// queues.cjs — Node.js v26.11.1
const { nextTick } = require('node:process');

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
~~~

~~~javascript
// queues.mjs — Node.js v26.11.1
import { nextTick } from 'node:process';

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
~~~

本机依次运行得到 CommonJS：nextTick, promise, microtask；ES module：promise, microtask, nextTick。Promise 与 queueMicrotask 同属微任务队列，在本例中按排队顺序运行。若代码已经在执行微任务时才排入 nextTick，该 callback 不会插队中断本轮微任务队列；Node 会等当前队列排空后再处理它：

~~~javascript
Promise.resolve().then(() => {
  console.log('microtask A');
  process.nextTick(() => console.log('nextTick from microtask'));
  Promise.resolve().then(() => console.log('microtask B'));
  queueMicrotask(() => console.log('queueMicrotask from microtask'));
});
~~~

Node.js v26.11.1 的本机输出是 microtask A、microtask B、queueMicrotask from microtask、nextTick from microtask。当前 Node 文档把 process.nextTick() 标为 Legacy，多数用户代码应优先选 queueMicrotask()；只有兼容现有 nextTick 排序契约时才保留 nextTick。递归排入 nextTick 会不断清空该队列，令循环迟迟进不了 poll，从而饿死 I/O。

nextTick 曾用于让 callback API 的验证错误也延后到当前调用栈退栈后交付，或者让构造器返回后才发出 readiness 事件，好让调用方先注册 listener：

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

该例运行输出 ready；普通的可移植延后优先使用 queueMicrotask。上述顺序是 Node 宿主的调度契约，不是 JavaScript Promise 语言本身的跨宿主规则。浏览器事件循环见[浏览器事件循环](../../frontend/runtime/event-loop.md)；Node 主线程与 CPU worker 的选择见[Node.js 调度与 worker 选择](#21.%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

> [!info]- 来源
> - 阶段、计时器门槛、poll 与 setImmediate()：[Node.js Event Loop](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick)，核对于 2026-11-06；Node.js 20 起的阶段变更对应 libuv 1.45.0。
> - nextTick 队列、CommonJS/ES module 顺序和 Legacy 状态：[Node.js v26.11.1, process](https://nodejs.org/download/release/v26.11.1/docs/api/process.html#when-to-use-queuemicrotask-vs-processnexttick)，三个队列例子于该版本重放。
## 23. Node.js 流如何传播背压？

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

### 什么状态表示写入方该等一等？

Readable（可读流）提供数据块；Writable（可写流）接收数据块；Transform（转换流）一边读取一边转换；Duplex（双工流）同时可读可写。只有 writable 仍处于可写、未结束且未销毁状态时，手动调用 writable.write(chunk) 返回 false 才表示当前块已被接收、内部缓冲达到 highWaterMark 阈值；这时先停止继续写，等 drain 后再恢复。若写入已结束、流已销毁或遇到错误，false 不能证明数据已接收，且不会保证再有 drain；应处理 error/close 并结束这条管线。

在正常可写状态下，返回 true 表示当前仍可继续写入；返回 false 表示应暂停，待 drain 后再继续。

highWaterMark（缓冲阈值）是何时降低读取速度的门槛，不是内存硬上限。`Readable.from()` 默认 `objectMode: true`，此时阈值按数据块个数而非字节数计；本例产出字符串，因此显式关闭 object mode。`32 KiB` 只设置本地文件 sink 的阈值，压缩流、源流、较大单块和管线外队列仍有各自缓冲。真正的背压要求生产端能暂停，且每一层都把“下游暂时消化不了”传回源。

### 如何让一条报表流自然限速并释放游标？

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

生产 worker 应从已持久接受且已授权的 job 读取 acct-17、时间范围与分页上限，不能从队列正文重新信任未验证的账户范围。现有报表设计按最多 12 页查询、每页短事务读取；读取完一页即归还连接，再做压缩和写入，见[如何限定 ORM Session 并排查连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。如果实际驱动提供的是持有数据库游标的长连接流，它可能在下游变慢时继续占住事务和连接；须把这段真实连接持有时间计入连接池和任务槽预算。需要同一快照时，可以明确选择长事务并核算额外成本，不能把短事务分页示例直接换成长游标。真实驱动是否响应取消仍需按驱动契约确认；如果不支持，正在执行的查询可能要等返回后生成器 finally 才能关闭游标。

Writable 的 highWaterMark 是缓冲阈值，不是整条管线的内存预算；如果上游在管线外把所有任务先放入数组或无界队列，stream 背压到不了那条队列。取消会传播给参与管线的流，但不能假定驱动正在执行的 `cursor.next()` 已停止：当前查询可能要先返回，生成器的 `finally` 才能关闭游标。资源所有者应跟踪并等待该操作确实结束，再关闭它仍在使用的连接；仅观察 AbortSignal 已触发不足以证明资源可释放。可读流的 end 表示没有更多输入块；调用 end() 后可写流的 finish 表示已处理接受的写入；close 表示该流报告资源关闭；error 表示失败。文件流 finish 也不证明远端应用收到数据或文件系统已持久化。

**接下来：** 本章说明管线内部的流量控制；HTTP 请求、worker 和持久队列的并发上限见[如何估算并限制异步工作管线？](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)。服务退出时如何停止接入并等流结束，见[Node.js 服务如何排空并关闭？](#24.%20Node.js%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E6%8E%92%E7%A9%BA%E5%B9%B6%E5%85%B3%E9%97%AD%EF%BC%9F)。

> [!info]- 来源
> - Writable.write() 返回 false、drain、错误/销毁状态，以及 Readable.from() 默认 object mode：[Node.js v26.11.1, Stream](https://nodejs.org/download/release/v26.11.1/docs/api/stream.html)，核对于 2026-11-06。
> - pipeline() 的 Promise、AbortSignal 和流清理：[Node.js v26.11.1, stream/promises](https://nodejs.org/download/release/v26.11.1/docs/api/stream.html#stream-promises-api)，核对于 2026-11-06。
> - end、finish、close 和 error 的生命周期定义：[Node.js v26.11.1, Stream API](https://nodejs.org/download/release/v26.11.1/docs/api/stream.html)，核对于 2026-11-06。
## 24. Node.js 服务如何排空并关闭？

**案例：** 报表 API 正在读取数据库并写流式响应时收到 SIGTERM。优雅关闭（graceful shutdown）的关键是按所有权顺序收拢工作：先停止对外宣称 readiness（就绪状态）并拒绝新任务，再停止接收连接，等待现有请求和后台工作不再使用依赖，最后关闭连接池、后台工作线程或进程和其他资源。deadline（截止时间）到达时发出协作取消；只有可观察的完成条件才能证明任务已经停下。

~~~mermaid
stateDiagram-v2
    [*] --> Ready
    Ready --> Draining: SIGTERM / 摘除就绪并拒绝新任务
    Draining --> Waiting: 停止接收连接
    Waiting --> Cleanup: 在途工作与 HTTP 服务都已结束
    Waiting --> Deadline: 截止时间到
    Deadline --> Cancel: 发出协作取消
    Cancel --> ForceClose: 关闭剩余 HTTP 连接
    ForceClose --> Waiting: 等工作退出其依赖
    Cleanup --> Closed: 关闭池、worker 与其他资源
    Closed --> [*]
~~~

这里的排空不是 HTTP Server 自动替应用完成的事。request handler、后台任务、响应流和任务专用游标都要登记到各自拥有者，关闭程序才能知道它们何时不再使用依赖。

### 为什么要先拒绝工作再关闭连接？

先将实例标为不就绪，负载均衡器就有机会停止把新连接路由到它；但健康状态的传播有延迟，因此 handler 也要在入队或开始副作用前检查 draining 状态。对已经打开的 keep-alive 连接，新请求可能仍会到达，handler 应返回带 Connection: close 的 503 并且不要受理任务。随后调用 server.close() 停止接入；它的回调表示 HTTP 连接和响应已收尾。应用拥有的后台工作由单独的 inFlight 集合跟踪并等待，不能把这两个完成条件混为一谈。

下面是可以直接运行的最小服务。它用一个可取消的计时操作代替数据库报表任务，跟踪这项工作，并演示：1 秒截止到达时向它发出取消、关闭剩余 HTTP 连接，然后等待实际工作结束才清资源。这个截止只约束本例可取消的 timer 与 HTTP 连接；不响应取消的 handler 仍会让 inFlight 等待继续。真实服务要把 readiness、任务跟踪和资源清理接到自己的 health、worker 及连接池实现上，并由进程 supervisor 提供最终硬截止。

> [!example]- 可运行的关停示例
>
> ~~~javascript
> // 保存为 shutdown-demo.cjs；使用 Node.js v26.11.1 运行
> const http = require('node:http');
> const { setTimeout: sleep } = require('node:timers/promises');
>
> const workAbort = new AbortController();
> const inFlight = new Set();
> let draining = false;
>
> function trackWork(promise) {
>   inFlight.add(promise);
>   promise.then(
>     () => inFlight.delete(promise),
>     () => inFlight.delete(promise),
>   );
>   return promise;
> }
>
> async function createReport(signal) {
>   await sleep(5_000, undefined, { signal });
>   return 'report ready';
> }
>
> async function waitForInFlightWork() {
>   while (inFlight.size > 0) {
>     await Promise.allSettled([...inFlight]);
>   }
> }
>
> const server = http.createServer(async (request, response) => {
>   if (draining) {
>     response.writeHead(503, { Connection: 'close' });
>     response.end('draining');
>     return;
>   }
>
>   try {
>     const report = await trackWork(createReport(workAbort.signal));
>     response.end(report);
>   } catch (error) {
>     if (!response.destroyed) {
>       response.writeHead(503);
>       response.end('report stopped');
>     }
>   }
> });
>
> server.listen(8000);
>
> function markReadiness(ready) {
>   console.log('ready:', ready);
> }
>
> async function closeOwnedResources() {
>   // 生产服务在这里关闭数据库池、worker、定时任务和应用拥有的句柄。
>   console.log('resource cleanup complete');
> }
>
> async function shutdown() {
>   draining = true;
>   markReadiness(false);
>
>   const deadline = setTimeout(() => {
>     workAbort.abort(new Error('shutdown deadline'));
>     server.closeAllConnections();
>   }, 1_000);
>
>   const serverClosed = new Promise((resolve, reject) => {
>     server.close(error => error ? reject(error) : resolve());
>   });
>
>   try {
>     const lifecycle = await Promise.allSettled([
>       serverClosed,
>       waitForInFlightWork(),
>     ]);
>     const lifecycleFailures = lifecycle.filter(result => result.status === 'rejected');
>
>     let cleanupFailure;
>     let cleanupFailed = false;
>     try {
>       await closeOwnedResources();
>     } catch (error) {
>       cleanupFailed = true;
>       cleanupFailure = error;
>     }
>
>     for (const result of lifecycleFailures) {
>       console.error('shutdown lifecycle failed:', result.reason);
>       process.exitCode = 1;
>     }
>     if (cleanupFailed) {
>       console.error('resource cleanup failed:', cleanupFailure);
>       process.exitCode = 1;
>     }
>   } finally {
>     clearTimeout(deadline);
>   }
> }
>
> process.once('SIGTERM', () => {
>   void shutdown().catch(error => {
>     console.error('shutdown failed:', error);
>     process.exitCode = 1;
>   });
> });
> ~~~

服务在收到信号后先把 draining 设为 true，再启动 deadline。该截止计时器必须保持引用：若用 unref()，当其他句柄不再阻止退出时，Node 可能在 deadline 回调执行前退出。Node.js 19 及以后，server.close() 会关闭空闲连接并等待活动连接；超时时调用 closeAllConnections() 是强制关闭 HTTP(S) 连接，且应该在 close() 之后调用以避免连接竞态。它不会关闭升级后的 WebSocket 或 HTTP/2 会话，这些要由各自的所有者处理。注册 SIGTERM listener 会接管该信号的默认退出路径，所以 handler 必须完成清理，或明确设置失败退出码。

本例监听 SIGTERM，适合显式向进程发送该信号的部署。PM2 对 stop、restart、reload 默认先发 SIGINT；运行在 PM2 下时也要处理 SIGINT，或把 `PM2_KILL_SIGNAL` 配成 SIGTERM。PM2 的 `kill_timeout` 到期后会发 SIGKILL，因此优雅关闭预算必须短于该上限或同步调整管理器配置。

本例的可取消 timer 会在 deadline 到达时停止，因此 tracked work 随后结束，才允许关闭其资源。`server.close()` 回调和 inFlight Promise 集合分别代表 HTTP 收尾与应用工作收尾；即使 HTTP 连接已被强制关闭，handler 仍可能占用数据库连接。对不支持取消的数据库查询、忽略信号的 handler 或已经启动的远端副作用，取消只是通知，并不会强制中止它们；waitForInFlightWork 必须等到它们确实不再使用依赖。若服务超过上层硬截止时间仍未退出，应由进程 supervisor 最终终止，而不能提前关闭仍在使用的资源。HTTP 任务与持久后台 job 的取消边界不同：连接断开不自动撤销已持久接受的账户报表，见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

**本机重放：** Node.js v26.11.1 上启动此脚本，发起一个尚未完成的请求后发送 SIGTERM；deadline 触发取消，输出 ready: false 与 resource cleanup complete，进程以成功状态结束。若 handler 忽略 signal，该清理次序会继续等待它，而不会提前关闭连接池。

> [!info]- 来源
> - HTTP server.close()、closeAllConnections()、空闲连接和协议升级连接边界：[Node.js v26.11.1, HTTP](https://nodejs.org/download/release/v26.11.1/docs/api/http.html)，核对于 2026-11-06。
> - SIGTERM handler 替代默认退出行为及信号行为：[Node.js v26.11.1, process](https://nodejs.org/download/release/v26.11.1/docs/api/process.html)，核对于 2026-11-06。
> - PM2 stop/restart/reload 的默认 SIGINT、可配置的 kill signal 和最终 SIGKILL 截止：[PM2, Graceful Start/Shutdown](https://pm2.keymetrics.io/docs/usage/signals-clean-restart/)，核对于 2026-11-06。
> - 定时器 unref() 与事件循环存活：[Node.js v26.11.1, Timers](https://nodejs.org/download/release/v26.11.1/docs/api/timers.html)，核对于 2026-11-06。
> - AbortSignal 对 Promise 定时器的协作取消：[Node.js v26.11.1, Timers Promises API](https://nodejs.org/download/release/v26.11.1/docs/api/timers.html#timers-promises-api)，本例按上述时序重放。
## 25. Python 的值、迭代器与资源生命周期如何工作？

**案例：** worker 读取账户报表的 CSV 分页，把有效行逐个送入后续处理。要避免意外共享行对象，不能把整份文件先展开到内存；遇到坏行时，还要关闭文件和临时目录。Python 名称绑定到对象，迭代器按需交付值，上下文管理器则界定资源清理。

~~~mermaid
flowchart LR
    File[CSV 文件] --> Iterator[生成器逐行读取]
    Iterator -->|有效行| Yield[交付一行给调用者]
    Iterator -->|后续格式错误| Error[抛出解析异常]
    Error --> Unwind[离开嵌套 with 块]
    Unwind --> Close[关闭文件并删除临时目录]
    Yield --> Partial[更早输出的行已经离开生成器]
~~~

图中从输入到输出是一条惰性流程：错误可能在已经产出部分结果后才出现，所以资源会清理，但副作用不会自动回滚。

### 名称、可变对象和浅拷贝怎样相互影响？

赋值通常是把名称绑定到对象，不是复制对象。列表和字典可变；同一列表被两个名称引用时，经任一名称原地修改，另一个名称看到的也是同一结果。把其中一个名称重新绑定到新字典，不会改变另一个绑定。浅拷贝会新建外层容器，但其中嵌套的可变对象仍可能共用。

字符串和元组不可原地替换其成员；不过，元组里仍可以放一个可变列表，再修改列表内容。set 保存唯一元素但不提供序列索引；字典把键映射到值，并从 Python 3.7 起保证保留插入顺序。CPython 的 id(obj) 当前以对象地址作为运行期身份值，但不能跨进程或运行期拿来标识账户、job 或数据库记录。

~~~python
event = {"id": "evt-1", "tags": ["new"]}
alias = event
alias["tags"].append("priority")
print(event["tags"])

outer_copy = event.copy()
outer_copy["id"] = "evt-copy"
outer_copy["tags"].append("shared")
print(event["tags"])

alias = {"id": "evt-2", "tags": []}
print(event["id"])
~~~

输出依次是 ['new', 'priority']、['new', 'priority', 'shared']、evt-1。若要隔离嵌套状态，应按所需字段显式重建，或在确有需要时深拷贝；不要把“拷贝了字典”理解为递归复制所有对象。

函数调用也传递对象引用。若函数原地修改传入列表，调用者能观察到修改；函数内部把形参改绑到新对象则不会替调用方重新绑定名称。函数默认表达式在执行 def 时求值一次，因此可变默认对象会被多次调用共用：

~~~python
def unsafe_add(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

print(unsafe_add("first"))
print(unsafe_add("second"))

def add(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

print(add("first"))
print(add("second"))
~~~

前两个结果会累积为 ['first'] 和 ['first', 'second']；修正后的调用分别得到 ['first'] 和 ['second']。若 None 本身也是有效输入，用单独 sentinel 表示“调用方未提供”。

### 迭代器和生成器如何控制读取量？

可迭代对象能提供迭代器；迭代器每次被请求时给出一个值，直到完成。生成器函数包含 yield，调用时返回一个保存执行位置的迭代器；循环或消费端每次请求下一值时，生成器才继续执行。这样可以逐行处理大文件，避免先构造完整结果列表；把生成器转成 list 则会立即消费并保存所有值。

~~~python
from collections.abc import Iterable, Iterator

Row = dict[str, str]

def ready_rows(rows: Iterable[Row]) -> Iterator[Row]:
    for row in rows:
        if row["status"] == "ready":
            yield row
~~~

惰性读取减少中间存储，也可以更早开始输出，但不会让一个多行事务自动具备原子性。如果第 500 条数据记录才有格式错误，而前 499 条已经写入其他系统，就必须由调用方决定这些部分结果能否保留；需要全有或全无时，先验证并暂存，或把修改置于合适的事务边界。

### 解析失败时资源和先前输出会怎样？

下面用合成 CSV 展示完整过程。生成器按 CSV 记录验证列数、状态值和整数数量；错误时读取 `csv.reader.line_num`，报告读到该记录时的物理文件行号，并保留原始异常。CSV 记录可能跨多行，所以不能用记录序号当文件行号。外层在文件与临时目录两个 with 块之外捕获异常。坏记录到来之前已经打印的报表行仍会保留，但两个资源都会在异常退出时关闭。

~~~python
import csv
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

Row = dict[str, str]

def ready_rows(source) -> Iterator[Row]:
    reader = csv.reader(source)
    try:
        headers = next(reader)
    except StopIteration:
        return

    required = {"id", "status", "count"}
    if not required.issubset(headers):
        raise ValueError("CSV header must include id, status, and count")

    for values in reader:
        line_number = reader.line_num
        if len(values) != len(headers):
            raise ValueError(
                f"CSV physical line {line_number}: column count does not match header"
            )
        row = dict(zip(headers, values))
        try:
            status = row["status"]
            if status not in {"ready", "queued"}:
                raise ValueError(f"unknown status {status!r}")
            count = int(row["count"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"CSV physical line {line_number}: status must be ready or queued, "
                "and count must be an integer"
            ) from error

        if status == "ready" and count > 0:
            yield row

def add_tag(row: Row, tag: str = "reviewed") -> Row:
    enriched = row.copy()
    enriched["tag"] = tag
    return enriched

CSV_TEXT = """id,status,count,note
evt-1,ready,3,"account
export"
evt-2,queued,1,skip
evt-3,unknown,2,bad-status
"""

try:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "events.csv"
        path.write_text(CSV_TEXT, encoding="utf-8")

        with path.open(encoding="utf-8", newline="") as source:
            for row in ready_rows(source):
                print(add_tag(row))
except ValueError as error:
    print(f"Rejected input: {error}")
~~~

本机以 CPython 3.11.13 重放，输出第一条 evt-1 记录，再报告 `CSV physical line 5` 的未知状态。该坏行是第 3 条数据记录；第一条 evt-1 记录跨文件第 2、3 两行，第二条 evt-2 在第 4 行，所以记录序号和物理行号不同。生成器是在消费者推进时运行，异常离开两个上下文后文件关闭，TemporaryDirectory 清除其目录。由于第一条结果已输出，资源清理不等同于撤回此前效果。

普通文件的 with 语句能在异常时关闭文件。上下文管理器会先进入代码块，退出时运行清理逻辑；若清理器选择抑制异常，还可改变异常传播，因此应检查实际管理器契约。需及时释放游标、文件或锁时，显式使用 with/finally，不依赖垃圾回收何时运行。

### 类型标注和虚拟环境分别保证什么？

type hint（类型提示）描述函数参数、结果或变量的预期形状，供读者、IDE 和静态类型检查器使用。Python 运行时默认不会因为注解不匹配而拒绝返回值；从网络、文件或数据库读入的 str 仍需解析、验证并转换为可信类型。若一个返回 int 的函数实际返回 str，静态检查器可以报告，但普通调用仍会拿到字符串。

~~~python
def declared_integer() -> int:
    return "still a string"

print(declared_integer())
~~~

本机输出 still a string。版本和实现也要分开说明：本文代码使用 Python 3.11 的语法和标准库行为；字典插入顺序从 Python 3.7 起是语言保证，CPython 3.6 中只是实现细节；CPython 的 id(obj) 目前表现为对象身份值，但不能把它当作跨进程、跨运行的业务标识。

虚拟环境隔离项目安装的包，不会安装或固定 Python 解释器本身。创建环境时选定解释器，再用该环境中的 Python 运行 pip，才能保证装包和执行指向同一环境。将上面的完整文件处理程序保存为 python-fundamentals-example.py。这个示例只依赖标准库，不需要额外安装：

~~~sh
python3.11 -m venv .venv
.venv/bin/python python-fundamentals-example.py
~~~

项目如需第三方库，应把依赖写入项目的 packaging 配置或依赖文件，再用 .venv/bin/python -m pip install -r requirements.txt 从该环境安装；可复现运行还取决于兼容的解释器版本、包版本和平台要求。Python 异步请求怎样选择运行边界见[异步 FastAPI 接口为什么仍会阻塞？](#27.%20%E5%BC%82%E6%AD%A5%20FastAPI%20%E6%8E%A5%E5%8F%A3%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BB%8D%E4%BC%9A%E9%98%BB%E5%A1%9E%EF%BC%9F)；实例属性优先级、descriptor 与协作式多继承见[Python 实例属性何时来自对象字典，何时变成描述符或绑定方法？](#26.%20Python%20%E5%AE%9E%E4%BE%8B%E5%B1%9E%E6%80%A7%E4%BD%95%E6%97%B6%E6%9D%A5%E8%87%AA%E5%AF%B9%E8%B1%A1%E5%AD%97%E5%85%B8%EF%BC%8C%E4%BD%95%E6%97%B6%E5%8F%98%E6%88%90%E6%8F%8F%E8%BF%B0%E7%AC%A6%E6%88%96%E7%BB%91%E5%AE%9A%E6%96%B9%E6%B3%95%EF%BC%9F)。

> [!info]- 来源
> - 名称绑定、对象可变性和字典顺序：[Python 3.11 Language Reference, Data model](https://docs.python.org/3.11/reference/datamodel.html#objects-values-and-types)，核对于 2026-11-06。
> - 默认参数只在函数定义时求值：[Python 3.11 Tutorial, Default Argument Values](https://docs.python.org/3.11/tutorial/controlflow.html#default-argument-values)，本例于 CPython 3.11.13 重放。
> - `csv.reader.line_num` 计源文件物理行，CSV 记录可跨多行：[Python 3.11 csv module](https://docs.python.org/3.11/library/csv.html#csv.csvreader.line_num)，多行记录例于 CPython 3.11.13 重放。
> - 迭代器、生成器与 StopIteration：[Python 3.11 Language Reference, Data model](https://docs.python.org/3.11/reference/datamodel.html#generator-functions)，CSV 例子于 CPython 3.11.13 重放。
> - with 退出时的资源清理：[Python 3.11 Language Reference, The with statement](https://docs.python.org/3.11/reference/compound_stmts.html#the-with-statement)。
> - 注解不作默认运行时验证：[Python 3.11 typing](https://docs.python.org/3.11/library/typing.html)，注解示例于 CPython 3.11.13 重放。
> - venv 与包安装：[Python 3.11 venv](https://docs.python.org/3.11/library/venv.html)、[Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/installing-packages/)，核对于 2026-11-06。
## 26. Python 实例属性何时来自对象字典，何时变成描述符或绑定方法？

**案例：** 合成报表对象需要拒绝空标题；读者还要理解为什么直接往实例字典塞入同名键有时无效、有时能覆盖类属性。验证代码还组合了审计、规范化 mixin（混入类）与共同基类：调用 super() 时，问题不是“调用语法上写的父类”，而是“当前类 method resolution order（方法解析顺序，MRO）中的下一个实现”。

~~~mermaid
flowchart TD
    Get[读取 obj.name] --> MRO["在 type(obj) 的 MRO 找类属性"]
    MRO -->|找到候选| Data{候选是带 __get__ 的数据描述符?}
    MRO -->|没有候选| Dict
    Data -->|是| DGet[调用 descriptor.__get__]
    DGet -->|返回值| Result[返回值]
    DGet -->|抛 AttributeError| Hook{定义了 __getattr__?}
    Data -->|否| Dict{obj.__dict__ 有 name?}
    Dict -->|有| Instance[返回实例值]
    Instance --> Result
    Dict -->|没有，MRO 有类候选| Getter{候选有 __get__?}
    Dict -->|没有，MRO 无类候选| Hook{定义了 __getattr__?}
    Getter -->|是| CallGet[调用 descriptor.__get__]
    Getter -->|否| ClassValue[返回 MRO 中的类候选值]
    CallGet -->|返回值，函数会绑定实例| Result
    CallGet -->|抛 AttributeError| Hook
    ClassValue --> Result
    Hook -->|是| Fallback[调用 __getattr__]
    Hook -->|否| Raise[向调用方抛 AttributeError]
    Fallback --> Result
~~~

图按默认实例查找说明路径：若默认查找（包括实例字典）仍未找到属性，或候选描述符的 `__get__` 抛出 AttributeError，默认 `__getattribute__` 会抛 AttributeError；普通点号访问随后会调用类定义的 `__getattr__`，若没有该方法则把 AttributeError 交给调用方。实际项目若覆写 `__getattribute__`、使用特殊代理或 class/metaclass 属性访问，行为还会增加一层。本章只解释普通实例的属性读取和协作式多继承。

### 同名实例值为什么压不过一个字段验证器？

descriptor（描述符）是定义了 `__get__`、`__set__` 或 `__delete__` 的对象。描述符必须放在类属性上才参与点号访问。定义 `__set__` 或 `__delete__` 会让它成为 data descriptor（数据描述符）；本节的描述符还定义 `__get__`，因此读取时优先于实例字典。只有 `__get__` 的则是 non-data descriptor（非数据描述符），实例值可以把它盖住。

下面用一个数据描述符检查报表标题。`__set_name__` 在类创建时取得属性名；验证后的值存在实例字典的另一个键中，避免描述符递归调用自己。

~~~python
class NonEmptyText:
    def __set_name__(self, owner, name):
        self.storage_name = "_" + name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__.get(self.storage_name)

    def __set__(self, instance, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("title must contain non-whitespace text")
        instance.__dict__[self.storage_name] = value.strip()


class Report:
    title = NonEmptyText()

    def __init__(self, title):
        self.title = title

    def publish(self):
        return "published: " + self.title


report = Report("  Monthly summary  ")
print(report.title)
report.__dict__["title"] = "forged instance value"
print(report.title)
try:
    report.title = "   "
except ValueError as error:
    print(type(error).__name__, str(error))
~~~

CPython 3.11.13 的输出是：

~~~text
Monthly summary
Monthly summary
ValueError title must contain non-whitespace text
~~~

实例字典此时有 _title 和 title 两个键，但读取 report.title 会先找到类上的 NonEmptyText，再调用它的 `__get__`；名为 title 的字典值不会胜出。赋值 report.title=... 同样先调用 `__set__`，因此验证器能规范化有效输入并拒绝空白输入。这个写法适合字段校验、延迟加载或受控计算；要小心避免描述符内部写回自身管理的同名属性。

### 为什么方法会绑定 self，又为什么实例能临时覆盖？

类中定义的普通函数也是非数据描述符。读取 report.publish 时，函数的 `__get__` 将它绑定成方法对象，方法的 `__self__` 指向 report；调用 report.publish() 等价于把该实例作为第一个参数传入函数。

~~~python
bound = report.publish
print(bound.__self__ is report)
print(bound())
report.__dict__["publish"] = "temporary label"
print(report.publish)
~~~

输出依次是 True、published: Monthly summary 和 temporary label。函数属于非数据描述符，因此实例字典的 publish 值优先。类上的函数才会发生这种绑定；若把一个普通函数直接放进实例字典，它不会自动转成绑定方法。这个区别解释了测试中为何给一个实例临时赋值可以替换方法，以及为什么这类 monkey patch（运行时替换）只影响该实例。

普通属性查找可以用优先级表概括：

| 查找结果 | 实例字典有同名键 | 读取结果 |
| --- | --- | --- |
| 带 `__get__` 的数据描述符，例如 NonEmptyText | 有或没有 | 描述符的 `__get__` 结果 |
| 无类候选，或候选不是带 `__get__` 的数据描述符 | 有 | 实例字典中的值 |
| 有 `__get__` 的非数据描述符，例如方法函数 | 没有 | 调用 `__get__`；普通函数会绑定实例 |
| 没有 `__get__` 的类候选，例如普通值或只有 `__set__` 的描述符 | 没有 | 返回 MRO 中的类候选值/描述符对象 |
| 无类候选 | 没有 | 调用 `__getattr__`；若没有则抛 AttributeError |

如果默认查找未找到属性，或描述符的 `__get__` 抛出 AttributeError，点号访问还会调用类定义的 `__getattr__`；若没有这个方法，AttributeError 会传给调用方。只有定义 `__set__` 或 `__delete__` 的对象属于数据描述符；但只有同时有 `__get__` 时，它才会在读取时按数据描述符路径优先于实例字典。类属性查找、元类上的描述符与自定义 `__getattribute__` 的细节不在这张实例查找表内。

### 菱形继承中 super() 到底走向哪里？

假设标题检查接收字符串并由多个可组合的验证步骤构成：审计 mixin 记录验证执行顺序，规范化 mixin 去除首尾空格，共同基类作最终非空验证。两种 mixin 都继承 FieldBase，形成一个菱形：

~~~python
events = []


class FieldBase:
    def validate(self, value):
        events.append("FieldBase")
        if not value:
            raise ValueError("empty title")
        return value


class NormalizeMixin(FieldBase):
    def validate(self, value):
        events.append("NormalizeMixin.before")
        result = super().validate(value.strip())
        events.append("NormalizeMixin.after")
        return result


class AuditMixin(FieldBase):
    def validate(self, value):
        events.append("AuditMixin.before")
        result = super().validate(value)
        events.append("AuditMixin.after")
        return result


class MonthlyTitleField(AuditMixin, NormalizeMixin):
    def validate(self, value):
        events.append("MonthlyTitleField")
        return super().validate(value)


field = MonthlyTitleField()
result = field.validate("  Monthly summary  ")
print([cls.__name__ for cls in MonthlyTitleField.__mro__])
print(result)
for event in events:
    print(event)
~~~

运行输出：

~~~text
['MonthlyTitleField', 'AuditMixin', 'NormalizeMixin', 'FieldBase', 'object']
Monthly summary
MonthlyTitleField
AuditMixin.before
NormalizeMixin.before
FieldBase
NormalizeMixin.after
AuditMixin.after
~~~

C3 线性化算法的约束是保留每个父类自身的顺序，同时保留子类声明的直接父类顺序。可手推为：

~~~text
L(AuditMixin)        = [AuditMixin, FieldBase, object]
L(NormalizeMixin)    = [NormalizeMixin, FieldBase, object]
L(MonthlyTitleField) = [MonthlyTitleField] + merge(
    [AuditMixin, FieldBase, object],
    [NormalizeMixin, FieldBase, object],
    [AuditMixin, NormalizeMixin]
)
~~~

merge 每轮从输入列表左到右扫描，取第一个不在任何列表尾部中的首项；“尾部”指每个列表去掉首项后的剩余元素。取出的首项从它所在的各个列表中移除。先取 AuditMixin：它是第一条列表和直接父类顺序列表的首项，且不在任何列表尾部。移除后，第一条列表的首项 FieldBase 出现在第二条列表的尾部 `[FieldBase, object]`，所以暂不能取；接着选中第二条列表和直接父类列表的首项 NormalizeMixin。随后依次取 FieldBase、object。于是 MRO 是 MonthlyTitleField → AuditMixin → NormalizeMixin → FieldBase → object。

所以 MonthlyTitleField 内的 super() 找到 AuditMixin；AuditMixin 内的 super() 仍从实例真实类型 MonthlyTitleField 的 MRO 继续，下一站是 NormalizeMixin，而不是 AuditMixin 在定义时写出的直接基类 FieldBase。NormalizeMixin 再交给 FieldBase，基类只执行一次。依本例输入，执行序列为包装层、审计前置、规范化前置、基础检查、规范化收尾、审计收尾。

协作式 mixin 的每个实现都要遵守共同约定：接受兼容的参数，并在恰当位置调用 super()。若某个 mixin 直接返回而不继续调用，后续步骤会被截断；若不同实现对同名方法的参数约定不兼容，也无法可靠地串起来。多继承适用于确实需要按 MRO 组合的横切行为；若顺序与协作约定难以说清，组合对象或显式调用步骤通常更容易维护。

如果要继续看对象名称绑定、可变性、迭代器和资源生命周期，见[Python 的值、迭代器与资源生命周期如何工作？](#25.%20Python%20%E7%9A%84%E5%80%BC%E3%80%81%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E8%B5%84%E6%BA%90%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E5%A6%82%E4%BD%95%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

> [!info]- 来源
> - 描述符类型、实例属性和类属性的读取优先级、函数方法绑定及 C3 MRO：[Python 3.11 Language Reference, Data Model](https://docs.python.org/3.11/reference/datamodel.html)，§3.3.2.3、§3.2.8.2，核对于 2026-11-09。
> - 描述符仅通过类属性触发、`__set_name__` 的用途：[Python 3.11 Descriptor HowTo Guide](https://docs.python.org/3.11/howto/descriptor.html)，Descriptor Protocol，核对于 2026-11-09。
> - 示例中的实例字典、描述符遮蔽与 MRO 调用次序已在 CPython 3.11.13 实跑；这里只检查普通实例属性，不声称覆盖自定义元类或 `__getattribute__`。
## 27. 异步 FastAPI 接口为什么仍会阻塞？

**案例：** FastAPI 报表接口收到 acct-17 的查询，异步数据库驱动要等数页结果；同一 worker 还必须及时回应其他请求。async def 只是协程函数声明，只有执行到会挂起的 await 才能把事件循环让给别的任务。同步阻塞调用仍会占住当前线程，资源也必须活到最后一次使用它的响应阶段。

~~~mermaid
flowchart TD
    Route[报表请求进入路由] --> Library{底层库提供哪种接口？}
    Library -->|原生 async API| Await[async def 中 await]
    Library -->|同步阻塞 I/O| Sync[FastAPI 调用 def 路由/依赖]
    Library -->|同步辅助函数| Inline{是否由 async 路由直接调用？}
    Inline -->|是，直接调用| Block[当前事件循环被阻塞]
    Inline -->|否，主动卸载| DefaultExec[asyncio.to_thread 默认 executor]
    Sync --> Pool[Starlette / AnyIO 同步线程池]
    Library -->|大量纯 Python CPU 计算| Process[有界进程/计算 worker]
    Await --> Resource[资源活到最后一次读取或响应结束]
    Sync --> Resource
    DefaultExec --> Resource
    Process --> Resource
~~~

### 从 async def 到运行中的协程，中间发生什么？

调用 async def 函数只会构造并返回协程对象，函数体此时尚未执行；await 它或用 asyncio.create_task() 将它调度为 Task 后，函数体才开始运行。await 在等待一个尚未完成的可等待对象时暂停当前任务，事件循环可以推进其他就绪任务。被创建的任务仍由创建者或结构化并发作用域负责收集结果和等待结束。在 Python 3.11 中，TaskGroup 会在离开作用域前等待组内任务完成。

await 并不保证一定让出线程：若等待的对象已经就绪，代码可以继续推进。time.sleep()、同步数据库驱动或长时间 Python 循环则不会让事件循环调度别的任务。一个同步辅助函数如果从 async def 路由中直接调用，只是普通函数调用，FastAPI 不会自动把它移到线程池。

按驱动来选择接口：有原生 async 数据库或 HTTP 客户端时，在 async 路由中 await 它；若只能使用同步阻塞 I/O，可以把 FastAPI 路由或依赖本身声明为 def，由 Starlette/AnyIO 的同步工作线程池运行；短期兼容阻塞 I/O 时也可用 asyncio.to_thread()。这两者是不同的线程池，独立受限：框架调用的同步路由/依赖走 AnyIO 池，asyncio.to_thread() 走事件循环的默认 executor。应用要分别配置和计入它们的容量。FastAPI 只会对它负责调用的同步路由和依赖做调度，async 路由里直接调用的同步辅助函数仍在当前线程运行。

对纯 Python CPU 工作，CPython 3.11 的 Global Interpreter Lock（全局解释器锁，GIL）通常让多个线程不能同时执行 Python 字节码；to_thread 是避免阻塞事件循环的 I/O 选项，不是通用 CPU 并行开关。进程池或独立 worker 可以并行计算，但会增加序列化、进程启动、内存和排队成本。CPython 3.13 引入实验性的自由线程构建；3.14 起它成为正式支持的可选构建，但不是默认解释器，未适配的扩展还可能重新启用 GIL。运行效果取决于实际解释器和依赖，应测量确认。无论哪种卸载方式，都要限制 worker 数及等待队列。

### 任务取消时，函数、线程和远端操作分别会怎样？

Task.cancel() 会安排在事件循环下一次机会把 CancelledError 注入协程。任务可以在 finally 中释放资源；清理完成后通常应让取消继续传播。TaskGroup 和 timeout scope 也依赖取消传播，不要把 CancelledError 当作普通业务异常吞掉。

asyncio.timeout(秒数) 需要事件循环重新获得调度机会才能送达取消。如果事件循环被同步函数堵住，超时回调无法运行；阻塞调用返回后，若代码在让出控制权前已退出 timeout 上下文，超时甚至可能完全不触发。本机 CPython 3.11.13 中，`asyncio.timeout(0.01)` 包住 `time.sleep(0.05)` 正常退出，耗时约 0.06 秒。对 await asyncio.to_thread(blocking_call)，取消当前 Task 会让调用方停止等待结果，却不能强制停止已经开始运行的线程函数。底层线程可能继续占用文件、连接或 CPU，所以不要在任务已取消时立刻关闭仍被它使用的连接池。

HTTP 客户端超时或断线也不能证明远端副作用已经停止。一次请求超时后，写入可能尚未到达服务、可能回滚，也可能已经提交但响应丢失；耐久 job 需显式取消，并从权威状态确认结果，见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

### FastAPI 的 yield 依赖应何时释放？

一个 yield 依赖的生命周期要覆盖它最后一次被使用的时点。FastAPI 中未指定 scope 时，带 yield 的依赖默认是 request scope：依赖在路由前打开，在 response 处理完成后关闭。若路由返回的 StreamingResponse 仍要读取数据库游标，就让 request scope 一直覆盖流生成。只有路由返回后不再需要该资源，才用 Depends(scope="function")，这样清理发生在发送响应前。

这条 StreamingResponse 路径在请求内直接向客户端发送正文；连接和游标活到正文结束或请求取消。持久导出是另一条路径：先同事务接受 job、outbox 和等待槽并返回 202，后台 worker 再写 CSV 私有对象；上传与结果引用提交后才把 job 标为 succeeded。客户端断开不能替代 job 取消。

~~~mermaid
sequenceDiagram
    participant F as FastAPI
    participant D as yield 依赖
    participant R as 路由函数
    participant B as 响应正文生成器
    F->>D: 打开会话或游标
    F->>R: 调用路由
    R-->>F: 返回响应
    alt function scope
        F->>D: 先清理依赖
        F->>B: 发送响应正文
    else request scope（默认）
        F->>B: 生成并发送正文
        B->>D: 流式读取时继续使用资源
        F->>D: 请求响应生命周期结束后清理
    end
~~~

下面的路由片段只展示资源和调度边界。真实服务中的数据库驱动、超时和流式响应都应按本机库契约替换。

~~~python
import asyncio
import time

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

class Store:
    async def get(self):
        print("read")
        await asyncio.sleep(0)
        return "report row"

async def get_store():
    print("open")
    try:
        yield Store()
    finally:
        print("close")

def load_settings():
    return {"region": "demo"}

@app.get("/row")
async def read_row(
    settings=Depends(load_settings),
    store=Depends(get_store, scope="function"),
):
    async with asyncio.timeout(0.5):
        return {"region": settings["region"], "row": await store.get()}

def blocking_io():
    time.sleep(0.06)
    return "done"

@app.get("/blocking")
async def blocking_route():
    return {"result": blocking_io()}

@app.get("/offloaded")
async def offloaded_route():
    try:
        return {"result": await asyncio.to_thread(blocking_io)}
    except asyncio.CancelledError:
        # 取消当前等待任务不会强停已经开始的 blocking_io 线程。
        raise

@app.get("/stream")
async def stream(store=Depends(get_store)):
    async def body():
        print("body")
        yield await store.get()

    return StreamingResponse(body(), media_type="text/plain")
~~~

`/row` 的 function-scope 依赖事件顺序是 `open → read → close`；`/stream` 默认 request scope 的顺序是 `open → body → read → close`。这是依赖和生成器事件 trace，不是对 ASGI response send 次序的测量。0.5 秒 timeout 只是示例预算；真实应用的 session、事务和数据库连接是不同资源，每个请求或 worker attempt 都要有独立短生命周期，不能把同一个 ORM Session 共享给并发 Task。见[如何限定 ORM Session 并排查连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。若流生成器需要游标，依赖的 scope 必须覆盖最后一次游标读取；一个后台 job 则应在自己的执行生命周期内重新取得资源。

本机 CPython 3.11.13、FastAPI 0.128.0、Starlette 0.47.2、HTTPX 0.28.1 上用独立 smoke 驱动核对过这些机制：同步依赖被移出事件循环线程；同步阻塞调用会拖慢同时请求；运行中的 `to_thread` 函数在等待它的 Task 被取消后仍完成。取消请求测试使用 HTTPX `ASGITransport` 并在同进程取消 ASGI 调用 Task；这不等于真实 TCP 客户端断线，也不据此推断服务器断线后的资源行为。FastAPI 版本会影响依赖生命周期选项，升级时应核对所装版本。

> [!info]- 来源
> - Python 3.11 协程、TaskGroup、Task.cancel()、timeout 与 to_thread：[Python 3.11 asyncio tasks](https://docs.python.org/3.11/library/asyncio-task.html)，Task取消和后台线程示例于 CPython 3.11.13 重放。
> - asyncio.to_thread() 调用事件循环默认 executor 的实现：[CPython 3.11, Lib/asyncio/threads.py](https://github.com/python/cpython/blob/3.11/Lib/asyncio/threads.py)；阻塞函数已运行后不能由取消 awaiter 强制停止，线程验证于 CPython 3.11.13 重放。
> - 已经运行的 callable 不能由 Future.cancel() 强制取消：[Python 3.11 concurrent.futures](https://docs.python.org/3.11/library/concurrent.futures.html#concurrent.futures.Future.cancel)，已运行线程示例于 CPython 3.11.13 重放。
> - async 函数、生成器和协程对象的语言定义：[Python 3.11 Language Reference, Data model](https://docs.python.org/3.11/reference/datamodel.html#coroutine-functions)。
> - CPython 自由线程模式的可选构建、运行时 GIL 状态和扩展兼容边界：[Python support for free threading](https://docs.python.org/3/howto/free-threading-python.html)；3.14 正式支持标准见 [PEP 779](https://peps.python.org/pep-0779/)，核对于 2026-11-06。
> - FastAPI 对同步路由/依赖与异步路由的调度边界：[FastAPI, Concurrency and async / await](https://fastapi.tiangolo.com/async/)，核对于 2026-11-06。
> - 同步路由/依赖使用 AnyIO 线程容量、且 Starlette 内其他同步操作共用该限制：[Starlette, Thread Pool](https://www.starlette.io/threadpool/)；AnyIO 的限制不影响 asyncio 默认 executor：[AnyIO, Working with threads](https://anyio.readthedocs.io/en/stable/threads.html)，核对于 2026-11-06。
> - yield 依赖默认 request scope 与 function scope 的清理时点：[FastAPI, Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)，核对于 2026-11-06；0.128.0 路由 resolver 实现见 [dependency utilities](https://github.com/fastapi/fastapi/blob/0.128.0/fastapi/dependencies/utils.py)。
## 28. 如何估算并限制异步工作管线？

**案例：** API 接到 acct-17 的账户报表请求：先验证并持久接受任务，后台 worker（工作进程）顺序读数据库并生成 CSV，最后写入私有对象存储。受理事务同时写 job、outbox 和一个共享等待槽，提交后才返回 `202`；只有对象上传完成、结果引用与 `succeeded` 状态提交后，报表才可查询。这里估算的是这条持久后台导出路径。直接用 HTTP 流式响应是另一条请求内路径：连接和流资源要活到正文发送完或请求取消，不会自动变成可查询的 job 结果。

要决定接多少任务，必须同时看准入速率、等待上限、每个执行槽的处理时间、数据库连接和输出体量。队列能保留待办工作，却不会自动增加处理能力。

容量规划中的 admission control（准入控制）决定是否接受新工作；backpressure（背压）把下游拥塞反馈给上游。两者都要与任务槽位和连接池的所有权一起定义。

~~~mermaid
flowchart LR
    Request[提交报表] --> Rate{速率预算可用？}
    Rate -->|否| Reject[拒绝，尚未承诺受理]
    Rate -->|是| Slot{共享等待槽可用？}
    Slot -->|否| Reject
    Slot -->|是| Persist[同一事务：写 job、outbox 与一个等待槽]
    Persist --> Relay[relay 发布 outbox]
    Relay --> Broker[message broker（消息代理）]
    Broker --> ExecSlot{worker 已取得执行槽？}
    ExecSlot -->|否| Broker
    ExecSlot -->|是| Claim[条件领取 job]
    Claim --> Active[领取时释放等待槽；执行槽继续归 worker]
    Active --> Settle[尝试完成或确认停止并清理]
    Settle --> Free[归还执行槽]
    Broker -->|重投仍是同一逻辑 job| Broker
~~~

等待槽属于尚未被 worker 领取的逻辑 job。API 在同一数据库事务提交 job、`pending` outbox 行和等待槽；relay 重发同一 outbox 意图、broker 重复投递时都不新占槽。worker 必须在领取前先预占一个执行槽；没有执行槽就不领取、不确认消息，并把预取和本地待处理消息限制在执行容量内。条件更新成功时 job 变为 `running`、等待槽释放，执行槽由 worker 持有；若消息重复、job 已终态或条件领取失败，就归还刚预占的执行槽。等待中的 job 若在领取前取消或转为其他终态，状态变化与释放等待槽必须同事务进行且只释放一次。

成功领取后执行槽一直由该物理 attempt 持有，直到该尝试确实停止运行、不再使用它持有的连接、游标或上传句柄后才归还。不要仅因数据库状态变化就释放物理槽，也不必为了回收异步孤儿对象而继续占着已停止 worker 的执行槽；孤儿对象由独立的清理责任方按宽限期处理。请求超时、发出取消信号、租约到期都不能单独证明执行停止。租约到期后，恢复器先检查取消请求：若 job 已请求取消，就条件提交终态，不重排；若仍可重试且能取得新等待槽，则用条件更新 fencing（隔离旧 attempt 对结果的写入权），并在同一事务中把逻辑 job 重排、写新的 outbox 意图。这不代表旧 worker 的计算、连接或游标已经停止。被 fencing 的旧 attempt 仍占原物理执行槽到实际退出并释放正在使用的资源，新 attempt 领取时另取一个执行槽。若是已确定结束的普通失败，完成资源清理后再为重试预留等待槽。租约接管和旧结果 fencing 的状态转移见[怎样设计可持久查询的账户报表？](#%E5%B7%A5%E4%BD%9C%E8%BF%9B%E7%A8%8B%E9%87%8D%E8%AF%95%E6%80%8E%E6%A0%B7%E9%81%BF%E5%85%8D%E6%97%A7%E7%BB%93%E6%9E%9C%E8%A6%86%E7%9B%96%E6%96%B0%E7%BB%93%E6%9E%9C%EF%BC%9F)。

### 用平均在途量估算，不要把平均值当峰值保证

先给公式里的量对齐单位和边界。若一个稳定系统平均每秒接受 40 个请求，每个请求在该系统内平均停留 0.2 秒，则平均在途请求约为 40 次/秒 × 0.2 秒 = 8 个。这是 Little 定律（Little's Law）：平均在系统中的任务数 = 平均到达速率 × 平均停留时间。若 W 包含排队，就必须把同一个队列纳入系统边界；若只算 worker 执行时间，就不能把排队延迟偷偷算进 W。

这个关系描述长期平均量，不能推出峰值吞吐、p95/p99 时延或安全并发上限。需求成批到达、重试、变长任务和下游资源限制都要另外测量。队列长度（queue depth）说明有多少任务在等；queue age（队列等待时长）说明最老任务等了多久，两者都应跟踪。

### 合成账户报表要预留多少执行槽？

下表是用于演算的合成输入，不是生产测量、服务目标或默认推荐值。

| 输入 | 假设 |
| --- | ---: |
| 新幂等键产生的平均与 10 分钟峰值 job 提交速率 | 5 / 20 个每秒 |
| 单个请求大小 | 8 KiB |
| 提交事务持有数据库连接 | 10 ms |
| 每份报表的顺序索引读取 | 12 次，每次借连接 20 ms |
| worker 每个 attempt 平均处理时间 | 6 s |
| 每份结果与每个 job 元数据 | 128 KiB / 2 KiB |
| 结果对象与终态/幂等元数据保留期 | 7 天 / 终态后 14 天 |

先假设每份报表只执行一个 attempt，且重试、恢复和失败清理额外耗时不计入 6 秒。平均到达 5 份/秒、平均 attempt 处理 6 秒，对应 5 × 6 = 30 个平均在途 attempt。若 10 分钟峰值 20 份/秒都被接受，则需要约 20 × 6 = 120 个平均并发 attempt。4 个后台 worker 副本、每副本 2 个进程、每进程 8 个并行 attempt 槽，一共是 4 × 2 × 8 = 64 个执行槽。

64 个执行槽全满时，按 6 秒平均处理时间，理想平均服务率是 64 / 6 ≈ 10.67 个 attempt/秒。若规划时先把平均利用率压在假设的 70%，估算速率为 64 × 0.70 / 6 ≈ 7.47 个/秒。将 token bucket（令牌桶）准入目标设为 7 份报表/秒，则按每份一次 attempt 估算会占用 7 × 6 / 64 ≈ 65.6% 的槽。70% 和 7 个/秒只是后续负载测试的起点，不是实测容量承诺；重试会占用额外 attempt 槽。

准入速率和等待队列要分别封顶。本例假设持续准入 7 份/秒、短时突发 30 份、所有 outbox 与 broker 队列中最多 240 个已接受未领取的逻辑 job。受理前，在同一事务里持久化 job、outbox 发布意图并原子预留一个共享等待槽；outbox 和 broker 之间迁移同一个 job 不再占第二槽。worker 有执行槽后才条件领取；领取事务只释放该 job 当前排队轮次的等待槽一次。领取前取消的 job 转终态时，也要在同一条件状态转移中释放等待槽一次。运行中的 job 只有在 attempt 实际完成或已确认停止、不再使用实时资源后才能归还该物理 attempt 的执行槽；若租约恢复已 fencing 旧 attempt，恢复器只在 job 未请求取消且取得新等待槽时才能重排并写 outbox，旧物理执行槽仍占用，新 attempt 领取时另取执行槽。重试重排须同事务再次取得等待槽并写新的 outbox 意图；没有槽位就记录可查询的容量失败状态，不得无界重发。

若 20 个/秒的新幂等键提交持续 600 秒，共有 12,000 个新的逻辑 job 意图到达。令牌桶最多准入 7 × 600 + 30 = 4,230 个，因此在共享等待槽和其他限额没有更早拒绝的假设下，至少 12,000 − 4,230 = 7,770 个新逻辑 job 不能受理。相同幂等键重放会返回原 job，不在这组新 job 到达量中，也不再占一个令牌或等待槽；重放 HTTP 请求本身仍消耗 API 服务容量。速率或等待槽已满时返回明确过载错误，不能返回 202 Accepted（已受理）后再悄悄丢任务。完整 job 状态和事务边界见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 进程内连接池怎样叠加成数据库总预算？

连接池通常由每个应用进程持有；扩容进程会复制池上限，多个服务还会争用同一数据库预算。假设本例 API 和 worker 都部署 4 个副本、每副本 2 个进程，每个进程使用 SQLAlchemy QueuePool，配置 pool_size=8、max_overflow=2：

| 连接使用者 | 最大上限计算 | 连接上限 |
| --- | ---: | ---: |
| API：4 个副本，每副本 2 个进程 | 4 × 2 × (8 + 2) | 80 |
| worker：4 个副本，每副本 2 个进程 | 4 × 2 × (8 + 2) | 80 |
| 其他共用数据库的服务 | 本例预留 | 40 |
| 应用配置总上限 | 80 + 80 + 40 | 200 |
| 教学用数据库连接预算 | 本例假设 | 240 |
| 未分配余量 | 240 − 200 | 40 |

这是并发借出连接的配置上限，不是数据库此刻一定会有 200 条活跃连接；池也可能保留已连接但空闲的物理连接。单份报表读取的 connection-seconds（连接秒）为 12 × 0.020 秒 = 0.24；按 5 个报表/秒估算，平均约有 5 × 0.24 = 1.2 条连接被报表读取借出。若假设峰值 20 个/秒都被接受，该数为 4.8；10 ms 的提交事务另加 0.05 条平均借出连接，峰值假设下另加 0.2 条。平均借出量是需求估算，连接预算仍应按各进程池上限核算。每进程连接池上限与 checkout 等待见[怎样限定 ORM Session 并排查连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。

### 结果存储和请求字节量会涨到多少？

按 5 份报表/秒、每份结果 128 KiB，长期平均结果写入速率是 640 KiB/s。七天是 7 × 24 × 60 × 60 = 604,800 秒；若都保留，结果数据体量约为：

~~~text
128 KiB × 5/s × 604,800 s ÷ 1,048,576 KiB/GiB = 369 GiB
~~~

这还没计入索引、复制、压缩和清理滞后。结果对象保留七天约占 `128 KiB × 5/s × 604,800 s ÷ 1,048,576 ≈ 369 GiB`。假设每个 job 的 2 KiB 终态/幂等元数据在完成后保留 14 天，近似体量是 `2 KiB × 5/s × 1,209,600 s ÷ 1,048,576 ≈ 11.54 GiB`，未计索引；处理时长和清理滞后会略微增加实际在库行数。若准入后以 7 份/秒持续完成，结果速率约 0.875 MiB/s；30 个 job 的突发全部完成时约生成 3.75 MiB。当前 64 槽、6 秒平均处理时间对应的理想持续完成率是 10.67 份/秒，结果写入约 1.33 MiB/s；实际要以对象上传、worker 执行和数据库状态提交测量，不能把 20 个/秒的提交峰值当作可达到的完成速率。下载流量要和报表生成分开预算。

### 如何确认最先到达的瓶颈？

在这些假设下，峰值按时处理需要 120 个平均并发 job，而计划只有 64 个槽，因此 worker 执行槽先于列出的连接配置上限达到规划值。这只是排查顺序的假设，不表示数据库 CPU、存储 I/O 或网络已经有余量。

用代表性的 8 KiB 请求、12 次读取扇出和输出大小逐步加压，再单独试 20/秒突发、满队列、慢读、重试和 worker 丢失。分别记录 API 接受延迟、job 排队时长、生成时长、下载时长，以及 p50、p95、p99（第 50、95、99 百分位）延迟分位数。6 秒是平均处理时长，只能用于这次平均在途量估算，不能写成 p95 保证。观测活动槽位、共享等待槽、最老队列年龄、数据库 checkout 等待和 CPU、结果留存量、完成与失败状态，再按真实 service-level objective（SLO，服务级目标）决定扩副本、改准入还是优化查询。[可观测性、SLO 与事件响应](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)说明如何按各阶段检查饱和与延迟。

**接下来：** 本章把任务、排队和连接限制到同一工作负载假设；应用是否需要异步 job 以及完整持久生命周期见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)，消息确认语义见[发布者确认和消费者确认分别证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - Little 定律成立条件、平均数和系统边界：[Little, “A Proof for the Queuing Formula: L = λW,” Operations Research 9(3), 1961](https://doi.org/10.1287/opre.9.3.383)，该关系对应长期稳定系统的平均量。
> - SQLAlchemy 2.1.8 QueuePool 的 pool_size + max_overflow 同时连接上限：[SQLAlchemy 2.1, Connection Pooling](https://docs.sqlalchemy.org/en/21/core/pooling.html)，官网版本与行为核对于 2026-11-06；部署到其他池实现时按实际配置重算。
> - 延迟分布分位数与服务目标的关系：[Google SRE Workbook, Implementing SLOs](https://sre.google/workbook/implementing-slos/)，核对于 2026-11-06。
> - 表中工作负载与容量数字均为按上述显式假设重算的合成算例，不是服务测量。
## 29. Web 服务如何限制拒绝服务的影响？

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

速率限制是准入政策，不会给出一个“安全的 QPS”。容量章负责在正常负载下估算资源与背压，见[如何估算并限制异步工作管线？](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)；本章强调在攻击者可分布请求、上游容量会饱和且不同请求成本悬殊时，应由哪一层拒绝或削减工作。

### 限额触发时如何让客户端和服务一起恢复？

若单个调用方超过合同额度，API 可按其错误契约返回 `429 Too Many Requests`，并选择用 `Retry-After` 建议等待时间；若服务整体暂时不能处理，请求也可能得到 `503 Service Unavailable`。这些状态表达本次 HTTP 请求结果，不会自行清除队列或建立未来重试。客户端应遵守等待时间，并用带抖动的指数退避避免一群用户同时重试；对于有副作用的 POST，还要先按[请求超时后的结果确认与安全重试契约](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)处理未知结果。

当入口流量超过上游能力时，应用返回 429/503 并不能帮助未到达应用的请求；要让上游服务商启动预案。当应用数据库或 worker 过载时，边缘可先挡掉已知攻击形态，但 API 还要把并发和队列限制在下游可承受范围，不能让短时间增长的队列拖垮健康的请求。限额和降级策略要配合服务目标，也要监控拒绝比例、合法租户成功率、数据库等待和可用容量，才能判断是不是阻断了攻击同时误伤正常读者。

> [!info]- 来源
> - 分布式流量、IP 欺骗、攻击类别、预防和响应步骤：[CISA、FBI、MS-ISAC, Understanding and Responding to Distributed Denial-of-Service Attacks](https://www.cisa.gov/sites/default/files/2024-03/understanding-and-responding-to-distributed-denial-of-service-attacks_508c.pdf)，2024-03-21，§2–§5；核对于 2026-11-06。
> - 网络与应用层 DoS、限速以及可消耗资源的应用输入：[OWASP Denial of Service Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html)，Fundamentals、Application Attacks、Network Attacks、Rate Limiting，按 2026-11-06 版本核对。
> - `429 Too Many Requests` 与可选 `Retry-After`：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，§4，2012-04；临时过载 `503` 与等待建议字段：[RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§10.2.3、§15.6.4，2022-06。均核对于 2026-11-06。
## 30. 怎样用最小反例定位报表授权回归？

报表平台工程师收到一条跨租户访问回归：tenant-a 读自己的 report 42 应返回 200，tenant-b 猜中同一 ID 也只能得到 404。为了定位并修复回归，先把需求改写成可观察结果，再提出一个能被反例推翻的根因假设。若新改动让 B 得到 200，就沿主体、application programming interface（应用程序接口，API）路由、查询和序列化追踪请求，而不是先猜数据库或框架有问题。针对该边界的可运行测试见[测试如何证明报表服务改动？](#31.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E6%B5%8B%E8%AF%95%E8%BE%B9%E7%95%8C%E9%AA%8C%E8%AF%81%E4%B8%80%E6%AC%A1%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E6%94%B9%E5%8A%A8%EF%BC%9F)。

~~~mermaid
flowchart TD
    A[可信主体为 tenant-b，请求 report 42] --> B[主体依赖得到当前租户]
    B --> C[路由把主体交给数据查询]
    C --> D{查询同时限制租户与报表 ID？}
    D -->|否| E[返回其他租户的行]
    D -->|是| F[查无匹配行，返回 404]
~~~

这张图标出三处必须核对的交接：主体依赖是否正确给出当前租户，路由是否把它传入查询，查询是否把主体范围用于取行。一个响应状态只能提示失败发生了，不能单独证明是哪一处失效。

### 先把症状变成可证伪假设

假设一次自动化重构把原有的租户范围查询：

~~~python
report = session.scalar(
    select(Report).where(
        Report.report_id == report_id,
        Report.tenant_id == tenant_id,
    )
)
~~~

替换成按主键直接读：

~~~python
report = session.get(Report, report_id)
~~~

这个合成模型把 report_id 设成全局主键、tenant_id 设成资源所有者，所以 session.get(Report, report_id) 是合法的主键查找，但不会验证所有权。若真实表用复合主键，get 的参数应是相应的主键 tuple；具体形式要与真实 schema 对齐。原测试只以 tenant-a 创建并读取自己的报表，因此仍然通过。这个测试确认了所有者的成功路径，却没有测试访问边界。

先写出预期观察：

| 主体 | 请求 | 预期结果 |
|---|---|---|
| tenant-a | GET /api/reports/42 | 200，返回 report 42 |
| tenant-b | GET /api/reports/42 | 404，不泄露跨租户资源是否存在 |
| 无有效主体 | GET /api/reports/42 | 401，由认证入口拒绝 |

假设是“数据读取不再依据当前 tenant_id 限定行”。最小反例只需要一条归属 tenant-a 的 report 42 和一次可信主体 tenant-b 的读取。变更前若得到 200，这支持假设；若得到 404，则应检查主体解析、更早的拒绝分支、缓存或另一条路由。反例缩小调查范围，但只有看到查询缺少租户谓词并将其与这条行记录对应起来，才定位到数据库查询根因。

### 沿调用路径找出丢失的条件

从 API 路由向内读：

1. 确认请求经过哪一个公开入口，是否经过认证依赖。
2. 看依赖返回的主体来自已验证会话或 token（令牌），而非任意客户端字段。
3. 沿函数调用检查 report_id 和 tenant_id 是否都传到数据层。
4. 查看最终 SQL 或 object-relational mapping（对象关系映射，ORM）条件、行归属以及 cache（缓存）是否绕过了同一授权范围。
5. 查看错误映射和序列化，确认不存在“查无权限行却返回成功”之类的备用分支。

在这个合成例中，路由仍然拿到了 tenant_id，但 session.get 只按主键载入记录，没有使用 tenant_id。根因是查询丢失了范围条件。聚焦修正就是重新同时约束租户和资源：

~~~python
report = session.scalar(
    select(Report).where(
        Report.report_id == report_id,
        Report.tenant_id == tenant_id,
    )
)
~~~

然后重跑所有者和非所有者测试及同一入口的邻近检查。若成功响应缓存键仅包含 report_id，数据库查询正确也可能再次泄露；缓存命中必须在返回前执行同等范围检查。这类授权边界和后台任务执行时的复验条件见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

### 独立阅读实现与测试

先从需求列预期结果，再读修改过的路由、调用者、依赖、SQL/事务和错误响应。之后阅读测试本身，判断它是否确实通过被修改的入口到达真实数据库，fixture（测试夹具）是否建立了正确主体，断言是否覆盖必须拒绝的访问。模型或生成式改动的实现与测试可能共享同一遗漏假设；全部通过也不代表遗漏的需求已被验证。

一个实际复核要把四项证据串起来：报告 42 的所有者/非所有者输入，观察到的状态码，改动前后的查询条件，以及回归断言。需要数据库约束或 broker（消息代理）的 redelivery（重投）结论时，再确认测试实际使用的引擎或 broker；模拟会话、本地重复调用和部署探针只能证明各自的接缝，不能外推到未执行的边界。

> [!example] 反例通过前后比较
> 变更前：tenant-b 请求 /api/reports/42 得到 200，支持“缺少租户范围”的假设；沿调用路径确认查询确实漏了 tenant 谓词，才定位到根因。
>
> 变更：查询从只按 report_id 读取，改为同时匹配 report_id 和主体的 tenant_id。
>
> 变更后：tenant-a 仍得到 200，tenant-b 得到 404，匿名请求得到 401。只有这些观察与需求一致，才说明当前回归已被修复；其他 query path、缓存和后台导出仍各有自己的边界。

在共享分支上保留小而聚焦的修复，用[Git 如何记录通过验收的改动？](#32.%20Git%20%E6%80%8E%E6%A0%B7%E6%8A%8A%E9%80%9A%E8%BF%87%E9%AA%8C%E6%94%B6%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%94%B9%E5%8A%A8%E5%8F%98%E6%88%90%E5%8F%AF%E8%BF%BD%E6%BA%AF%E6%8F%90%E4%BA%A4%EF%BC%9F)记录源码快照。评审时独立检查实际差异、需求边界和测试覆盖；具体的代码评审流程由团队自己的仓库政策规定。

> [!info]- 来源
> - GitHub 官方 [Reviewing proposed changes](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests) 与[Review concepts](https://docs.github.com/en/pull-requests/concepts/giving-reviews)，checked 2026-11-06：支持从差异和提交检查改动与评审意见；本文的最小反例是合成 API 的行为推演。
> - 租户授权的规范规则由[逐次授权报表资源](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)承担；本篇只用该规则定位一次 SQL 条件遗漏，不重复完整认证和授权设计。
## 31. 怎样用测试边界验证一次报表服务改动？

报表平台工程师准备发布一项租户授权修复：tenant-a 应能读取自己的 report 42，得到 200；tenant-b 猜中同一 ID 时只能得到 404。导出 job 重复投递后，任务状态和结果对象引用也只能提交一次。要判断这次改动能否发布，测试必须覆盖这些用户可观察的失败条件，而不只是确认实现和它自己生成的 happy-path 测试一起通过。

application programming interface（应用程序接口，API）集成和数据库集成分别需要真实路由与 structured query language（结构化查询语言，SQL）。若要声称 publisher confirm（发布者确认）、consumer acknowledgement（消费者确认，ACK）或部署装配正确，还要把实际 broker（消息代理）或近似生产链路纳入测试。本文 SQLite 示例验证 FastAPI 路由和 SQL，不代表 PostgreSQL、broker 或生产身份系统已经验证。

~~~mermaid
flowchart TD
    A[契约：A 读 report 42 得 200；B 得 404] --> B[单元：租户规则]
    B --> C[API + SQLite：路由、主体接缝、查询]
    C --> D[契约：与已发布响应结构比较]
    D --> E[PostgreSQL：生产数据库方言与约束]
    E --> F[RabbitMQ：发布确认、重投、消费者确认]
    F --> G[近生产旅程：组件装配与流量路径]
~~~

每升高一层，必须能指出新增层解决的失败条件。测试数量多不能替代边界正确。单个端到端测试不易定位原因，也很难覆盖大量输入；只测函数又看不到依赖装配或真实数据库行为。

### 先把风险与可证明的边界对应起来

| 要排除的失败 | 合适边界 | 该边界能给出的证据 | 不能据此声称 |
|---|---|---|---|
| 租户 A/B 条件判断颠倒 | 单元测试 | 给定主体和资源归属，访问规则输出允许或拒绝 | 真实 HTTP 路由一定调用该规则 |
| 路由忘记传租户条件、返回错状态或错字段 | API 集成 | 实际路由、参数校验、依赖注入、响应序列化和错误映射 | 真实网络或生产身份提供方正常 |
| 唯一键、回滚或条件更新不守约束 | 数据库集成 | 选定数据库执行真实表结构与 SQL | 换一个数据库也有相同锁和类型行为 |
| 新响应不兼容已发布客户端 | 契约测试 | 当前输出与已发布 schema（结构定义）/代表性旧客户端比较 | 只检查本次自动生成的 schema 就兼容旧客户端 |
| 确认或重投造成丢失、重复业务效果 | broker 集成 | 指定 broker、队列配置、ACK 模式和持久化存储共同执行交接 | 本地函数调用两次等同于 broker 重投 |
| 只有服务装配后才出现的故障 | 近生产端到端 | 真实身份、API、数据库、队列和 worker 的受控旅程 | 一个健康探针就代表用户旅程正确 |

这些边界是互补关系，不是固定的“测试金字塔”。尽量把快速、确定的检查放在靠近故障条件的位置；只有下层无法证明的属性才提高边界。前端组件和浏览器行为另由[前端测试](../../frontend/testing/frontend-testing.md)说明，本篇聚焦 API、持久化和消息交付。

### 用实际路由重放跨租户反例

先将主体边界做成可替换依赖。X-Tenant-ID 只是测试接缝，用来把 tenant-a、tenant-b 送到实际路由；生产服务必须从已验证的登录上下文取得主体，不能信任客户端任填的租户头。示意表把 report_id 设为全局主键、tenant_id 设为资源所有者；若真实表用复合主键，测试应按真实 schema 改写，不能照搬主键读取方式。

> [!example] 关键查询和断言
> 关键是查询同时约束当前租户和 report 42，且两个租户走同一个 API 路由：
>
> ~~~python
> row = connection.execute(
>     text("""
>         SELECT report_id, state FROM reports
>         WHERE tenant_id = :tenant_id AND report_id = :report_id
>     """),
>     {"tenant_id": tenant_id, "report_id": report_id},
> ).mappings().first()
>
> owner = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-a"})
> other = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-b"})
> assert owner.status_code == 200
> assert owner.json() == {"report_id": 42, "state": "ready"}
> assert other.status_code == 404
> ~~~
>
> 这组检查通过 FastAPI TestClient 进程内调用实际路由、通过 SQLAlchemy 执行参数化查询，并由 SQLite 执行真实 SELECT。它不是 mock，也没有建立网络 socket。

> [!example]- 完整 FastAPI + SQLite fixture 与 OpenAPI 检查
> 下方测试夹具为每次测试建立内存 SQLite，使用 StaticPool 让 TestClient 所在线程与数据库检查共享该连接。示例中的测试头不是真实认证协议。
>
> ~~~python
> from typing import Annotated
>
> import pytest
> from fastapi import Depends, FastAPI, Header, HTTPException, Request
> from fastapi.testclient import TestClient
> from sqlalchemy import create_engine, text
> from sqlalchemy.pool import StaticPool
>
>
> def create_app() -> FastAPI:
>     engine = create_engine(
>         "sqlite+pysqlite://",
>         connect_args={"check_same_thread": False},
>         poolclass=StaticPool,
>     )
>     with engine.begin() as connection:
>         connection.execute(text("""
>             CREATE TABLE reports (
>                 report_id INTEGER PRIMARY KEY,
>                 tenant_id TEXT NOT NULL,
>                 state TEXT NOT NULL
>             )
>         """))
>         connection.execute(
>             text("INSERT INTO reports VALUES (:id, :tenant, :state)"),
>             {"id": 42, "tenant": "tenant-a", "state": "ready"},
>         )
>
>     app = FastAPI()
>     app.state.engine = engine
>
>     def tenant_from_test_header(
>         x_tenant_id: Annotated[str | None, Header()] = None,
>     ) -> str:
>         if not x_tenant_id:
>             raise HTTPException(status_code=401, detail="authentication required")
>         return x_tenant_id
>
>     @app.get(
>         "/api/reports/{report_id}",
>         responses={
>             401: {"description": "Authentication required"},
>             404: {"description": "Not found"},
>         },
>     )
>     def read_report(
>         report_id: int,
>         tenant_id: Annotated[str, Depends(tenant_from_test_header)],
>         request: Request,
>     ):
>         with request.app.state.engine.connect() as connection:
>             row = connection.execute(
>                 text("""
>                     SELECT report_id, state FROM reports
>                     WHERE tenant_id = :tenant_id AND report_id = :report_id
>                 """),
>                 {"tenant_id": tenant_id, "report_id": report_id},
>             ).mappings().first()
>         if row is None:
>             raise HTTPException(status_code=404, detail="report not found")
>         return dict(row)
>
>     return app
>
>
> @pytest.fixture
> def client():
>     app = create_app()
>     with TestClient(app) as test_client:
>         yield test_client
>     app.state.engine.dispose()
>
>
> def test_report_scope_and_authentication(client):
>     owner = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-a"})
>     other = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-b"})
>     anonymous = client.get("/api/reports/42")
>
>     assert owner.status_code == 200
>     assert owner.json() == {"report_id": 42, "state": "ready"}
>     assert other.status_code == 404
>     assert anonymous.status_code == 401
>
>
> def test_public_schema_declares_scope_errors(client):
>     operation = client.get("/openapi.json").json()["paths"]["/api/reports/{report_id}"]["get"]
>     assert {"200", "401", "404", "422"} <= set(operation["responses"])
> ~~~
>
> 保存为 test_report_scope.py 后运行 python -m pytest -q test_report_scope.py。OpenAPI 检查说明本应用声明了哪些响应码；若要保证已有客户端兼容，仍需与已发布 schema 或代表性旧客户端比较。

若原实现只按 report_id 读取，tenant-b 的测试会得到 200，暴露缺失的租户条件。示例中 report_id 是全局主键，所以 SQLAlchemy 的 session.get(Report, 42) 能找到该行，但这不等于当前主体有权读取它；复合主键则需要不同的主键参数。修正后，所有者得到 200、越租户请求得到 404、匿名请求得到 401。相关授权规则见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

参数校验和旧客户端兼容也要分别验收：请求先通过认证后，`GET /api/reports/not-a-number` 由整数路径参数校验返回 422；没有可信主体的请求应在认证边界先得到 401。若既有客户端依赖响应中的 `state` 字段，应把上一版发布的 schema 或代表性请求/响应作为固定契约，删掉 `state` 时该契约测试应失败。当前 `/openapi.json` 只证明此版本声明了什么，不证明它仍兼容旧客户端。

> [!example] 唯一约束与重复投递的最小状态轨迹
> SQLite 演算的插入表以 `(tenant_id, request_key)` 为唯一键。首次插入影响 1 行；相同键再次插入触发唯一约束并回滚事务，查询仍只有原来的 1 行。这个约束例说明重复 insert 不会多建一行；它不等于 API 应对相同幂等键返回 409。报表接口若收到相同键和相同参数，应按[持久报表任务](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)的契约读取并返回原 job；键相同但参数冲突时再按该业务契约拒绝。
>
> 对 worker 的本地条件更新，初始行是 `pending, processed_count=0`。第一次以 `WHERE status='pending'` 更新为 `done` 并递增计数，`rowcount=1`；再次执行同一条件时 `rowcount=0`；事务后最终状态仍为 `done, processed_count=1`。这证明选定 SQLite SQL 对重复函数调用只计一次，不证明 broker 的重投、ACK 或跨进程并发契约。

若 worker（工作进程）被本地函数调用两次，只能验证数据库状态迁移是否防重；它不覆盖消息是否被 broker 接收、连接中断后怎样重投或 ACK 是否可靠。若 worker 外发邮件、付款等副作用，还要让外部动作具备操作键幂等性或经持久 outbox 处理。任务与数据库结果边界见[超时后的结果确认与安全重试](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)；发布者确认与消费者 ACK 的 broker 语义见[消息交付如何确认](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 从测试证据接到可发布的变更

测试通过只是证据链的一环。它应能指向变更需求、对应代码和具体测试数据；随后由 Git 提交固定源码快照，Docker 根据这个快照构建镜像，部署流水线再验证并晋级相同镜像。生产路径出现问题时，指标、trace 与日志用于定位是哪一环偏离。完整过程见[如何晋级已验证的报表服务产物？](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)。

> [!info]- 来源
> - 测试方式的界限：FastAPI 官方 [Testing](https://fastapi.tiangolo.com/tutorial/testing/) 说明 TestClient 对应用路由的调用，checked 2026-11-06；pytest 官方 [Fixtures reference](https://docs.pytest.org/en/stable/reference/fixtures.html) 说明 fixture 作用域和发现，checked 2026-11-06。
> - SQLite 约束与共享内存连接：SQLite [CREATE TABLE](https://www.sqlite.org/lang_createtable.html)；SQLAlchemy 2.0 官方 [SQLite 内存数据库与连接池](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads-or-coroutines)，适用于本例的 StaticPool / check_same_thread 连接安排。
> - 本地运行边界：示例执行环境为 FastAPI 0.128.0、SQLAlchemy 2.0.44、pytest 9.0.2 与系统 SQLite；它不代表 PostgreSQL 或 broker 集成测试。
## 32. Git 怎样把通过验收的报表改动变成可追溯提交？

修复 report 42 的租户条件并通过相关检查后，Git 能把已审查的源码快照变成可复查的提交。这个提交给构建系统提供固定输入，但它还不是部署产物：之后要记录由它构建出的镜像摘要，并验证、晋级那份镜像。Git 命令改变工作区、暂存区、提交或引用；它不撤销数据库迁移、已发布镜像或生产副作用。

branch（分支）是指向提交的可移动引用；working tree（工作区）保存文件，index（暂存区）保存下一次提交的快照，commit（提交）固定一棵树及父提交。区分这几层，才能选择正确的恢复动作。

创建分支只建立一个指向提交的引用，`git switch -c <name>` 也不会把未提交的工作区或暂存区改动保存成快照。要在切换任务前保护这类改动，应先提交或暂存保存，再核对恢复后的状态。

~~~mermaid
flowchart TD
    A[工作区：改了查询与测试] --> B[检查 diff 并选择文件]
    B --> C[暂存区：本次提交精确内容]
    C --> D[提交：固定源码树和父提交]
    D --> E[CI（持续集成）以提交号构建镜像]
    E --> F[镜像摘要与提交号形成可追溯映射]
    D --> G{哪里需要修复？}
    G -->|仅未共享的本地历史| H[reset / rebase]
    G -->|已经共享的提交| I[revert 新增反向提交]
~~~

### 把一个小修复明确放进暂存区

在示意仓库中，改动只包含 `src/reports.py` 的租户限定查询和 `tests/test_report_scope.py` 的非所有者断言。先查看仓库是否混有其他任务，再查看准确的差异：

~~~bash
git status --short
git diff -- src/reports.py tests/test_report_scope.py
~~~

逐文件暂存能避免把本地配置、调试输出或其他人的改动混进报告修复：

~~~bash
git add src/reports.py tests/test_report_scope.py
git diff --cached
git diff --cached --check
git status --short
git commit -m "fix(reports): enforce tenant-scoped reads"
git show --stat --oneline HEAD
git log --oneline --graph --decorate -8
~~~

commit message（提交说明）描述变化和对象，`fix(reports): ...` 属于可选的 Conventional Commits（常规提交说明格式），不是 Git 本身的要求。仓库策略若规定 squash、merge commit 或签名提交，就按该策略执行。代码审查应检查实际 diff（差异）和测试边界；提交标题不等于测试通过。

### 先检查远端，再选择 merge 或 rebase

`git fetch`（获取）更新远程跟踪引用但不改当前分支；`git pull`（拉取）执行获取后再按配置整合。可以先查看差异，再选择整合方式：

~~~bash
git fetch origin
git log --left-right --oneline --graph HEAD...origin/main
~~~

三点范围列出两边各自独有的提交；`<` 表示只在当前 `HEAD` 可达，`>` 表示只在 `origin/main` 可达。两点写法 `HEAD..origin/main` 只列远端独有提交，不能单独判断本地是否也有未发布提交。

| 当前状态 | 常见做法 | 原因 |
|---|---|---|
| 更新尚未发布的本地分支 | 按仓库政策 rebase（变基）或 merge（合并） | 变基重放提交会创建新提交 ID；合并保留双侧历史和可能的汇合点 |
| 多人已经基于该分支继续提交 | 先协调，通常不改写共享提交 | 改写会让其他人的父提交失效并要求重新整合 |
| 仓库需要显示集成节点 | merge | 合并提交可显式记录两条历史如何接合 |

例如仅有自己未推送的 `fix/report-tenant-scope` 分支，可以按团队约定 `git rebase origin/main`。若团队需要保留合并关系，则 `git merge origin/main`。两者都可能产生冲突；不要用某种分支模型替代仓库现行策略。

发生冲突时，先看带冲突标记的源文件及 `git diff --cc`。在 report42 的例子里，必须保留当前主体与报表 ID 两个条件，再解决与远端其他调整的真实冲突。检查文件、运行相应测试后暂存并继续：

~~~bash
git add src/reports.py
git rebase --continue
~~~

示例从干净工作区开始。合并未完成前可 `git merge --abort` 尝试重建合并前状态；如果开始合并时已有未提交改动，Git 在某些情况下无法完整恢复它们。变基未完成前可 `git rebase --abort`。不要把未理解的冲突整块接受为 ours 或 theirs。

### stash 与 cherry-pick 解决不同问题

临时切走时，`git stash push -m "report scope in progress"` 保存已跟踪文件的工作区和暂存区状态；默认不含未跟踪文件，需要时加 `-u`。`git stash apply` 默认重新应用改动但不保证恢复原先暂存状态；需要尽量恢复 index（暂存区）时用 `git stash apply --index`。`apply` 保留记录，`pop` 在应用成功后移除记录。应用后检查状态和冲突，不要把 stash 当成备份；重要工作还应保存在提交或其他持久位置。

`git cherry-pick <commit>`（挑选提交）把指定提交所引入的改动应用到当前分支，并创建一个新的提交。它适合把已审查的报表修复移到维护分支，但新提交 ID 不同，应记录实际运行的检查和部署构建对应的目标提交。

### 按变化所在层恢复

若只是暂存了不想提交的文件，用 `git restore --staged <path>` 保留工作区内容并移出 index；若只丢弃工作区的未暂存编辑，用 `git restore <path>`，该路径内容会被覆盖。对已经提交的共享修复，用 `git revert <commit>` 添加一个反向提交，保留原提交供历史审计。普通提交可直接指定；撤销 merge commit 时须选择主线父提交，例如 `git revert -m 1 <merge-commit>`，并先检查这个反向差异以及后续合并会受什么影响。回滚共享历史时通常用 revert，不要直接把远端分支强制指回旧位置。

| reset 方式 | branch 引用 | 暂存区 | 工作区 |
|---|---|---|---|
| `--soft <target>` | 移到目标 | 保留 | 保留 |
| `--mixed <target>` | 移到目标 | 重置为目标内容 | 保留 |
| `--hard <target>` | 移到目标 | 重置为目标内容 | 丢弃与目标不符的受跟踪改动，也可能覆盖路径 |

在未共享的本地提交上，确认工作区内容可丢弃后才考虑 `git reset --hard <target>`。若只需改提交边界，`--soft` 或 `--mixed` 更合适。若误移 branch 指针，可先查看 `git reflog` 找回旧提交，再用新 branch 保住它：

~~~bash
git reflog
git branch recovery/report-scope <commit-id>
git show --stat recovery/report-scope
~~~

reflog 是本地引用移动记录，会过期，不是远端备份。恢复到共享存储前先检查保住的快照。Git 对 reset、restore、revert 的职责有明确区分：reset 移动当前提交/重置 index，restore 改文件，revert 新增反向提交。

变更经 PR 和状态检查进入共享分支后，CI 才能用这个确切的提交构建镜像。容器摘要和晋级过程见[Docker 如何把该提交构建成固定镜像？](#33.%20Docker%20%E5%A6%82%E4%BD%95%E6%8A%8A%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E7%9A%84%E6%BA%90%E7%A0%81%E6%9E%84%E5%BB%BA%E6%88%90%E5%8F%AF%E8%BF%90%E8%A1%8C%E9%95%9C%E5%83%8F%EF%BC%9F)与[如何晋级已验证的报表服务产物？](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)。

> [!info]- 来源
> - Git 官方手册：[status](https://git-scm.com/docs/git-status)、[diff](https://git-scm.com/docs/git-diff)、[add](https://git-scm.com/docs/git-add)、[commit](https://git-scm.com/docs/git-commit)，checked 2026-11-06：工作区、index 和提交差异。
> - Git 官方手册：[fetch](https://git-scm.com/docs/git-fetch)、[pull](https://git-scm.com/docs/git-pull)、[merge](https://git-scm.com/docs/git-merge)、[rebase](https://git-scm.com/docs/git-rebase)，checked 2026-11-06：远端跟踪、整合和历史重放。
> - Git 官方手册：[reset](https://git-scm.com/docs/git-reset)、[restore](https://git-scm.com/docs/git-restore)、[revert](https://git-scm.com/docs/git-revert)、[reflog](https://git-scm.com/docs/git-reflog)、[stash](https://git-scm.com/docs/git-stash)、[cherry-pick](https://git-scm.com/docs/git-cherry-pick)，checked 2026-11-06：各命令的状态影响和恢复范围；本机 Git 2.56.0。
## 33. Docker 如何把报表服务的源码构建成可运行镜像？

报表平台工程师已修复 tenant-a 对 report 42 的读取条件，现在要确保测试过的提交确实构建成可复用镜像。container image（容器镜像）是只读文件系统和默认配置；container（容器）启动时增加可写层；volume（数据卷）把数据库数据放在容器外；network（网络）让 application programming interface（应用程序接口，API）、worker（工作进程）和数据库互通。发布时把 Git 提交固定为镜像摘要，并把数据库、密钥和运行配置放在镜像之外。下面用示意提交 c4f2a91 演示本地构建；本地验证不会自动发布或部署。

~~~mermaid
flowchart TD
    A[源码提交 c4f2a91 + 依赖锁文件] --> B[多阶段构建与依赖安装]
    B --> C[镜像 report-api，记录摘要]
    C --> D[API 容器与 worker 容器]
    D --> E[同一 Compose 网络中的 db:5432]
    E --> F[命名卷独立保存数据库文件]
    C --> G[构建流水线测试精确镜像，再发布相同摘要]
~~~

图里的 c4f2a91 和 report-api 都是示意值。image digest（镜像摘要）是内容身份；tag（可变标签）只是可变别名。同一提交可有不同构建结果，必须记录实际摘要才能确认 staging（预发布环境）与 production（生产环境）用的是相同镜像内容。

### 按运行所需文件分层构建

Python 报表 API 和 worker 可以来自同一个多阶段镜像：构建阶段下载由 dependency lock file（依赖锁定文件）固定的依赖，最终阶段只复制运行所需依赖和代码。下面基础镜像 tag 只用于说明结构；实际 CI 应记录所解析的基础镜像摘要，或直接固定摘要。

~~~dockerfile
FROM python:3.12-slim AS wheels
WORKDIR /build
COPY requirements.txt .
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
COPY --from=wheels /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels
COPY app ./app
USER 10001:10001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
~~~

为减少无关输入，先复制依赖清单再复制频繁改变的源码；这样源码改动不会使依赖安装层失效。`.dockerignore` 应排除 `.git/`、`.venv/`、`__pycache__/`、本机日志、真实 `.env` 和 secret（密钥）文件。Build context（构建上下文）是发送给 builder 的文件集合；若把密钥放进 context 再 COPY，镜像历史里就可能留下它。构建阶段需要私有包凭据时使用 BuildKit secret mount（构建时临时挂载密钥），而不是 Dockerfile `ARG` 或 `ENV`。运行期配置和密钥再由所选运行平台注入。

例如本地单平台构建并记录元数据的命令是：

~~~bash
docker buildx build --load --metadata-file /tmp/report-api-build.json -t report-api:c4f2a91 .
docker image inspect report-api:c4f2a91
docker image history report-api:c4f2a91
~~~

`--load` 将单平台镜像载入本地 Docker Engine；本地 `containerimage.digest` 只标识该 build 输出，不能当作 registry 已发布的摘要。示例 tag `report-api:c4f2a91` 只是本地引用：要将镜像归到该提交，CI 必须 checkout 确切的 `c4f2a91` 并从干净工作区构建，因为 tag 名不会约束 Build context。生产发布由 CI 从受控提交执行 `--push`，记录实际 push 的 `containerimage.digest` 并从 registry 核对目标 manifest；之后 staging 与 production 晋级同一不可变引用，不要分别重建。单平台摘要指向一个平台 manifest；多平台索引摘要指向多个平台 manifest，不同架构实际运行的内容可能不同。跨架构部署须记录并验收每个目标平台的 manifest digest，或明确预发布和生产使用同一平台。

Dockerfile 中的 `RUN` 在构建镜像时执行；`CMD` 提供容器启动时的默认命令或参数，`ENTRYPOINT` 指定主要可执行程序。Compose 的 `command` 覆盖镜像的默认 `CMD`，不会自动替换 `ENTRYPOINT`。因此 API 和 worker 可通过各自的 `command` 使用同一镜像启动不同进程。

### 容器、服务网络与数据存留是不同状态

下面的 Compose 片段复用上一条命令已载入的 `report-api:c4f2a91`，不再设置 `build:`，因此 API 与 worker 使用同一份本地镜像。若开发环境另用 `build: .` 和 `report-api:local`，那是从当前目录再构建的一份本地拓扑样例，不等于上面已验收提交的镜像。

API 与 worker 使用不同 command，但在 Compose 网络内访问数据库服务名 `db` 和容器端口 5432。容器间通信无需公开数据库端口。只将需要本机浏览器访问的 API 发布到宿主机回环地址：

~~~yaml
services:
  api:
    image: report-api:c4f2a91
    pull_policy: never
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      DATABASE_HOST: db
  worker:
    image: report-api:c4f2a91
    pull_policy: never
    command: ["python", "-m", "app.worker"]
    environment:
      DATABASE_HOST: db
  db:
    image: postgres:18
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - report-data:/var/lib/postgresql

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  report-data:
~~~

此片段只演示 API/worker 到 `db:5432` 的服务发现和网络可达，并未配置应用数据库凭据。`db_password` 当前只挂给 db，用于初始化 Postgres 默认管理员；官方镜像的 `POSTGRES_PASSWORD_FILE` 只在数据目录为空时用于初始化，后来修改 secret 文件不会轮换已有数据库中的密码。改密码须在数据库中执行凭据变更，并同步更新应用 secret。实际应用应另行创建最小权限账号，把用户名和独立密码注入 API/worker，并让代码从受控 secret 路径读取。不能从只有 `DATABASE_HOST` 推出应用已登录数据库。生产部署应让平台 secret store（密钥存储服务）管理凭据，不应把示意文件加入版本控制。受支持的 Docker Compose CLI v2 和 v5 都使用 `docker compose` 命令与 Compose Specification；Compose 文件顶层 `version` 字段已废弃，旧版独立 `docker-compose` 命令应迁移到该 CLI。服务加入项目网络后可通过服务名发现彼此；主机只在 API 的 127.0.0.1:8080 上可访问。网络成员关系限制可达路径，但不代替数据库身份、应用认证或租户授权。port mapping（端口映射）只转发连接，不证明进程健康。Docker Engine 28 及之后的默认 bridge/NAT 配置下，本机回环发布只在 Docker 主机可达；更早版本存在同一 Layer 2 网络主机可访问的例外。省略主机 IP 通常会绑定全部宿主接口，必须按 Engine 版本、network mode（网络模式）和路由判断暴露范围。

容器写层随容器删除而丢失；命名卷由 Docker 管理，在容器替换后仍可复用。匿名卷也可存活，但新容器通常不会自动重新挂上相同卷。bind mount 直接把宿主路径映射到容器，适合需要共同读写的开发文件。volume 不是备份；还需独立恢复演练。普通 `docker compose down` 保留声明的 named volumes，`docker compose down -v` 会删除项目卷和其中的数据。

本例使用官方 Postgres 18 镜像，把 volume 挂到 `/var/lib/postgresql`，由版本专属的数据目录组织数据库文件。旧版本镜像常见挂载点是 `/var/lib/postgresql/data`；现有旧卷不能只改 image tag 后直接按新目录启动，必须按官方镜像和 PostgreSQL 大版本迁移说明备份、转换或恢复。

### 从构建状态检查到运行状态观察

常见本地查看命令用于分开判断镜像、容器和服务：

| 命令 | 读取的状态 | 适合确认 |
|---|---|---|
| `docker image ls` | 本机镜像和 tag | 镜像是否已载入，不能证明运行中 |
| `docker ps -a` | 创建过的容器 | 容器是否运行或退出 |
| `docker compose logs api worker` | Compose 服务日志 | 启动错误或应用输出 |
| `docker compose exec api /bin/sh` | api 服务容器内进程环境 | 仅当镜像里确实有 shell；精简镜像可能没有 |
| `docker compose ps` | Compose 服务 | 容器状态；实际容器名由项目名和服务名生成 |
| `docker image history report-api:c4f2a91` | 镜像层历史 | COPY/RUN 的构建结果，不是镜像里的完整文件审计 |

detached mode（后台运行模式）返回 shell 不表示程序有监督，也不证明容器健康。启动探针、就绪探针和应用 SLI 属于运行平台与服务观测，不由镜像构建证明；参见[容器运行时如何承接 API 和 worker？](#34.%20%E6%8A%A5%E8%A1%A8%20API%20%E4%B8%8E%E5%BC%82%E6%AD%A5%20worker%20%E5%BA%94%E7%94%B1%E4%BB%80%E4%B9%88%E8%BF%90%E8%A1%8C%E6%97%B6%E6%89%BF%E6%8E%A5%EF%BC%9F)。ACK、队列延迟与业务完成由[消息交付如何确认](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)说明。

基本操作可按 image/container 两种对象查看：`docker pull redis:7` 拉取镜像，`docker run --name cache -d redis:7` 创建并启动容器，`docker ps -a` 查看含已停止的容器，`docker stop cache` 与 `docker start cache` 停止或重新启动已有容器，`docker rm cache` 移除已停止容器，`docker image rm redis:7` 移除镜像标签。对正在运行的容器使用 `docker rm -f` 会同时停止并删除它，先确认容器写层中没有要保留的数据。

手动推送镜像时先用 `docker login registry.example.com` 验证 registry 身份，再 `docker tag` 赋上 registry 地址并 `docker push`。这会发布镜像，不能用可变 tag 代替部署时的 digest；生产中由受控 CI 身份执行该步骤，本文不运行登录或推送。

> [!info]- 来源
> - Image、Dockerfile 指令与多阶段构建：[Docker image concepts](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/)、[Dockerfile reference](https://docs.docker.com/reference/dockerfile/) 与[多阶段构建](https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/)，checked 2026-11-06；Compose 服务的 [`command`](https://docs.docker.com/reference/compose-file/services/#command) 覆盖默认 `CMD`。
> - Layer cache、context 和 secret：[Build cache](https://docs.docker.com/build/cache/)、[Build secrets](https://docs.docker.com/build/building/secrets/)、[buildx build --metadata-file](https://docs.docker.com/reference/cli/docker/buildx/build/)，checked 2026-11-06。
> - Network、port publish 和 volume：[Docker networking](https://docs.docker.com/engine/network/)、[port publishing](https://docs.docker.com/engine/network/port-publishing/)、[volumes](https://docs.docker.com/engine/storage/volumes/)，checked 2026-11-06；Docker Engine localhost publishing 语义须按 Engine 版本、network mode 和路由核对。
> - Compose 默认网络、volume、secret 与 CLI 版本：[Compose file reference](https://docs.docker.com/compose/compose-file/)、[Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/) 和[Compose history](https://docs.docker.com/compose/intro/history/)，checked 2026-11-06；当前 v2/v5 使用 `docker compose` 与 Compose Specification。
> - Postgres image 的初始化变量和数据路径：[官方 image 环境变量](https://hub.docker.com/_/postgres#environment-variables)与[PGDATA 说明](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)，checked 2026-11-06。`POSTGRES_PASSWORD_FILE` 不会更新既有数据目录中的账号密码；PostgreSQL 18 路径与旧镜像迁移边界适用于相应官方 image，换版不迁移数据。
> - 固定发布标识：[Docker image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/)，checked 2026-11-06；具体多平台 manifest 应读 builder 和 registry 的实际 metadata。
> - 基本操作：[docker run](https://docs.docker.com/reference/cli/docker/container/run/)、[docker stop](https://docs.docker.com/reference/cli/docker/container/stop/)、[docker rm](https://docs.docker.com/reference/cli/docker/container/rm/)、[docker login](https://docs.docker.com/reference/cli/docker/login/)、[docker tag](https://docs.docker.com/reference/cli/docker/image/tag/) 和[docker push](https://docs.docker.com/reference/cli/docker/image/push/)，checked 2026-11-06。
## 34. 报表 API 与异步 worker 应由什么运行时承接？

在这次租户授权修复中，tenant-a 读取 report 42 应得到 200，tenant-b 猜中同一 ID 应得到 404。用户通过浏览器访问 application programming interface（应用程序接口，API）；当账户 acct-17 为 report 42 发起异步导出时，请求幂等键为 report-demo-208，API 在同一数据库事务写入 job（任务）job-demo-731、outbox（事务发件箱）意图并预留一个等待槽。等待槽是数据库维护的排队准入额度：每个未被领取的排队轮次占一个，接管重排时重新预留，领取时释放，不是 broker 的 prefetch 或锁。relay（转发进程）发布到 queue（队列），worker（工作进程）计算结果、写入私有对象并提交状态。只读请求和导出任务虽指向同一报表，但授权响应与 job 成功/失败是不同用户结果；每层的网络可达、身份权限、业务规则和恢复责任都不同。

~~~mermaid
flowchart TD
    B[浏览器] -->|HTTPS| C[可选 CDN]
    C --> L[负载均衡器：本图的入口]
    L --> A[私有 API 运行时]
    A -->|按当前主体查 tenant（租户）+ report| D[(数据库)]
    A -->|job + pending outbox + 预留数据库排队额度，同一事务| D
    D --> R[Outbox relay]
    R -->|发布并等待 broker（消息代理）确认| Q[队列]
    Q -->|delivery（消息投递）| W[私有 worker]
    W --> D
    W --> O[私有对象存储]
    W -->|耐久结果状态后 ACK| Q
~~~

只读请求和异步导出均以 report 42 为报表资源；导出由账户 acct-17 发起，report-demo-208 是幂等键，job-demo-731 是持久任务 ID。worker 用 task role（任务角色）把结果写入私有对象；只有数据库记录已提交对象引用后，拥有读取权限的下载 API 才能签发短期 signed URL（签名网址）。浏览器不持有 worker 的 task role；S3 预签名 URL 把签发身份在有效期内可重复使用的受限读取能力交给持有 URL 的浏览器。应用后来撤销用户业务权限，不会自动撤销已发出的 URL；新发 URL 应设较短有效期，撤销底层签名凭据或改变资源策略也会影响既有 URL。CDN 可选地位于本图负载均衡器之前，含租户私有结果的响应不能按公共 URL 无条件共享缓存。通常 DNS 先把公共服务名解析为入口地址，再建立 HTTPS 连接；更完整的协议过程见[HTTP 与网络请求如何建立？](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F)。路由、outbox 与 attempt（尝试号）状态细节见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 网络路径和身份策略分开

负载均衡器接收 HTTPS（安全超文本传输协议）并把请求送到配置的健康目标；计算服务运行 API 和 worker；数据库保存结构化状态；对象存储保存大文件；队列把可异步完成的工作和用户请求分离。浏览器可以通过范围受限、短期有效的签名网址直传或下载对象，不需要把 bucket（对象存储桶）设成公开。

网络路由、防火墙或安全组决定“谁能连到哪个地址”；工作负载身份和资源策略决定“该主体能对哪个资源做什么”；应用的授权规则再决定当前业务用户能否读取 tenant-a 的 report 42。这三个层次不能互相替代。常见拓扑只开放负载均衡器，API 仅允许来自负载均衡器，数据库只允许来自 API/worker。worker 的 task role 只需要写入报表前缀；签发下载 URL 的 API 还需要相应读取权限，S3 按签发凭据授权预签名请求，浏览器只持有短期 bearer URL，不需加入服务角色。队列只接受被授予权限的服务身份。本地 Compose 只能验证服务发现和网络连通；同一个镜像摘要进入 staging 后，还要经已装配的真实入口和测试身份复放 A→200、B→404，不能把镜像相同当成认证、配置或租户授权已验证。见[晋级验收](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)。

### 托管平台管理什么，应用仍拥有哪部分

| 层 | 平台通常负责 | 应用团队仍负责 |
|---|---|---|
| 计算 | 按服务方案提供主机维护、调度和运行环境 | 镜像/包、启动退出、资源上限、扩缩容策略、健康规则 |
| 数据库 | 所选配置包含的基础设施、补丁、备份或故障切换 | schema 和迁移、查询/连接行为、权限授予、保留期、恢复演练 |
| 对象存储 | 服务可用性及文档承诺的持久性机制 | 私有命名、保留/生命周期、上传上限、谁能拿 signed URL 及其过期/撤权策略 |
| 队列 | 在服务合同和配置限制内存储和投递消息 | 幂等处理、重试退避、毒消息处理、队列年龄和死信队列（DLQ）恢复 |

“托管”减少平台运维，但不会替工作负载选择安全配置。托管数据库不会修复缺索引查询或连接风暴；托管队列也不会使非幂等 worker 在重试时安全。

### 按任务时长、并发和停止行为选择运行时

一次有界、可重试的短报告任务可以由 function service（函数托管服务）执行，前提是最大执行时长、cold start（冷启动）、并发和触发器语义符合任务；长时间 API 与 queue worker 需要明确进程生命周期、并发界限和停止流程时，managed container service（托管容器服务）往往更适合；需要主机级控制或兼容遗留环境时，virtual machine（虚拟机，VM）提供控制权，但团队要承担系统补丁和容量管理。按峰值/稳态负载、最低常驻容量、启动延迟容忍度、长连接、执行上限和团队运维能力比较。serverless（无服务器计算）仍有状态、网络、配额和费用边界。

在这个报表例子里，HTTP API 要持续接收读请求，worker 要等队列、处理 database（数据库）和对象存储，并在部署停止时完成或释放当前 delivery（消息投递）。因此可把 API 与 worker 作为分开的可扩缩容服务，同一镜像运行不同命令。只有导出任务明确有界且平台事件处理语义合适时，才把它拆为函数。Cloud Run functions 的代际、并发和时长限制见[托管函数何时适合报表任务？](../../archive/front-end/Deprecated_Interview_Notes/hosted-functions-tradeoffs.md)。

进程收到停止信号时，API 服务先把 readiness probe（就绪探针）标为未就绪，让负载均衡器停止送入新的 HTTP 请求；这不会自动停止独立 worker 消费队列。worker 要主动暂停 broker consumer 或停止取新 delivery，再在宽限期内完成当前任务或中止并释放未确认 delivery。只在结果或终态已持久提交后 ACK；未提交的 delivery 让 broker 按其恢复契约重投，数据库租约恢复器另负责接管仍记录为 running 的 job。API 的 readiness 控制入口流量，worker 的 pause/cancel 控制消息领取，二者不能互相替代。数据库连接池、线程、临时文件和 telemetry exporter（遥测导出器）都要有明确清理。具体 stop signal、async cancellation（异步取消）与资源释放依运行时和平台实现；容器 health probe（健康探针）的职责由[容器发布检查](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)说明，消息交接则由[发布确认与消费者 ACK](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)说明。

### worker 凭据怎样注入、轮换并撤销？

报表系统有两个独立进程：发送 worker 用 HMAC（基于哈希的消息认证码）密钥为 Webhook（回调通知）签名；接收服务用允许的 keyId→密钥映射验签。合成协议要求同一 endpoint/source 的发送端与接收端持有对应相同密钥，但每个服务只取得自己需要的密钥值和授权范围，使用独立的 ECS execution role（执行角色）注入各自 Secret ARN。短期工作负载身份、共享消息密钥和某个用户授予第三方的 OAuth grant（OAuth 授权）生命周期不同，不能混成一个环境变量或角色。

以 Amazon ECS 为一个具体部署例子，容器镜像只包含代码，task definition（任务定义）引用 Secrets Manager 中的密钥，不放密钥值。ECS 的 task execution role（任务执行角色）给 ECS agent 启动任务时读取所需 Secret ARN 的权限；该角色的权限不直接交给容器内代码。应用调用 AWS 服务时使用另一个 task role（任务角色），例如只允许向指定报表前缀写对象。角色分开并按服务授予最小动作与资源范围，避免 worker 因共享角色取得无关 API 或 Secret 权限。ECS 任务角色提供短期工作负载凭据，AWS SDK 通过容器凭据接口取得并刷新它们；应用不应把这组 AWS 凭据再复制成长期静态键。

接收 ECS service 在启动时把验证器允许的 keyId→密钥映射注入 `WEBHOOK_VERIFY_KEYS_JSON`；签发 ECS worker 只注入当前 keyId 对应的 `WEBHOOK_SIGNING_KEY` 与 keyId。两服务用不同的 task definition 和 execution role，只能读取各自命名的 Secret ARN；task role 不承担读取 Secret 的职责。ECS 的 `valueFrom` 可以指向完整 secret、JSON key、version-stage 或 VersionId；本例不固定 VersionId，让它跟随 `AWSCURRENT`。移动该 staging label 后，正在运行任务的环境不会自动更新；要启动新 task 或强制 service 滚动部署，进程才会读到新值。若 task definition 固定了 VersionId，则必须先更新 task definition revision 指向新版本，再替换任务。ECS 官方还指出容器内的应用、日志和调试工具都可能访问这些环境变量，所以不能 dump 全部环境、在异常信息中回显配置，也不应把密钥加入镜像层、版本库、任务参数明文、前端 bundle、请求日志或模型 prompt/checkpoint。相同签名、重试和接收路径见[Webhook 接收方怎样验证并可靠受理？](#17.%20Webhook%EF%BC%88%E5%9B%9E%E8%B0%83%E9%80%9A%E7%9F%A5%EF%BC%89%E6%8E%A5%E6%94%B6%E6%96%B9%E5%A6%82%E4%BD%95%E9%AA%8C%E8%AF%81%E5%B9%B6%E5%8F%AF%E9%9D%A0%E5%8F%97%E7%90%86%EF%BC%9F)。

正常轮换按“接收端先兼容、发送端再切换、接收端最后移除旧键”进行。本合成 Webhook outbox 保存未签名原文，发送 worker 每次新尝试才签名：

1. 为该 endpoint/source 生成新 keyId 和新密钥；把接收端的 `WEBHOOK_VERIFY_KEYS_JSON` 更新为旧、新双键映射，移到新 `AWSCURRENT` 并强制部署 receiver task。若 task definition 固定 VersionId，则发布引用新版本的 revision；确认旧 receiver task 已退出。
2. 更新发送端 `WEBHOOK_SIGNING_KEY` 和当前 keyId，替换 sender task。Sender 每次尝试都用新 key 重签相同 eventId 和正文；等旧 sender task 全部退出并记录所有旧 sender 实例签名时间戳的最大值；只有当每个仍可能接收旧请求的 receiver 时钟都已晚于该最大时间戳加 300 秒，且最大在途请求处理时限也已过，才可移除旧键。不能只从最后一次发送起等待 300 秒；实际轮换还要覆盖已知时钟偏差。
3. 将接收端验证映射更新为仅新键，并强制替换 receiver task；若固定 VersionId，更新 task definition revision。确认旧 receiver task 退出后，旧密钥才不再驻留于任一运行进程。过期 Secrets Manager 版本按保留策略移除。
4. 如果实现预先排队已签名请求而非未签名正文，就要在旧签名失效前重新签名这些请求，或等其失效后再移除旧键。

移动 `AWSCURRENT` 不会改变正在运行的环境变量；每个使用该 Secret 的 sender/receiver service 都要部署新 task。若双方引用 VersionId，则各自 task definition 都要发布指向该版本的新 revision。

若 key 已泄漏，紧急路径不保留新旧双接受窗口。新 key 应预先生成；先暂停端点交付并阻断入口或停止旧 receiver task，再部署只含新 key 的 receiver task；随后把 sender 切到新 key 并替换旧 sender task，确认旧进程均退出后恢复交付。若 task definition 固定 VersionId，两端都要更新 task definition revision。没有可用新 key 时立即撤销旧 key 并维持暂停，不为可用性继续接受泄漏密钥。发送端按撤销 keyId 找出未确认事件，只能在原 `createdAt + 30 天` 截止前，用原 eventId、原正文和新 attemptId 重签；换键不会重置期限。旧请求若已受理但响应丢失，持久 inbox 会识别重复；已确认 2xx 的事件不重放。删除 Secrets Manager 的值本身不能清除已注入进程中的副本，必须替换对应 receiver/sender task。对于能直接访问资源的其他凭据，还要在签发方或目标资源撤销授权；用户 OAuth access token 的撤销时机依 provider 契约处理。

用户 OAuth grant 属于另一个授权主体：它代表某个用户允许 Agent 或应用访问特定下游资源，必须按用户、租户、目标 audience（令牌受众）、scope（权限范围）与过期状态隔离，并在用户撤权后阻止新调用。它不是 ECS task role，也不是服务级 Webhook HMAC 密钥。OAuth 刷新 token 不进入统一 worker 环境、日志、模型上下文或恢复快照；运行时只按已绑定 grant 取用，撤权后依第三方 provider 契约停止或重新授权。短期工作负载身份不替代该用户 grant，也不能扩大用户授权范围。

分开审计 secret 注入与业务 API 调用。CloudTrail 的 Secrets Manager `GetSecretValue` 事件可用于查看 execution role 对 Secret ARN 的访问；再关联 task definition revision、task 启动和部署控制面记录。若 task definition 固定 VersionId，revision 能标出期望版本；若跟随 `AWSCURRENT`，需保存 staging label 变更和滚动部署时间线。不能假定 GetSecretValue 的 CloudTrail 记录含 taskArn 或响应返回的 VersionId。业务 SDK 以 task role 调 AWS API，其 CloudTrail session 可带 taskArn；这类业务调用审计不能替代 secret 注入审计。两条记录都不含密钥值，日志中也不得记签名原文。审计轨迹能定位谁在何时读取或启用了凭据，但不会自动证明权限最小；还要检查实际 IAM policy 与目标资源范围。

### 用失败信号和成本边界检查组件

| 边界 | 计划中的失败 | 观察信号 | 成本/限制 |
|---|---|---|---|
| 负载均衡 / 网络 | 错路由、无健康目标、出站流量受阻、证书过期 | 请求错误、连接失败、目标健康数 | 请求与字节、网络地址转换、数据传输 |
| 计算服务 | 启动失败、崩溃循环、CPU/内存饱和、扩容慢 | 就绪实例、CPU/内存、重启与请求排队 | 最低副本和运行时间；扩容不是瞬时容量 |
| 数据库 | 连接耗尽、锁等待、I/O/存储或故障切换 | 连接池等待、连接数、查询时延、锁 | 计算、存储、I/O、备份保留 |
| 对象存储 | 权限错误、路由故障、对象意外公开、无限保留 | API 错误、对象增长、下载量 | 存储、请求、生命周期、复制、出站流量 |
| 队列 / worker | 重复/延迟投递、毒消息、积压上升 | 最老消息年龄、队列深度、未确认数、死信队列 | 保留消息、worker 计算、积压排空时间 |

平台容量与业务结果要分开观察。CPU 不高并不能证明 report 42 可正确读取；queue 有消费者也不代表报表已经成功。可观测性章会把这些组件信号与用户的 request/job 结果连接起来。

> [!info]- 来源
> - 网络与身份责任：AWS Well-Architected [Security pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html) 和 [ECS task IAM roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)，checked 2026-11-06；这是 AWS 实例，其他平台的身份模型不同。
> - 托管函数的 warm runtime、实例复用与重试：AWS Lambda [Execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) 与 [application design](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html)，checked 2026-11-06；内存缓存可复用但不能作为跨执行持久状态的事实限于 Lambda 运行时。
> - 对象授权路径：Amazon S3 [access management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-management.html) 和[presigned URL](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)，checked 2026-11-06；签名 URL 可给短期访问，不代表 bucket 公开。
> - 运行探针：Kubernetes 官方 [Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)，checked 2026-11-06；probe 作用依平台，readiness 影响流量，liveness 可触发重启。
> - 证据和术语按具体平台合同适用；本文图是通用架构示意，不代表任何已部署系统。
> - 一个具体注入/身份例子：AWS ECS [task role 最小权限与隔离说明](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html)、[Task IAM role 的临时凭据交付与 taskArn 审计上下文](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)、[task execution role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)，以及 AWS SDK [container credential provider](https://docs.aws.amazon.com/sdkref/latest/guide/feature-container-credentials.html) 和[标准 credential provider 自动续期](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html)，checked 2026-11-09。task role 供应用 SDK 调用云服务并取得/续期临时凭据，execution role 给 ECS agent 启动所需权限。
> - [ECS 注入 Secrets Manager 环境变量](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html)，checked 2026-11-09：引用可指定 JSON key、version-stage 或 VersionId；stage 与 VersionId 不能同时指定。未固定 VersionId 且未指定 version-stage 时默认读取 `AWSCURRENT`。Secret 在 task 启动时注入，更新后须启动新 task 或强制服务部署，容器内应用、日志和调试工具可访问这些变量。其他云平台的读取、刷新和撤销语义不同。 [Secrets Manager GetSecretValue API](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html) 与 [Secrets Manager CloudTrail entries](https://docs.aws.amazon.com/secretsmanager/latest/userguide/cloudtrail_log_entries.html)，checked 2026-11-09：API response 含 VersionId，但 SecretString/SecretBinary 不进入 CloudTrail；审计不能把 API response 内容说成 CloudTrail 返回字段。
## 35. 如何晋级并回滚已验证的报表服务产物？

对 report 42 的租户范围修复，测试结果应绑定到固定的源码提交。continuous integration（持续集成，CI）在该提交上运行静态检查、单元测试、数据库测试和所需的消息代理检查；构建一次 container image（容器镜像），测试这份确切镜像，再把相同 digest（摘要）从 staging（预发布环境）晋级到 production（生产环境）。continuous delivery（持续交付）让通过门禁的产物随时可发布；continuous deployment（持续部署）则在规则满足后自动发布。部署回滚不能自动撤销数据库写入或远程副作用。

~~~mermaid
flowchart TD
    A[提交 c4f2a91] --> B[静态 + 单元 + 集成 + 契约测试]
    B --> C[构建一次并发布镜像]
    C --> D[保存 commit 与 image digest]
    D --> E[在 staging 部署相同 digest]
    E --> F[smoke / 数据库 / worker 检查]
    F --> G{生产环境门禁}
    G -->|通过| H[小流量 canary]
    H --> I{用户 SLI 和依赖信号在范围内？}
    I -->|是| J[逐步放到全部流量]
    I -->|否| K[停止放量并判断安全回退目标]
    G -->|未通过| L[不接触生产流量]
~~~

图里的 c4f2a91 是示意 commit。单平台镜像的 digest 标识该平台 manifest；多平台镜像索引 digest 标识一组平台 manifest，同一个索引摘要可能让 amd64 与 arm64 节点拉取不同平台的镜像内容。因此本例若说 staging/prod 运行相同镜像内容，前提是部署目标平台相同；跨架构发布须记录并核验每个目标平台解析到的 manifest digest。构建时间戳 tag、latest 或 staging/prod 两次独立 build 都不能替代摘要；需要审计的是目标平台实际运行的产物。

### 一次构建，逐级测试并记录产物身份

先在 pull request（合并请求，PR）上运行与变更风险匹配的检查：修复授权范围要有所有者/非所有者测试；数据库 schema（结构定义）变更要兼容旧数据与旧代码；worker 改动触及 acknowledgement（确认，ACK）时需要所选消息代理的集成测试。合并可能产生新的 merge commit，因此构建前要在最终合并提交上重跑必需检查，或确认 PR 检查验证的源码树与最终构建输入完全相同。随后 CI 从这个已验收的 commit（提交）构建一次镜像，并记录提交、依赖锁文件、构建器、基础镜像与镜像摘要。

例如 Buildx 可在构建并推送镜像时把构建 metadata 写到文件：

~~~bash
docker buildx build \
  --push \
  --metadata-file report-build.json \
  --tag registry.example.com/team/report-api:c4f2a91 \
  .
jq -r '."containerimage.digest"' report-build.json
~~~

该命令会构建并推送镜像；得到摘要后，把预发布和生产环境的目标都写成同一个不可变引用，如 `registry.example.com/team/report-api@sha256:...`。生产变更记录至少能回答：哪个提交生成了这个摘要、哪组检查针对它通过、当前哪个环境运行它。

在 staging（预发布环境）验证同一摘要时，用经真实入口和测试身份提供方装配的请求复放授权回归：tenant-a 读取 report 42 应返回 200 和预期报表；tenant-b 用自己的合法身份请求同一路径应返回 404。这里不能用客户端自填的租户头代替身份。tenant-a 得到 404 也是本次验收失败，不能因为 tenant-b 的合法拒绝状态也是 404 就把状态码集合当作成功判断。worker 的提交/ACK 检查覆盖另一条异步路径，不能代替这项用户读请求验收。

如果每个环境分别重建，即使源码提交相同，也可能遇到基础镜像、依赖、构建时间输入或构建器变化。一个具体镜像通过预发布环境后，应晋级它本身；运行时数据库地址、feature flag（功能开关）和 secret（密钥）通过受控配置注入，不把密钥烘进镜像。若有前端 bundle（前端打包文件），编译期环境配置不同会生成不同产物；若要逐环境晋级同一静态站点 bundle，应把非秘密配置作为运行时公开配置读取。无论何种方式，编译进 bundle 的值都对浏览器用户可见，不能作为密钥。静态站点没有容器镜像时，也可记录每次发布的 artifact ID（产物标识）或校验和，并在 staging 与 production 验证同一组文件。

### 将环境门禁、启动检查和渐进放量接起来

GitHub Actions environment（工作流环境）可以为 production 配置部署保护规则，例如要求审查者批准、限制可部署分支或控制环境密钥的访问。workflow（工作流）引用该环境的 job（任务）通过相应规则后才运行；这控制的是凭据和部署授权，不替代应用自己的流量安全判定。选用第三方 action（自动化步骤）时，固定已审核的完整 commit SHA（提交哈希）；tag 可移动。

发布前核对部署配置的 identity and access management（身份与访问管理，IAM）权限、网络路由、密钥来源、数据库迁移和目标镜像摘要。镜像本身不应包含数据库密码。一次数据库 migration（结构迁移）由独立、可观察的步骤执行，而不是每个 API replica（副本）启动时都执行。

readiness probe（就绪探针）判断实例是否可以接收流量；liveness probe（存活探针）判断进程是否卡在无法自愈的状态并可触发重启；startup probe（启动探针）给慢启动应用完成初始化的时间，成功前先不执行存活/就绪探针。不要让存活探针依赖每个暂时性的下游服务，否则数据库短暂故障可能让实例同时重启。绿色探针只能说明探针路径正常，还不能证明 report 42 的授权、结果对象或队列处理正确。

支持渐进发布的平台可以从一小部分真实流量开始，按用户 SLI（服务等级指标）、错误类别、延迟、容量与 queue age（队列消息年龄）比较新旧 revision（版本实例）。只在样本量、时间窗口和代表性任务足够时继续放量；新版本启动成功不等于用户旅程健康。具体平台可能采用滚动更新、blue-green（蓝绿发布）或 canary（金丝雀发布），其流量切换和自动判断机制并不相同。

### 回退代码时不要假设数据也回去了

如果新镜像导致 5xx、超时或 queue worker 持续失败，可以停止放量并回退到最近一个已完成且安全的应用版本。report 42 的租户隔离修复有安全意义：若旧版存在已知跨租户漏洞，回到旧 image 会重新开放数据风险。此时应先隔离受影响入口、禁用危险路径或前向修复，不能机械恢复成旧 digest。缓解选择需要 production trace、部署时间和权限测试共同支持，见[从报表服务信号定位发布故障](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)。

代码回退不等于数据库回滚。常用 expand-and-contract（扩展-收缩迁移）次序是：先加向后兼容的列、索引或表形态；部署同时接受新旧形态的代码；在可控事务或批次中回填并核对；切换读写；等旧 API 实例和旧 worker 全部退出、旧代码不再是回滚目标后，才删除旧形态。进入删除旧结构的收缩阶段前，要确认线上没有实例或 worker 再读写它，而且发布策略已不再考虑回滚到仍依赖该结构的旧版本。

镜像 rollback 不会撤销已经提交的 job、已上传且已引用的报告对象、已发送邮件或支付。若外部动作需要补偿，应使用有幂等键的明确补偿流程；恢复备份也可能丢失备份之后的新写入，是恢复决策，不是普通应用回滚。数据库与对象状态由各自备份、保留与审计边界负责。

> [!info]- 来源
> - GitHub Actions [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments) 与[部署环境概念](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)，checked 2026-11-06：保护规则、required reviewers、branch 限制和环境 secrets 的授予时间；部署行为仍由具体 workflow/provider 决定。
> - GitHub Actions [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)，checked 2026-11-06：third-party Action 使用完整 commit SHA 的不可变发布方式与审查理由。
> - Docker Buildx [build --metadata-file](https://docs.docker.com/reference/cli/docker/buildx/build/)、[image digest](https://docs.docker.com/dhi/explore/security-concepts/digests/) 与[multi-platform images](https://docs.docker.com/build/building/multi-platform/)，checked 2026-11-06：push 返回的 registry digest、可移动 tag、索引摘要和各平台 manifest digest 的边界。
> - 探针：Kubernetes [Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)，checked 2026-11-06：三种探针的不同动作；不同平台的配置语义须看其官方文档。
> - 自动回退实例：Amazon ECS [Deployment failure detection](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-failure-detection.html) 与[deployment circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html)，checked 2026-11-06：ECS circuit breaker 根据任务运行与已配置健康检查判断 steady state，CloudWatch alarm 可作另一类 failure detector；自动 rollback 需要配置，且回到上次 COMPLETED deployment。不是所有发布平台都采用相同条件。
> - 数据库兼容性：AWS blue/green 官方白皮书 [Decoupling schema changes from code changes](https://docs.aws.amazon.com/pdfs/whitepapers/latest/blue-green-deployments/blue-green-deployments.pdf)，checked 2026-11-06：新旧环境共用数据时要保持 schema 兼容；本文的 expand-and-contract 是通用工程安排，不是平台自动回滚数据库的承诺。
## 36. 怎样从报表服务信号定位发布后的故障？

report-api 的新镜像已经通过测试并开始逐步接收真实流量。若用户看到 5xx、report 42 变慢或导出任务迟迟未完成，先用聚合指标确定影响范围，再沿一个 request/job trace（请求或任务的分布式追踪）找出耗时或失败阶段，最后用关联日志核实该阶段做了什么。指标、追踪和日志各自回答不同问题；一个健康进程或没有告警都不能单独证明用户结果正确。

~~~mermaid
flowchart TD
    D[发布新的镜像 digest] --> M[指标显示错误/延迟窗口与范围]
    M --> T[代表性 trace 找到慢或失败阶段]
    T --> L[关联日志解释该事件]
    L --> A[选有证据的最小缓解]
    A --> V[核对用户 SLI 与依赖恢复]
    V --> P[记录原因、修复与检测缺口]
~~~

图把已发布构建连接到事故诊断：观测要能够区分“新镜像引入变化”与数据库、队列、对象存储等依赖故障。trace context（追踪上下文）与跨异步边界传播方式由 OpenTelemetry 的上下文传播机制说明；用户 SLO（服务等级目标）的目标和预算由[测试验收与发布流程](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)使用。

### 从一个用户请求关联三种信号

对 GET /api/reports/42 记录稳定的路由模板、响应类别、区域和依赖名称。传递追踪上下文后，可以把入口、API、数据库访问与对象存储调用组合成一个 trace（分布式追踪）。一个 span（操作区间）有开始时间、结束时间和状态；日志关联时同时记录 trace ID 与 span ID，便于回到具体请求和子操作。父子关系显示某个步骤消耗了多少时间，但并行或嵌套 span 的持续时长可能重叠，不能简单相加为总耗时。对异步导出，可在消息属性中传播可用的追踪上下文，同时保留 job ID 作为业务关联键。trace ID/job ID 是单次操作信息，不要将它们作为每条 metric（指标）的维度。

| 信号 | 它回答的问题 | 报表服务示例 |
|---|---|---|
| Metrics（指标） | 整体是否变差，何时、哪类请求受影响？ | report 路由的有效请求数、坏事件率、延迟分位数、数据库连接等待、任务最老年龄 |
| Traces（追踪） | 这个请求/任务在哪个阶段变慢或失败？ | API 请求的操作区间包含授权查询和报表读取；异步任务的追踪延伸到队列、worker、数据库和对象上传 |
| Logs（日志） | 该阶段具体记录了哪个结果或错误？ | 同一追踪 ID 的结构化事件记录查询超时、状态转换失败或对象写入错误 |

调查正在放量的新镜像时，先从该 canary（小流量版本）的指标窗口筛选受影响路由和结果，再找代表性慢请求。例：一次读取耗时 900 ms，其中授权/报表查询 span 占 720 ms，关联日志显示查询前先等连接池 600 ms。指标把影响连到当前摘要和时间窗；trace 说明慢在查询阶段；日志显示主要等待来自连接池。若该摘要对应的指标窗口达到停止放量门槛，就暂停增加流量并核对连接池与下游数据库信号；这条 trace 用于定位慢在哪一阶段，尚不足以单独触发停发或归因给查询计划。若 trace 被采样，缺少样本不证明没有请求或故障；检查采样率、遥测新鲜度和覆盖后再判断。

> [!example] 用 report 42 的 SLI 核对用户影响
> 设定 30 天的 service level indicator（服务等级指标，SLI）：在可信身份边界已确认主体、且 report ID 格式有效后进入 API 的 report read 请求为分母；之后超时、5xx 或没有响应仍留在分母。身份提供方在主体确认前发生的失败另用入口认证指标衡量，不能因为 API 内部授权组件返回成功才决定是否计入。好事件是服务在 400 ms 内按业务契约给出预期结果：tenant-a 有权读取 report 42，必须返回 200 和预期报表；tenant-b 无权读同一资源，按本例契约返回 404。tenant-a 得到 404 即使状态码“看起来可接受”也算坏事件。这个 SLI 衡量 API 边界的可用性和时延，不包含用户设备或服务回复后的网络，也不单独证明返回数据的租户归属正确；后者仍需授权回归测试和独立审计。
>
> 若 10,000 次符合条件的请求中 9,940 次为好事件，则 SLI 是 9,940 ÷ 10,000 = 99.4%。若 service level objective（服务等级目标，SLO）为 99.5%，坏事件预算为 (1 − 0.995) × 10,000 = 50 次；实有 60 次坏事件，超预算 10 次。单位是此 30 天窗口中的请求数，不是百分比或毫秒。SLI 是测量结果，SLO 是内部目标；service level agreement（服务等级协议，SLA）则是对外承诺，可能规定服务额度或违约后果，不能只把内部阈值改名为 SLA。这项 30 天 SLO 用于看长期错误预算；放量决策另看接下来数分钟的 canary 结果，不必等待 30 天预算恢复。该请求加权平均也不能证明每个 region（区域）或用户群体体验相同。
>
> 分母必须保持稳定，不能因为没有返回、超时或慢响应而把请求剔除。这个简单事件比率只适用于该定义和 30 天窗口。另设 job 完成时间 SLI 时，要定义接受后多久必须完成，并按统计窗口截止时的状态计算。例如约定 2 分钟 deadline，则只将本窗口中已接受至少 2 分钟的成熟任务纳入分母；成熟任务只有在自己的 deadline 前已持久化为 `succeeded` 才算好事件，否则算坏事件，包括截止时仍为 `queued`、`running` 或 `cancelled`，以及迟到才成功的任务。新近接受、尚未到期的任务暂不计入，也要单列 oldest pending age。统计应冻结窗口截止状态，不能用事后现在已完成的状态改写当时是否逾期。以 12:00 结束的窗口为例，11:57:00 接受的任务若到 11:59:01 才完成，已超 2 分钟 deadline，应计坏事件；11:59:30 才接受的任务在 12:00 仍未到期，不进分母。这样不能只对已完成样本计算，也不会把尚有时间完成的任务提前算失败。

SLO 告警可以要求至少 100 个符合条件的请求的滚动 10 分钟窗口中好事件比例低于 99%，且持续 5 分钟才触发。该数字只是说明一次告警条件的组成；实际阈值要按服务流量、目标与噪声调校。告警信息带上分子、分母、窗口、路由/区域和指标/追踪查询链接。HTTP 成功与时延度量交付；若报表含模型生成内容，任务质量需另用独立评估，用户反馈样本可能偏向主动评分者。见[LLM 任务评估方法](../../ai-engineering/evaluation/llm-evaluation-methods.md)和[生产反馈信号](../../ai-engineering/systems/ai-production-observability-and-feedback.md)。

### 让遥测可诊断，但不泄露报表内容

指标使用低 cardinality（基数）的维度，如 route template（路由模板）、响应类别、区域和依赖名；不要把 request ID、trace ID、用户/tenant ID、原始 URL、报表标题、提示词或返回内容放进每条指标。每种维度组合可能新增一条 time series（时间序列），任意 ID 会使序列数快速增长并增加聚合成本。

请求 ID 与追踪 ID 可放在各自日志/追踪记录中用于关联，但仍是敏感链接数据：限制访问和保留期；不记录 access token（访问令牌）、cookie、授权 header（请求头）或原始用户内容。优先记录有界分类，如授权结果=allow/deny、数据库错误=timeout、任务状态=succeeded/failed，并验证这些值实际有助于诊断。跨租户授权错误还需要适当的安全审计；不要把每个 tenant ID 作为指标标签暴露。

### 按证据缓解并确认恢复

告警触发后按固定证据顺序推进：

1. **确认影响范围。** 检查事件数、好事件比例、5xx/超时、路由/区域和新镜像摘要。确认遥测还在到达，分母仍按原 SLI 计算。
2. **定位阶段。** 比较入口、数据库、队列、worker 与对象存储的延迟、错误和饱和度；挑选受影响的追踪，再用标识查相关日志。异步任务要同时看最老消息年龄、队列深度、未确认消息数和死信队列；见[发布确认与消费者 ACK](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。
3. **按证据降低用户影响。** 若指标窗口显示新摘要的 canary 超出当前错误率或时延发布门槛，应停止增加该摘要流量；前述 900/720/600 ms trace 用于定位到连接池等待，而不是单独作为停放量依据。若连接池等待接近容量边界，可限制该版本的读流量并先恢复数据库连接余量。只有旧版本满足当前安全不变量时才能回到旧摘要；若旧版本含同一跨租户缺陷，则隔离受影响入口或前向修复，不能盲目回滚。
4. **验证短期恢复。** 在随后滚动 10 分钟窗口取得至少 100 个符合条件的请求后，确认好事件率达到已设的短期放量恢复门槛（本例为至少 99%），同时检查连接池等待、队列最老消息年龄及代表性 job 是否恢复；再经同一已装配入口验证 tenant-a 得到 200/预期数据、tenant-b 得到 404，才继续放量。不能只以“当前没有触发低于 99% 的告警”判断恢复，因为更低的比例也可能尚未持续 5 分钟。长期 30 天错误预算继续单独跟踪。安静的告警、绿色探针或 queue 收到 ACK 都不等同于 report 42 已按权限返回。
5. **记录改进。** 记下用户影响时间窗、因果机制、缓解动作、关联测试和遥测缺口，以及负责修复的具体改动。

> [!info]- 来源
> - OpenTelemetry [Signals](https://opentelemetry.io/docs/concepts/signals/)、[Traces](https://opentelemetry.io/docs/concepts/signals/traces/)、[Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/)、[Logs](https://opentelemetry.io/docs/concepts/signals/logs/) 与[Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)，checked 2026-11-06：信号的用途、trace/span 与上下文跨服务传播；cardinality 和隐私边界按本文的 report 例子应用。
> - Google SRE Workbook, [Chapter 2: Implementing SLOs](https://sre.google/workbook/implementing-slos/)，checked 2026-11-06：为用户结果定义事件 SLI、时间窗、错误预算和迭代规则。本文的 30 天、400 ms、99.5% 数值是合成示例，不是该来源建议的统一目标。
## 37. 怎样根据输入约束和访问模式选择算法？

报表请求已从数据库得到 acct-17 的 report 42 事件页：1,024 条，按 (occurred_at, event_id) 升序排列。接口要定位游标、显示分类树、缓存最近查看的页面，并按事件描述处理 Unicode（统一码）文本。选算法前先写明输入保证、要执行的操作和结果约束；只有这样才能证明候选范围可以丢弃，并估计成本。

本篇给出选型与复杂度模型。后续章节分别回答[数据结构怎样匹配访问方式](#38.%20%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%A6%82%E4%BD%95%E5%8C%B9%E9%85%8D%E8%AE%BF%E9%97%AE%E6%96%B9%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F)、[队列和栈怎样表示待处理工作](#39.%20%E9%98%9F%E5%88%97%E5%92%8C%E6%A0%88%E6%80%8E%E6%A0%B7%E8%A1%A8%E7%A4%BA%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%EF%BC%9F)、[LRU 如何维护按键查找与新近顺序](#40.%20%E6%9C%80%E8%BF%91%E6%9C%80%E5%B0%91%E4%BD%BF%E7%94%A8%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E6%8C%89%E9%94%AE%E6%9F%A5%E6%89%BE%E5%B9%B6%E6%9B%B4%E6%96%B0%E6%9C%80%E8%BF%91%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F)、[有序数据怎样缩小候选范围](#41.%20%E6%9C%89%E5%BA%8F%E6%95%B0%E6%8D%AE%E6%80%8E%E6%A0%B7%E8%AE%A9%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%E5%AE%89%E5%85%A8%E6%8E%92%E9%99%A4%E5%80%99%E9%80%89%EF%BC%9F)、[动态规划怎样定义状态和更新顺序](#45.%20%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92%E5%A6%82%E4%BD%95%E5%AE%9A%E4%B9%89%E7%8A%B6%E6%80%81%E5%B9%B6%E5%AE%89%E6%8E%92%E6%9B%B4%E6%96%B0%E9%A1%BA%E5%BA%8F%EF%BC%9F)、[分区如何改变排序成本](#46.%20%E5%88%86%E5%8C%BA%E5%A6%82%E4%BD%95%E6%94%B9%E5%8F%98%E5%BF%AB%E9%80%9F%E6%8E%92%E5%BA%8F%E7%9A%84%E6%97%B6%E9%97%B4%E5%92%8C%E7%A9%BA%E9%97%B4%E4%BB%A3%E4%BB%B7%EF%BC%9F)和[文本算法应选哪种字符单位](#47.%20%E6%96%87%E6%9C%AC%E7%AE%97%E6%B3%95%E5%BA%94%E6%8C%89%E7%A0%81%E5%85%83%E3%80%81%E7%A0%81%E7%82%B9%E8%BF%98%E6%98%AF%E5%AD%97%E7%B4%A0%E7%B0%87%E5%A4%84%E7%90%86%EF%BC%9F)。

### 先写明不变量，再选方法

事件页按复合键 (occurred_at, event_id) 排序，因此可用相同规则二分定位游标；这不意味着 event_id 单独有序。若顺序、键或空值排序规则改变，数据顺序和比较器也要一起改变。若数据未排序，则不能直接二分；可扫描，或先排序并计入预处理成本。

~~~mermaid
flowchart LR
    I[输入保证与规模] --> O[需要执行的操作]
    O --> P[可证明的候选排除或状态复用]
    P --> C[时间、空间与分配成本]
    C --> V[用边界输入复算结果]
~~~

例如，有序页中每次中点比较可以排除一半范围；动态规划复用相同子问题的结果；队列用头下标出队可免于搬移其余项。若缺少相应不变量，复杂度表中的数字便不适用。

### Big-O 表示增长，不是耗时承诺

Big-O notation（大 O 记号）描述输入规模增大时，操作数或额外空间的渐近上界，省略常数因子和低阶项。这里 n 是元素数；背包问题的 W 是数值容量，不是表示容量所需的位数。期望复杂度还依赖哈希分布等假设，需要明确标出。

| 增长量 | 典型例子 | 成立条件 |
|---|---|---|
| O(1) | 数组下标访问 | 下标已知且合法；按值查找不是常数时间 |
| O(1) 期望 | 哈希表查找 | 哈希值充分分散；这是期望模型，不是所有实现的严格界 |
| O(log n) | 有序数组二分、平衡搜索树 | 数据有序或树高受不变量约束 |
| O(n) | 顺序扫描 | 每个元素检查常数次 |
| O(n log n) | 归并排序、较均衡的快速排序 | 快速排序最坏会退化到 O(n²) |
| O(n²) | 两层全量扫描、平方级简单排序 | 两层循环均随 n 线性增长 |
| O(2ⁿ) | 朴素递归 Fibonacci 的上界、枚举子集 | 搜索树节点或候选数；按每个候选常数工作计 |
| O(n!) | 枚举所有排列 | 搜索树节点工作；每个节点做常数工作时成立 |

这些界只覆盖指定模型中的工作量。若枚举器还要复制并输出每个完整候选，输出成本要另算：从 n 个元素生成全部子集并复制为数组，元素总数为 n·2ⁿ⁻¹；输出所有 n 项排列则要写出 n·n! 个元素。连续数组扫描可能比指针跳转更快；哈希表扩容会让单次插入成本波动；数据库索引还涉及存储页读取。大 O 不替代测量，也不消除数据布局、内存局部性和运行时常数的影响，见[内存局部性如何改变实际成本](#48.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)。

> [!example] 1,024 条事件页上的查找
> 假设事件已按复合游标键升序，比较键的工作量为常数。目标位于末尾时，扫描需比较 1,024 次；二分最多进行 11 次中点探测，因为 2¹⁰=1,024，2¹¹=2,048；每次探测调用一个常数时间比较器，再判断比较结果。探测次数不等同于底层关系判断次数：若用直接 `===` 和 `<` 的标量写法，末尾命中例共做 21 次关系判断。若单次查找前要排序，预处理成本可能超过扫描。

### 怎样判断选型假设是否成立？

检查目标是定位还是排序、排序由谁建立且是否使用同一比较规则；是否存在可复用子问题、状态是否包含转移需要的信息；是否允许原地修改、复制、分配、扩容和递归栈是否进入内存预算；空输入、重复键、相同排序值、零容量、超大数和非 ASCII 文本是否改变结果。最后用边界输入复算返回值、副作用和复杂度条件。若不变量失效，换成线性扫描或显式预处理并计入成本。

> [!info]- 来源
> - 本章渐近复杂度表作为通用算法分析摘要；1,024 项二分中点探测上界由每轮区间减半复算。
## 38. 数据结构如何匹配访问方式，复杂度界何时成立？

报表 42 要按下标显示事件页、按 event_id 找记录、按时间顺序遍历；分类视图需要层级结构，运行时也可能保存工作树。选择数据结构时，应看目标如何被找到、链接如何更新、是否需要排序，以及树高或哈希分布等前提是否成立。实际速度还会受连续存储和指针跳转影响。

### 数组、链表和树各自适合什么操作？

| 结构 | 访问或查找 | 插入、删除 | 条件与代价 |
|---|---|---|---|
| 数组 | 已知下标 O(1)；按值找元素 O(n) | 中间改动 O(n)，后续元素要移动 | 连续访问方便；增长时可能分配和复制 |
| 单链表 | 按值或下标找节点 O(n) | 已知前驱链接时 O(1)，否则先找前驱 | 删除节点需要前驱 |
| 双向链表 | 查找通常需外部索引；裸链表 O(n) | 已知节点时 O(1) 改邻接链接 | 每个节点多存前后引用 |
| 高度平衡搜索树 | 搜索 O(log n) | 插入、删除 O(log n) | 需要不变量限制树高 |
| 未平衡搜索树 | 最坏 O(n) | 最坏 O(n) | 递增插入可形成长链 |
| Trie 前缀树 | 长度 m 的键约 O(m) | 沿字符路径增删 | 子边选择成本需受控；可能占较多内存 |

链表只有在已知所需节点/链接时才是 O(1) 更新；先扫描定位会让整体操作成为 O(n)。树的 O(log n) 需要高度界。连续数组扫描通常比指针追逐更有局部性，硬件成本见[内存局部性如何影响访问](#48.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)。

### 树的遍历顺序和搜索条件是什么？

二叉树深度优先遍历有三种访问时机：中序为左、节点、右；仅当满足 binary search tree（BST，二叉搜索树）次序规则时结果才升序。前序先节点，适合配合结构信息序列化；后序先子节点，适合先计算或释放子树。下面迭代中序返回第 k 小值；要求节点值为有限数字、比较规则一致且树满足 BST 次序（含其重复值规则）。重复值按节点分别计数；若实现把同值压在一个节点的计数器里，选择第 k 项时也要计入该计数。k 非正、非整数或节点不足时返回 null。先沿树高下降，再弹出并访问至多 k 个节点，时间 O(h+k)，最坏 O(n)；栈空间 O(h)，h 是树高；平衡树 h=O(log n)，退化时 h=O(n)。

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

red-black tree（红黑树）给二叉搜索树节点着色，约束红节点孩子为黑、路径黑高相同，并把根和叶哨兵按实现视为黑色。由此高度有 O(log n) 界，搜索、插入、删除最坏 O(log n)。Java TreeMap API 明确采用红黑树；C++ std::map 保证有序关联容器操作的对数界，但标准不规定树形。不能从一种实现推断另一种产品。

B-tree（B 树）每个节点容纳多个键，以降低存储页读取次数；其内部节点也可以保存记录或记录引用。B+ tree（B+ 树）内部节点只用于导航，记录保存在叶节点，叶页通常相连以支持范围扫描；具体数据库索引布局由产品文档决定。trie（前缀树）共享键前缀，适合前缀查询；m 是键长度，若每个字符转移能以常数期望时间选出，查找约 O(m)，否则还要加上各节点的子边查找成本。子边表示也会改变总内存。

### 哈希表为什么有碰撞，何时能快速查找？

#### Java SE 25 HashMap 契约与 OpenJDK 25u 实现边界

哈希表根据键的哈希值选桶，再在桶内处理冲突。不同键可落入同一桶，扩容只能改变分布而不会消除碰撞。Java 中 equals 相等的键必须有相同 hashCode；若键入表后改变参与 hashCode/equals 的字段，后续查询可能找不到原条目。哈希表适合精确键查找，不保证按键排序。

Java SE 25（LTS）HashMap 允许一个 null 键和多个 null 值，不保证迭代顺序，也不负责并发安全。合理散列下 get/put 有常数时间期望；哈希分布很差时碰撞会增加成本。默认初始容量为 16、负载因子为 0.75；超过阈值后表会扩容。扩容时要重分桶，单次 put 可能花 Θ(n)，把一系列插入的扩容成本摊开后才是均摊常数；散列冲突仍另算。

OpenJDK 25u 维护分支在桶索引前用 h ^ (h >>> 16) 扩散哈希高位，并定义 TREEIFY_THRESHOLD=8、MIN_TREEIFY_CAPACITY=64。对普通 putVal 的链表桶追加路径，8 个既有碰撞节点后追加第 9 个：若表容量已是 64，该次 put 将桶树化；若初始容量为 16，且这些键的扩散后哈希值完全相同，第 9、10 个碰撞项分别触发扩容到 32、64，第 11 个才树化。仅在旧表中同桶的不同哈希值可能在扩容时分到不同桶，不能沿用这个极端例的计数。这个计数只描述该源码路径，不能外推到 compute/merge 或任意树桶查询的严格 O(log n) 界。旧档案原解释针对 OpenJDK 17；截至 2026-11-06 核对的 17u 维护分支在哈希扰动和相关阈值上相同。桶细节是源码实现，不是 Java Map 接口保证；键的可比较性可帮助处理哈希值相同的树桶项，差的哈希分布仍会影响总体成本。

### 怎样遍历文档树并转换扁平记录？

报表分类可用树显示。Document Object Model（DOM，文档对象模型）分类节点组成树。depth-first search（DFS，深度优先搜索）沿一个分支前进，breadth-first search（BFS，广度优先搜索）按层访问；DOM 树每个节点从根只有一条路径，而无权图 BFS 的最短路结论按边数计。代码在每个节点调用 visit 后立即快照该节点的子节点：该回调对当前节点做的修改会进入随后快照；这不是从遍历开始时冻结的整棵 DOM 快照。

~~~javascript
function dfs(root, visit) {
  if (!root) return;
  visit(root);
  for (const child of Array.from(root.childNodes)) dfs(child, visit);
}
function dfsIterative(root, visit) {
  if (!root) return;
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    visit(node);
    const children = Array.from(node.childNodes);
    for (let i = children.length - 1; i >= 0; i--) stack.push(children[i]);
  }
}
function bfs(root, visit) {
  if (!root) return;
  const queue = [root];
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head];
    visit(node);
    for (const child of Array.from(node.childNodes)) queue.push(child);
  }
}
~~~

对固定树且 visit 每次为 O(1) 时，访问 n 个节点的遍历工作为 O(n)，显式栈/队列最坏 O(n) 空间；若回调改树，应按实际访问的节点数和回调成本另算。每个节点在调用 visit 后立即快照自己的 childNodes；回调对该节点的修改会影响随后快照，遍历不是整棵树在开始时的一致快照。BFS 用递增 head 下标；反复 shift 可能搬移剩余元素而使总工作达 O(n²)。实现见[队列和栈如何表示待处理工作](#39.%20%E9%98%9F%E5%88%97%E5%92%8C%E6%A0%88%E6%80%8E%E6%A0%B7%E8%A1%A8%E7%A4%BA%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

扁平分类行可两趟转成树：第一趟用 Map 按唯一 ID 建节点，第二趟按 parentId 接到父节点。每个父节点的 children 按输入行出现顺序追加，因此保留各自子项的相对输入顺序。约定一个根 parentId=0、ID 唯一且不能使用保留的根标记 ID 0、所有父 ID 存在；然后从根遍历检查不可达环。在常见平均常数时间的 Map 查找模型下，预期 O(n) 时间、O(n) 空间；ECMAScript 只要求平均访问次线性，未承诺精确 O(1)。

~~~javascript
function arrayToTree(rows) {
  if (!Array.isArray(rows)) throw new TypeError('rows must be an array');
  const nodes = new Map();
  for (const row of rows) {
    if (!row || !Number.isSafeInteger(row.id) || row.id <= 0 || nodes.has(row.id)) {
      throw new RangeError('rows must have unique positive safe-integer IDs');
    }
    nodes.set(row.id, { ...row, children: [] });
  }
  const roots = [];
  for (const row of rows) {
    const node = nodes.get(row.id);
    if (row.parentId === 0) roots.push(node);
    else {
      if (!Number.isSafeInteger(row.parentId) || row.parentId <= 0) {
        throw new RangeError('parentId must be 0 or a positive safe integer');
      }
      const parent = nodes.get(row.parentId);
      if (!parent) throw new RangeError('parent ID does not exist');
      parent.children.push(node);
    }
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

> [!example] 两行分类记录怎样变成一棵树？
> 输入为 [{id:1,parentId:0,name:根},{id:2,parentId:1,name:收入}]。第一趟 Map 建出两个空 children；第二趟把 id=1 设为根，再把 id=2 接到 parentId=1。根遍历访问 1、2，seen 与 Map 都有两项，因此数据可达且合法。treeToArray 再输出 [{id:1,parentId:0,name:根},{id:2,parentId:1,name:收入}]。

treeToArray 按前序输出父节点后再输出各子树；它不恢复任意扁平输入原先跨父节点交错的行顺序。回转假设输入为 ID 正安全整数、单根无环树，根 ID 标记 0 只用于 parentId；示例只输出 id、parentId、name；其他业务字段需显式复制。根标记不是 0 时应替换为实际协议。

### React Fiber 内部为什么把树节点链接起来？

React Fiber 节点用 child、sibling、return 等链接表达父子关系和同级顺序，使协调器能按工作单元保存进度。树仍是树，只是同级孩子通过 sibling 串联。transition 等并发特性允许某些渲染工作暂停、重启或让位；不能据此说每个 render 和 DOM commit 都可任意中断。DOM 变更在准备好的 commit 阶段应用。Fiber 布局是实现细节，应用应依赖 React 公共 API。

> [!info]- 来源
> - HashMap 契约、默认值与期望复杂度：[Java SE 25 HashMap API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/HashMap.html)，Java SE 25。
> - 哈希扰动与树化机制：[OpenJDK 17u HashMap 源码](https://github.com/openjdk/jdk17u/blob/master/src/java.base/share/classes/java/util/HashMap.java)、[OpenJDK 25u HashMap 源码](https://github.com/openjdk/jdk25u/blob/master/src/java.base/share/classes/java/util/HashMap.java)，2026-11-06 核对维护分支，作为实现样本。
> - 有序容器契约：[Java SE 25 TreeMap API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/TreeMap.html)、[C++ associative containers](https://eel.is/c++draft/associative.reqmts)。
> - React 并发行为：[React 18](https://react.dev/blog/2022/03/29/react-v18)，2022-03-29；Fiber 内部字段：[React Fiber 类型](https://github.com/facebook/react/blob/main/packages/react-reconciler/src/ReactInternalTypes.js)，2026-11-06 核对。
## 39. 队列和栈怎样表示待处理工作？

处理报表 42 的事件流时，通知消费者应先处理最早到达的事件；解析嵌套表达式时，应先返回最近进入的未完成分支。前者是 first-in, first-out (FIFO，先进先出) 队列，后者是 last-in, first-out (LIFO，后进先出) 栈。选好顺序后，还要让空状态和可存储值之间没有歧义。

### 队列怎样同时维护头、尾和空状态？

链表队列维护 head、tail、length：空时头尾均为 null 且长度为 0；非空时 head 指向最早项，tail 指向最新项且 tail.next 为 null。删除最后一项要同时清空头尾。空读抛错，因此 null 和 undefined 都可以是队列值。

~~~javascript
class Queue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }
  get isEmpty() { return this.length === 0; }
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

enqueue、dequeue、peek 都是 O(1)，但每个节点需要分配并维护链接。容量有上限时可用环形缓冲区；一次性的 BFS 扫描可用数组与递增 head 下标。长期 FIFO 若只增加 head，会保留尚未清理的已消费引用并让数组持续增长；可清空已消费槽并定期压缩，或改用环形缓冲区。Array.shift 的可观察语义不承诺某引擎的搬移成本，但常见数组实现会调整剩余索引，连续出队可能累积平方级工作。

用 head 而不是槽值表示空状态时，队列可以安全保存 null 和 undefined。下面两项出队后 head 递增；即使第 2 项本身是 undefined，head 仍小于长度，所以它是已存值而非“空”的信号。实际长期队列还应把消费槽设为 undefined 释放引用，并配合压缩或环形缓冲区控制数组增长。

| 操作 | 数组状态 | head | 结果 / 空状态 |
|---|---|---:|---|
| 初始 | [null, undefined] | 0 | 还有 2 项 |
| dequeue | [undefined, undefined] | 1 | 取出 null；还有 1 项 |
| dequeue | [undefined, undefined] | 2 | 取出已存的 undefined；此时 head 等于长度，队列为空 |

旧数值队列以 null 表示空：仅因为值域是 number，null 不会与有效值混淆；若要允许 null/undefined，须改为显式 isEmpty、带状态的返回值或异常。其受限实现保留如下。

> [!example]- 可选：数值专用 TypeScript 空值哨兵
> ~~~typescript
> interface QueueNode { val: number; next: QueueNode | null; }
> class NullableNumberQueue {
>   private head: QueueNode | null = null;
>   private tail: QueueNode | null = null;
>   private length = 0;
>   offer(val: number): void {
>     const node: QueueNode = { val, next: null };
>     if (this.tail) this.tail.next = node;
>     else this.head = node;
>     this.tail = node;
>     this.length++;
>   }
>   poll(): number | null {
>     if (!this.head) return null;
>     const value = this.head.val;
>     this.head = this.head.next;
>     if (!this.head) this.tail = null;
>     this.length--;
>     return value;
>   }
>   get size(): number { return this.length; }
> }
> ~~~

### 栈怎样保留最近未完成的工作？

数组末尾 push/pop 表达栈的入栈和出栈；显式空检查可避免把已存的 undefined 当作空栈。

~~~javascript
class Stack {
  constructor() { this.items = []; }
  get isEmpty() { return this.items.length === 0; }
  push(value) { this.items.push(value); }
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

push/pop 是末端操作；动态数组扩容时可能分配并复制，因此单次耗时会变化，通常按摊还常数时间分析。未知输入深度的递归还受运行时栈大小限制，可改用显式栈。

> [!info]- 来源
> - 数组末端和首端操作的规范行为：[ECMAScript 2026 indexed collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)，Array.prototype.shift/push/pop。标准描述可观察效果，不规定某引擎的数组搬移算法。
## 40. 最近最少使用缓存怎样按键查找并更新最近使用顺序？

报表界面最近访问 acct-17 的 report/42 游标页和 report/41 页面。容量已满时，Least Recently Used (LRU) cache（最近最少使用缓存）要淘汰最久未访问条目，因此同时需要按键查找和按新近顺序淘汰。若缓存受保护的报表数据，缓存键须隔离账户/授权范围、过滤器和游标；缓存命中不能代替授权检查。

### 用 Map 插入顺序表示新近程度

ECMAScript Map 保留键的插入顺序。命中时删后重设，把键移到最新端；迭代器按顺序返回键，首项是最旧键。实现支持任意键和值，has 可区分存入 undefined 与键缺失；对象键按对象身份比较，内容相同但新建的数组仍是另一个键；容量为非负整数，容量 0 时不留数据。

~~~javascript
class LRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
    this.capacity = capacity;
    this.cache = new Map();
  }
  has(key) { return this.cache.has(key); }
  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }
  put(key, value) {
    if (this.capacity === 0) return;
    if (this.cache.has(key)) this.cache.delete(key);
    else if (this.cache.size === this.capacity) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
~~~

> [!example] 容量为 2 的淘汰过程
> put(A, 页面42)、put(B, 页面41) 后，A 最旧、B 最新。get(A) 命中后顺序变成 B、A。put(C, 首页) 淘汰 B，留下 A、C。更新已有键也把它移到最新端。
>
> | 操作 | 最旧 → 最新 |
> |---|---|
> | put(A) | A |
> | put(B) | A, B |
> | get(A) | B, A |
> | put(C) | A, C；B 被淘汰 |

ECMAScript 要求 Map 的平均访问复杂度为次线性，但不承诺精确 O(1)。更重要的是，Map 的键查找保证不能推出 `keys().next()` 找到首个仍存活键也为 O(1)：新迭代器可能略过此前删除的内部位置，反复删后重插的工作量还取决于实现如何维护迭代状态。此版顺序正确、代码较短，但不能仅凭 Map 键访问界给每次淘汰一个 O(1) 上界。

### 用双向链表加 Map 显式维护索引与顺序

Map 把键映射到节点，双向链表通过已知节点更新相邻链接、从尾部淘汰。头尾哨兵使插入头部和删除节点无需为真实边界写分支。

~~~javascript
class ListNode {
  constructor(key, value) { this.key = key; this.value = value; this.prev = null; this.next = null; }
}
class LinkedLRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
    this.capacity = capacity;
    this.nodes = new Map();
    this.head = new ListNode(null, null);
    this.tail = new ListNode(null, null);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }
  has(key) { return this.nodes.has(key); }
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

已知节点时，链表摘除、移到 head 和从 tail 取最旧项都只改固定数目的链接，因此是确定的 O(1)；完整 get/put 还包含 Map 查找或更新。若所选 Map 实现对键访问提供期望 O(1)，整项操作也可按期望 O(1) 分析；ECMAScript 对 Map 的最低保证只是平均次线性。Map 版适合展示紧凑实现，链表版把淘汰顺序变成显式首尾链接。

> [!example]- 可选：不使用 Map/Record 的数字键练习变体
> 旧练习用 Object.create(null) 建无原型索引，以数字键查节点；命中移至头部，满容量插入淘汰尾节点。get 返回 -1 表示未命中，因此调用契约须约定 -1 不属于有效缓存值（代码本身不拒绝写入 -1）；键和值沿用 number 契约，不限为有限整数；索引把键转成属性名，因此 +0/-0 共用 "0"，NaN 共用 "NaN"，正负无穷分别成为属性名。大于安全整数范围的不同文本 ID 不能先存成 Number 再指望区分。容量须为非负整数。对象属性访问的复杂度是引擎行为，不是 ECMAScript 的精确 O(1) 保证。
>
> ~~~typescript
> class ListNode {
>   prev: ListNode | null = null;
>   next: ListNode | null = null;
>   constructor(readonly key: number, public value: number) {}
> }
> class NumericLRUCache {
>   private readonly index: { [key: string]: ListNode } = Object.create(null);
>   private head: ListNode | null = null;
>   private tail: ListNode | null = null;
>   private size = 0;
>   constructor(private readonly capacity: number) {
>     if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
>   }
>   get(key: number): number {
>     const node = this.index[key];
>     if (!node) return -1;
>     this.moveToHead(node);
>     return node.value;
>   }
>   put(key: number, value: number): void {
>     if (this.capacity === 0) return;
>     const existing = this.index[key];
>     if (existing) {
>       existing.value = value;
>       this.moveToHead(existing);
>       return;
>     }
>     if (this.size >= this.capacity) this.removeTail();
>     const node = new ListNode(key, value);
>     this.index[key] = node;
>     this.addHead(node);
>     this.size++;
>   }
>   private addHead(node: ListNode): void {
>     node.prev = null;
>     node.next = this.head;
>     if (this.head) this.head.prev = node;
>     this.head = node;
>     if (!this.tail) this.tail = node;
>   }
>   private remove(node: ListNode): void {
>     if (node.prev) node.prev.next = node.next;
>     else this.head = node.next;
>     if (node.next) node.next.prev = node.prev;
>     else this.tail = node.prev;
>     node.prev = null;
>     node.next = null;
>   }
>   private moveToHead(node: ListNode): void {
>     if (this.head === node) return;
>     this.remove(node);
>     this.addHead(node);
>   }
>   private removeTail(): void {
>     if (!this.tail) return;
>     const oldest = this.tail;
>     this.remove(oldest);
>     delete this.index[oldest.key];
>     this.size--;
>   }
> }
> ~~~

> [!info]- 来源
> - Map 键值、插入顺序与平均访问复杂度：[ECMAScript 2026 keyed collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)，Map Objects；规范承诺平均次线性访问，不承诺精确 O(1)。
> - 容量 2 状态与链表指针更新按本页代码复算；无 Map 变体以 TypeScript 5.7.2 编译并运行。
## 41. 有序数据怎样让二分查找和双指针安全排除候选？

报表 42 的事件页按 (occurred_at, event_id) 升序排列。若目标游标与这组键使用同一比较规则，binary search（二分查找）可以丢弃一半候选；若数组无序或只按 event_id 比较，就不能从时间顺序推断安全的排除范围。two pointers（双指针）也依赖同样的证明：每次移动前要说明为何被排除的一整批组合不可能成为答案。

### 二分查找如何缩小有序区间？

binary search（二分查找）在升序数组中维持闭区间 [left, right]。比较中点后，若中点小于目标，则它及左侧元素都不可能匹配，令 left=middle+1；若大于目标，右侧同理。下例返回任意一个匹配下标；空数组或找不到目标时返回 -1。

~~~javascript
function binarySearch(values, target, compare) {
  let left = 0;
  let right = values.length - 1;
  while (left <= right) {
    const middle = left + Math.floor((right - left) / 2);
    const order = compare(values[middle], target);
    if (order === 0) return middle;
    if (order < 0) left = middle + 1;
    else right = middle - 1;
  }
  return -1;
}
~~~

标量示例可传入 `(a, b) => a - b`。以 [3, 7, 11, 15, 19, 23, 27] 查找 19：循环不变式是“若目标存在，它仍在当前闭区间”。

| 轮次 | 当前区间 | 中点和值 | 更新 |
|---|---|---|---|
| 1 | [0,6] | 3 → 15 | 目标更大，left=4 |
| 2 | [4,6] | 5 → 23 | 目标更小，right=4 |
| 3 | [4,4] | 4 → 19 | 命中 |

若改查 20，前两轮后比较 19 并令 left=5，区间变空，返回 -1。

固定宽度整数语言中用 left + floor((right-left)/2) 避免 left+right 溢出。JavaScript 数组索引本身远小于 Number 精确整数上限，但差值写法便于移植。若要找重复值的第一个位置，应改用 lower bound：命中时仍收缩右半边，而非立刻返回。

报表 42 的游标按 `(occurred_at, event_id)` 字典序比较：先比 occurred_at，只有时间相同才比 event_id。下面假设时间使用统一 UTC、固定精度的 ISO 8601 字符串，且字典序与时间顺序一致，event_id 是安全整数；生产代码的比较器还必须与数据库的类型、空值顺序和排序规则一致。

~~~javascript
function compareEvent(a, b) {
  if (a.occurred_at < b.occurred_at) return -1;
  if (a.occurred_at > b.occurred_at) return 1;
  return a.event_id < b.event_id ? -1 : a.event_id > b.event_id ? 1 : 0;
}
~~~

| 排序行 | occurred_at | event_id | 与游标 (09:00, 41) 的顺序 |
|---|---|---:|---|
| A | 09:00 | 41 | 相等，确切命中游标 |
| B | 09:00 | 42 | 大于游标，下一页边界候选 |
| C | 09:01 | 13 | 也大于游标，但排在 B 后 |

比较器必须对同一排序域稳定地返回负数、零或正数。`binarySearch` 用 `compareEvent` 可以查确切游标；分页取下一页时通常要找第一个比较结果严格大于零的行（upper bound，上界），不能要求游标行仍存在。若行 A 已删除，B 仍是正确边界；这依赖相同排序规则、有效游标及相同数据范围，并要求 `(occurred_at,event_id)` 在该范围内唯一。若两个记录排序键完全相同，而页尾停在两者之间，严格 `>` 会跳过后一条；应加上唯一的 tie-breaker（平局裁决键）。表中时间为完整时间戳的简写，C 的 ID 虽更小，仍因时间更晚而排在 B 后。

### 双指针何时能替代重复扫描？

双指针仅在排序或移动不变量能证明安全时减少搜索空间；它不是一般嵌套循环的替代品。

#### 有序数组两数之和

数组升序时，若两端和小于 target，左端值与任何剩余右端相加都不会更大，因此 left 可以前进；若和过大，right 可后退。下例返回两个不同位置的下标或 null；重复值可被不同下标选中。输入假设为有限安全整数，避免 Number 精度和溢出语义影响比较。

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

#### 把零移到末尾并保留其他次序

next 表示下一个非零值应该写入的位置。每遇到非零值就与该位置交换，因此非零元素相对顺序不变，函数原地修改并返回同一数组。

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

> [!example] 两个指针怎样缩小候选集合
> 对 [1, 2, 4, 7, 11] 求和为 9：两端 1+11=12 太大，排除 11 与当前或更大左端值的组合，右指针左移；1+7=8 太小，排除 1 与当前/更小右项的组合，左指针右移；2+7=9，返回 [1,3]。排序是这项证明的前提。

> [!info]- 来源
> - 二分与双指针不变量按本页闭区间/升序数组逐步复算；事件页复合游标必须使用与来源排序相同的字典序比较。
## 42. 怎样在边界前进时维护一个有效窗口或活动区间？

合成报表 42 按到达时间记录事件。一个问题要找连续 k 条事件中净变化最大的窗口，另一个问题要找出处理耗时累计达到阈值时最短的连续事件段；资源预约表则要找同一时刻最多有多少任务占用资源。前两项是 fixed-size sliding window（固定宽度滑动窗口）和 variable-size sliding window（变长滑动窗口），第三项要用扫描线。三者都维护随边界变化的状态，但输入次序、状态不变量和移动理由各不相同。

本章统一把数组窗口写成半开区间 [left, right)：包含 left，不包含 right。长度因此是 right - left；相邻的 [a, b) 与 [b, c) 不共享端点。

### 固定宽度窗口：移出一项，再加入一项

假设按到达顺序记录每个事件对待处理任务数的净变化，完成任务可为负数。输入 [4, -2, 3, 5]，求任意连续 3 条事件的最大净变化。第一段 [0, 3) 的和是 4 - 2 + 3 = 5。右边界前进一格后，新段 [1, 4) 只需移出 4、加入 5，得到 -2 + 3 + 5 = 6。

| 窗口 | 本轮变化 | 和 |
|---|---|---:|
| [0, 3) | 4 - 2 + 3 | 5 |
| [1, 4) | 旧和 5 − 移出 4 + 加入 5 | 6 |

循环不变量是：每轮比较时，sum 恰好等于当前长度为 k 的 [left, right) 中所有值的和。固定宽度意味着每次右边界多含一项、左边界少含一项，所以只需增量更新这两项；不要求数据非负。每个输入项至多加入和移出一次，扫描为 O(n) 时间、O(1) 额外空间。这里按到达顺序计算；为了套用有序数组的双指针套路而先排序，会改变连续事件的含义。

~~~javascript
function maxFixedWindowSum(values, k) {
  if (!Array.isArray(values)) throw new TypeError('values must be an array');
  if (!Number.isSafeInteger(k) || k <= 0) throw new RangeError('k must be a positive safe integer');
  for (const value of values) {
    if (!Number.isSafeInteger(value)) throw new TypeError('values must contain safe integers');
  }
  if (values.length < k) return null;

  let sum = 0;
  for (let i = 0; i < k; i++) {
    sum += values[i];
    if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');
  }
  let best = sum;

  for (let right = k; right < values.length; right++) {
    sum -= values[right - k];
    if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');
    sum += values[right];
    if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');
    if (sum > best) best = sum;
  }
  return best;
}

console.log(maxFixedWindowSum([4, -2, 3, 5], 3)); // 6
console.log(maxFixedWindowSum([], 1));            // null
~~~

若 n < k（包括空输入），没有完整窗口，函数返回 null；k 必须是正整数。示例限定所有值与中间窗口和都在 JavaScript 安全整数范围内；业务值为小数时需改用相应的数值精度约定。

### 变长窗口：只在扩展和收缩都可证明时使用

另一项报表指标是：按事件顺序找到处理耗时总和至少达到 5 毫秒的最短连续区间。每条耗时是非负安全整数。输入 [2, 1, 3, 2] 的扫描如下：

| 新加入下标 | 当前 [left, right) | 和 | 决定 |
|---:|---|---:|---|
| 0 | [0, 1) | 2 | 未达 5，继续扩展 |
| 1 | [0, 2) | 3 | 未达 5，继续扩展 |
| 2 | [0, 3) | 6 | 记录长度 3；移除下标 0 后和为 4，停止收缩 |
| 3 | [1, 4) | 6 | 记录长度 3；移除下标 1 后 [2, 4) 和为 5，记录长度 2；再移除下标 2 后和为 2，停止收缩 |

扫描结束，最短区间是 [2, 4)，即耗时 3 和 2。保持的状态是当前区间总和；右边界每次加入一项。当总和达到阈值时，当前区间有效，尝试向右移 left 来缩短它。非负输入保证移除左项不会让和变大；若移除后低于阈值，再移左就不能从当前区间产生一个有效更短后缀，因此先扩展 right。left 和 right 都只向前，每项最多进入、离开一次，时间 O(n)、额外空间 O(1)。若整个扫描从未达到阈值，返回 null。

~~~javascript
function shortestWindowAtLeast(values, target) {
  if (!Array.isArray(values)) throw new TypeError('values must be an array');
  if (!Number.isSafeInteger(target) || target <= 0) {
    throw new RangeError('target must be a positive safe integer');
  }
  for (const value of values) {
    if (!Number.isSafeInteger(value) || value < 0) {
      throw new TypeError('values must contain non-negative safe integers');
    }
  }

  let left = 0;
  let sum = 0;
  let best = null;
  for (let right = 0; right < values.length; right++) {
    sum += values[right];
    if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');

    while (sum >= target) {
      const candidate = { start: left, end: right + 1, length: right + 1 - left };
      if (best === null || candidate.length < best.length) best = candidate;
      sum -= values[left];
      if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');
      left++;
    }
  }
  return best;
}

console.log(shortestWindowAtLeast([2, 1, 3, 2], 5)); // { start: 2, end: 4, length: 2 }
console.log(shortestWindowAtLeast([1, 2], 5));       // null
~~~

非负约束是这段代码正确性的前提，不是对输入的清洗偏好。若绕过入口的非负检查，把相同移动规则照搬到输入 [1, -1, 5]、阈值 5 上，算法先得到整段 [0, 3) 的和 5，记录长度 3；移除 1 后和变成 4，于是停止收缩并返回长度 3。但 [2, 3) 只含 5，长度为 1。负数让扩展可以降低总和、移除左项也可以提高总和；原来的移动理由失效，不能照搬这个窗口算法。

### sweep line（扫描线）：先排序端点，再维护活动集合大小

预约区间是另一类输入：它们不按开始时间排列，需先把端点排序。对同一批合成任务，预约为 A=[1,4)、B=[2,4)、C=[4,6)。区间采用半开约定，任务在结束时刻已释放，另一个任务可在该时刻开始而不与它重叠。

扫描线按时刻由小到大处理端点。在同一时刻，先结束 [a,t) 的任务，再开始 [t,b) 的任务；代码把同刻端点合成一组，先扣除结束数，再加开始数。这样不会把端点上并不同时活动的任务临时算成重叠。该例的活动数变化为：

| 时刻 | 结束 | 开始 | 处理后活动数 | 峰值 |
|---:|---|---|---:|---:|
| 1 | — | A | 1 | 1 |
| 2 | — | B | 2 | 2 |
| 4 | A、B | C | 1 | 2 |
| 6 | C | — | 0 | 2 |

峰值是 2。若在时刻 4 先加 C 再减 A、B，会短暂算出 3，虽然没有任何时刻三项区间同时包含在内。

~~~javascript
function maxConcurrentHalfOpen(intervals) {
  if (!Array.isArray(intervals)) throw new TypeError('intervals must be an array');
  const events = [];
  for (const interval of intervals) {
    if (!interval || !Number.isFinite(interval.start) || !Number.isFinite(interval.end)) {
      throw new TypeError('each interval needs finite start and end values');
    }
    if (interval.start >= interval.end) {
      throw new RangeError('each interval must satisfy start < end');
    }
    events.push({ time: interval.start, kind: 1 });
    events.push({ time: interval.end, kind: -1 });
  }

  events.sort((a, b) => a.time - b.time || a.kind - b.kind);
  let active = 0;
  let peak = 0;
  for (let i = 0; i < events.length;) {
    const time = events[i].time;
    let starts = 0;
    let ends = 0;
    while (i < events.length && events[i].time === time) {
      if (events[i].kind === -1) ends++;
      else starts++;
      i++;
    }
    active -= ends; // [start, time) 到此已结束
    active += starts; // [time, end) 从此开始
    peak = Math.max(peak, active);
  }
  return peak;
}

console.log(maxConcurrentHalfOpen([
  { name: 'A', start: 1, end: 4 },
  { name: 'B', start: 2, end: 4 },
  { name: 'C', start: 4, end: 6 }
])); // 2
console.log(maxConcurrentHalfOpen([])); // 0
~~~

每个区间必须满足 start < end；空区间不是资源预约，函数拒绝它。排序端点需 O(n log n)，线性分组需 O(n)，事件数组占 O(n) 空间。扫描线与保留到达顺序的窗口都维护局部状态，但前者先重排端点，后者不能改变原序列；两者的正确性分别来自半开端点规则和窗口的移动不变量。

> [!info]- 来源
> - 固定/变长窗口的双指针推进、每个元素有限次进入和离开：[Antti Laaksonen, Competitive Programmer’s Handbook, 2018 draft, §8.1 “Two pointers method” 与 §8.3 “Sliding window minimum”](https://cses.fi/book.pdf)。本页的求和窗口根据各自输入前提推导；带负值的失效例子由本页代码状态复算。
> - 端点排序后维护活动集合的扫描线思路：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §9.3 “Geometric Intersections”](https://algs4.cs.princeton.edu/93intersection/)，并参看作者实现 [IntervalIntersection.java](https://algs4.cs.princeton.edu/93intersection/IntervalIntersection.java.html)。本页使用半开预约区间，因此端点相等时结束项先退出、开始项再进入；示例峰值由代码复算。
## 43. 怎样在不断加入任务时持续取出最高优先级？

合成报表 42 有多个待处理任务，系统一边接收新任务，一边要取出当前最紧急的一项。若每次都重新排序整个集合，就会重复整理旧任务。priority queue（优先队列）只要求快速插入和取出当前最高优先级项；binary heap（二叉堆）用一条父子顺序约束支持这两项操作。

### 堆序只规定父子关系，不会把数组排好序

以下用最大堆，优先级较大的任务靠近根。把完全二叉树（最后一层从左向右填充）按层从左到右放入数组，使用 0 起始下标时，只有 i > 0 的位置才有父节点，父节点下标是 floor((i - 1) / 2)，子节点是 2i + 1 与 2i + 2。堆序要求任一父项不低于它的孩子；除根以外，数组并不保证整体有序。

~~~mermaid
flowchart TD
    i0["下标 0：根"]
    i1["下标 1：左子，2i+1"]
    i2["下标 2：右子，2i+2"]
    i0 --> i1
    i0 --> i2
~~~

本例约定同优先级按先到先出，因此入堆时另带递增序号。表中任务 A 和 B 优先级同为 5，A 先到；C 优先级为 8。

| 操作 | 堆数组（从根到叶） | 发生的修复 |
|---|---|---|
| 插入 A(5) | [A(5)] | 根无需调整 |
| 插入 B(5) | [A(5), B(5)] | 同优先级时 A 序号较早，不交换 |
| 插入 C(8) | [C(8), B(5), A(5)] | C 从下标 2 上浮到根 |
| 取出 | [A(5), B(5)] | 返回 C；末项 A 移到根，与同优先级且较晚的 B 保持先后次序 |

插入时先放数组末尾，再沿父节点上浮；删除根时以末项填根，再沿更高优先级的孩子下沉。堆高为 O(log n)，所以 push 和 pop 各需 O(log n)，peek 为 O(1)，额外存储 O(n)。如果所有元素一开始都已知，可以从最后一个非叶节点向根逐层下沉来建堆，整体 O(n)；若元素逐个到达，则用 push，累计为 O(n log n)。线性 heapify（自底向上建堆）的前提是能同时访问整批初始元素。

普通堆若只比较 priority，并不保证并列项稳定；稳定行为来自代码中的 sequence 次级键。此实现用 BigInt 序号，优先级必须是有限数；进入队列的优先级与序号保持不变。空堆的 peek 和 pop 都返回 null，实际任务包装在对象中，所以任务 value 本身即使是 null，也不与空队列混淆。

> [!example]- 可运行：稳定最大优先队列
> ~~~javascript
> class BinaryHeap {
>   constructor(higher) {
>     if (typeof higher !== 'function') throw new TypeError('higher must be a function');
>     this.higher = higher;
>     this.items = [];
>   }
>
>   get size() { return this.items.length; }
>   peek() { return this.items.length === 0 ? null : this.items[0]; }
>
>   push(value) {
>     const items = this.items;
>     items.push(value);
>     let i = items.length - 1;
>     while (i > 0) {
>       const parent = Math.floor((i - 1) / 2);
>       if (!this.higher(items[i], items[parent])) break;
>       [items[i], items[parent]] = [items[parent], items[i]];
>       i = parent;
>     }
>   }
>
>   pop() {
>     const items = this.items;
>     if (items.length === 0) return null;
>     const root = items[0];
>     const last = items.pop();
>     if (items.length > 0) {
>       items[0] = last;
>       let i = 0;
>       while (true) {
>         const left = 2 * i + 1;
>         const right = left + 1;
>         let best = i;
>         if (left < items.length && this.higher(items[left], items[best])) best = left;
>         if (right < items.length && this.higher(items[right], items[best])) best = right;
>         if (best === i) break;
>         [items[i], items[best]] = [items[best], items[i]];
>         i = best;
>       }
>     }
>     return root;
>   }
>
>   toArray() { return this.items.slice(); }
> }
>
> class StableMaxPriorityQueue {
>   constructor() {
>     this.sequence = 0n;
>     this.heap = new BinaryHeap((a, b) =>
>       a.priority > b.priority ||
>       (a.priority === b.priority && a.sequence < b.sequence)
>     );
>   }
>   get size() { return this.heap.size; }
>   peek() { return this.heap.peek(); }
>   push(priority, value) {
>     if (!Number.isFinite(priority)) throw new TypeError('priority must be finite');
>     this.heap.push(Object.freeze({ priority, sequence: this.sequence, value }));
>     this.sequence += 1n;
>   }
>   pop() { return this.heap.pop(); }
> }
>
> const tasks = new StableMaxPriorityQueue();
> tasks.push(5, 'A');
> tasks.push(5, 'B');
> tasks.push(8, 'C');
> console.log(tasks.pop().value); // C
> console.log(tasks.pop().value); // A
> console.log(tasks.pop().value); // B
> console.log(tasks.pop());       // null
> ~~~

上浮或下沉每一步都沿堆的一层前进；每层最多比较两个孩子，因此不会扫描整堆。若输入量一次性已知而且需要取出全部排序结果，直接排序可能更简单；堆的优势出现在不断插入、只需当前极值，或只保留少量 Top K 的时候。

### 只保留 Top K 时，根节点代表淘汰线

一次性读入 n 个带分数的任务，只保留最大的 K 个时，维护一个最多 K 项的最小堆。下方短代码复用前面折叠示例中的 BinaryHeap。根是当前保留集合里最差的一项：分数不高于它的输入直接丢弃，分数更高的输入弹出根，再插入新项。同分时较早项优先保留，根在同分项中是较晚到达的那个。依次读入 A(8)、B(5)、C(5)、D(7)、E(1)，K=3：

| 已读分数 | 保留集合 | 根（当前淘汰线） | 动作 |
|---|---|---|---|
| A、B、C | A(8)、B(5)、C(5) | C(5) | 堆已满 |
| 再读 D | A(8)、D(7)、B(5) | B(5) | D 淘汰同分项里较晚的 C |
| 再读 E | 不变 | B(5) | E(1) 低于根，丢弃 |

令 k' = min(K, n)。K 为正且 n 非零时，扫描需 O(n log(k' + 1)) 时间，最终按排名排序另需 O(k' log(k' + 1))；额外堆空间为 O(k')。这样 K=1 时扫描仍是 O(n)，K>n 时堆最多只有 n 项。K=0 时仍先校验输入的 n 项，之后返回空数组；n=0 时也返回空数组。代码中的 tie-breaker（平局裁决键）保证选择较早的并列分数。

~~~javascript
function topK(values, k) {
  if (!Array.isArray(values)) throw new TypeError('values must be an array');
  if (!Number.isSafeInteger(k) || k < 0) throw new RangeError('k must be a non-negative safe integer');
  for (const item of values) {
    if (!item || !Number.isFinite(item.score)) {
      throw new TypeError('values must contain items with finite scores');
    }
  }
  if (k === 0 || values.length === 0) return [];

  const worstFirst = (a, b) =>
    a.score < b.score ||
    (a.score === b.score && a.sequence > b.sequence);
  const heap = new BinaryHeap(worstFirst);

  for (let i = 0; i < values.length; i++) {
    const candidate = { score: values[i].score, sequence: BigInt(i), value: values[i] };
    if (heap.size < k) {
      heap.push(candidate);
    } else if (candidate.score > heap.peek().score) {
      heap.pop();
      heap.push(candidate);
    }
  }

  return heap.toArray()
    .sort((a, b) => {
      if (a.score > b.score) return -1;
      if (a.score < b.score) return 1;
      if (a.sequence < b.sequence) return -1;
      if (a.sequence > b.sequence) return 1;
      return 0;
    })
    .map(item => item.value);
}

const scoredTasks = [
  { id: 'A', score: 8 }, { id: 'B', score: 5 }, { id: 'C', score: 5 },
  { id: 'D', score: 7 }, { id: 'E', score: 1 }
];
console.log(topK(scoredTasks, 3).map(task => task.id)); // ['A', 'D', 'B']
console.log(topK(scoredTasks, 0));                     // []
~~~

若只需处理一条已完整到达的短数组且最终要所有项有序，排序一次是 O(n log n)，代码更直接；若 n 很大而 K 很小，Top K 堆把保留空间降到 O(K)，也允许数据流逐项到达。优先队列可用于任务调度；固定大小堆适合流式候选筛选。二者共享堆操作，但取舍目标不同。

> [!info]- 来源
> - 完全二叉树数组表示、上浮/下沉、插入/删除极值、线性 bottom-up heapify：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §2.4 “Priority Queues”](https://algs4.cs.princeton.edu/24pq/)。本页以 0 起始数组实现同一堆序；操作结果由 Node.js 运行复算。
> - 并列键稳定处理的作者实现样本：[Algorithms, 4th ed., StableMinPQ.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/StableMinPQ.java.html)。本页显式把到达序号作为次级比较键，稳定性因此属于本页 API 合约。
## 44. 搜索状态图时，何时永久标记节点，何时必须回退？

合成站点 S 要把一件包裹送到 Z。路网是一张有向图：S 可到 A、B；A 与 B 都可到汇点 T；T 可回到 S，也可到 Z。回边让图有环，共享汇点让两条路线合流。我们先用它找一条最少跳数路线，再枚举简单路线、检查依赖环，最后给路段加入非负代价。

本章的邻接表契约是：顶点 ID 都是字符串；Map 为每个顶点都建一项，包括没有出边的顶点（例如 Z→[]）；所有邻居也都作为顶点键出现。BFS 用 null 表示起点没有父节点，因此不接受 null 顶点 ID。

~~~mermaid
flowchart LR
    S --> A
    S --> B
    A --> T
    B --> T
    T --> S
    T --> Z
~~~

这些操作都沿边扩展候选状态，但保留的状态不同：breadth-first search（BFS，广度优先搜索）只要每个顶点的一条最短边数路径，可以全局去重；枚举简单路径时，同一顶点可能属于不同合法路径，必须只在当前递归路径内标记并在返回时撤销；拓扑排序要求有向边代表依赖且图无环；Dijkstra 选择当前代价最小的未定顶点，要求所有边权非负。

### 无权图最短路：顶点第一次入队时记录父节点

breadth-first search（广度优先搜索，BFS）用先进先出队列按层扩展：先看距 S 一条边的顶点，再看两条边的顶点。队列中的顶点按发现距离非递减排列，所以第一次发现一个顶点时，已找到它的最少边数路径。用 parent 同时记录“已经发现”与首次父节点，之后的回边或另一条同层路线不再入队。

| 处理的顶点 | 刚发现的邻居 | 队列（从前到后） | parent 新增 |
|---|---|---|---|
| S | A、B | A、B | A←S，B←S |
| A | T | B、T | T←A |
| B | T 已发现 | T | 无 |
| T | S 已发现、Z | Z | Z←T |
| Z | 已到目标 | 空 | — |

按首次父节点从 Z 回溯得到 S→A→T→Z，共 3 条边。若邻接表把 B 放在 A 前，BFS 可能返回 S→B→T→Z；两条都是最少边数路径。若目标不可达，返回 null；起点等于目标时返回仅含起点的路径。

~~~javascript
const routes = new Map([
  ['S', ['A', 'B']],
  ['A', ['T']],
  ['B', ['T']],
  ['T', ['S', 'Z']],
  ['Z', []]
]);

function shortestUnweightedPath(graph, start, target) {
  if (!graph.has(start) || !graph.has(target)) return null;
  const parent = new Map([[start, null]]); // 同时是全局 visited 集合
  const queue = [start];

  for (let head = 0; head < queue.length; head++) {
    const vertex = queue[head];
    if (vertex === target) break;
    for (const next of graph.get(vertex) ?? []) {
      if (parent.has(next)) continue;
      parent.set(next, vertex); // 入队时标记，避免重复排队
      queue.push(next);
    }
  }

  if (!parent.has(target)) return null;
  const path = [];
  for (let vertex = target; vertex !== null; vertex = parent.get(vertex)) {
    path.push(vertex);
  }
  return path.reverse();
}

console.log(shortestUnweightedPath(routes, 'S', 'Z')); // ['S', 'A', 'T', 'Z']
console.log(shortestUnweightedPath(routes, 'S', 'missing')); // null
~~~

邻接表下 BFS 为 O(V + E) 时间、O(V) 额外空间，V 为顶点数、E 为边数。这里用数组递增 head 取代反复 shift，队列头前进时不搬移剩余元素。全局 visited 合适的理由是此处只保留每个顶点的一条最短距离与父节点；它并不表示顶点只能出现在一条合法简单路径中。

### 枚举简单路径：visited 只属于当前路径，并在回退时撤销

若要列出所有不重复经过同一站点的路线，S→A→T→Z 与 S→B→T→Z 都是有效候选。BFS 的 parent 只保留 T 的第一个父节点 A；若把全局 visited 直接拿来做路径枚举，T 经 A 加入 visited 后，经 B 到达 T 的分支会被误删。

backtracking（回溯）沿候选边选下一站，递归扩展；回到上一层时撤销刚才加入的站点和路径项。onPath 只表示“这个顶点正在当前候选路径上”。它会拒绝 T→S，因为 S 已在这条路径里；回到起点的另一条分支时，T 的标记已撤销，因此 T 可以再次进入另一条路线。

~~~javascript
function allSimplePaths(graph, start, target) {
  const results = [];
  if (!graph.has(start) || !graph.has(target)) return results;
  const path = [start];
  const onPath = new Set([start]);

  function visit(vertex) {
    if (vertex === target) {
      results.push(path.slice());
      return;
    }
    for (const next of graph.get(vertex) ?? []) {
      if (onPath.has(next)) continue; // 本路径内重复才构成环
      onPath.add(next);
      path.push(next);
      visit(next);
      path.pop();
      onPath.delete(next); // 回退后允许别的分支复用 next
    }
  }

  visit(start);
  return results;
}

const routeGraphForPaths = new Map([
  ['S', ['A', 'B']],
  ['A', ['T']],
  ['B', ['T']],
  ['T', ['S', 'Z']],
  ['Z', []]
]);
console.log(allSimplePaths(routeGraphForPaths, 'S', 'Z'));
// [['S', 'A', 'T', 'Z'], ['S', 'B', 'T', 'Z']]
~~~

如果本次问题只需一条路线，不应枚举所有路线。固定不同起终点的完全有向图，仅遍历其余所有顶点的简单路径就有 (V−2)! 条，数量至少可达阶乘级；本例代码没有候选数上限。令 C 为实际检查的候选边数、L 为复制到结果中的路径总长度，运行时间按 O(C + L) 计；即使结果少，搜索也可能访问许多最终无法到达目标的前缀。递归栈、path 与 onPath 的辅助空间为 O(V)，返回结果另占与所有输出路径总长度相称的空间。深图也可能超过 JavaScript 调用栈深度，此时应把递归状态改成显式栈，但仍须在回退时撤销 onPath。

### 依赖排序：每条有向边都必须满足先后顺序

topological sort（拓扑排序）不是在一般图上重新安排搜索次序。若每条边 u→v 表示 u 必须先于 v，拓扑序才是可执行顺序。把 T→S 解释为一项依赖时，S→A→T→S 已成环，要求 S 先于 T 又要求 T 先于 S，因此不存在合法顺序。若 T→S 只是回程路线、不是依赖，就从依赖图删去这条边；其余边形成 DAG（directed acyclic graph，有向无环图），可排成 S、A、B、T、Z。

下面的 Kahn 算法维护每个顶点尚未满足的入边数。入度为 0 表示当前可执行；取出它后，逐条解除后继的一项依赖。若取出的顶点数少于图中顶点数，剩余边属于环内或被环阻塞的依赖，返回 null。

~~~javascript
function topologicalOrder(graph) {
  const vertices = new Set(graph.keys());
  for (const neighbors of graph.values()) {
    for (const next of neighbors) vertices.add(next);
  }

  const indegree = new Map(Array.from(vertices, vertex => [vertex, 0]));
  for (const neighbors of graph.values()) {
    for (const next of neighbors) indegree.set(next, indegree.get(next) + 1);
  }

  const ready = Array.from(vertices).filter(vertex => indegree.get(vertex) === 0);
  const order = [];
  for (let head = 0; head < ready.length; head++) {
    const vertex = ready[head];
    order.push(vertex);
    for (const next of graph.get(vertex) ?? []) {
      const remaining = indegree.get(next) - 1;
      indegree.set(next, remaining);
      if (remaining === 0) ready.push(next);
    }
  }
  return order.length === vertices.size ? order : null;
}

const dependencies = new Map([
  ['S', ['A', 'B']],
  ['A', ['T']],
  ['B', ['T']],
  ['T', ['Z']],
  ['Z', []]
]);
const cyclicDependencies = new Map([
  ['S', ['A', 'B']],
  ['A', ['T']],
  ['B', ['T']],
  ['T', ['S', 'Z']],
  ['Z', []]
]);
console.log(topologicalOrder(dependencies)); // ['S', 'A', 'B', 'T', 'Z']
console.log(topologicalOrder(cyclicDependencies)); // null：T → S 使依赖成环
~~~

每个顶点和边各处理常数次，邻接表下时间 O(V + E)、额外空间 O(V)。入度为 0 的顶点可能不止一个，因此不同合法拓扑序都可能成立。初始 ready 队列按顶点首次出现顺序排列；后续变为 ready 的顶点则按当前出队顶点的邻接表扫描顺序入队，并由 FIFO 队列处理，不保证沿用它们在原 Map 中首次出现的顺序。若业务要求特定顺序，应明确再加优先级规则，而不能把任意拓扑序当成唯一答案。

### 非负权最短路：松弛距离，并跳过过期堆项

现在为路线加上整数耗时：S→A 为 1，S→B 为 4，A→T 为 6，B→T 为 1，T→S 为 2，T→Z 为 1。BFS 仍找到 3 条边的 S→A→T→Z，但总代价是 8；代价较小的 S→B→T→Z 为 6。边数最少和代价最低是两个问题。

Dijkstra 算法用最小堆优先处理当前距离最小且尚未定型的顶点。relaxation（松弛）一条边 v→w 时，若 dist[v]+weight 小于已知 dist[w]，就更新距离与前驱并把新距离推入堆。此实现不原地修改旧堆项；某顶点改善时会留下旧项，弹出时若其距离已不等于当前 dist，就跳过。堆还可含同一个顶点的多条距离记录，settled（已定型）集合保证顶点只处理一次。

| 弹出的堆项 | 更新 | 堆中待处理项（可能含过期项） | 说明 |
|---|---|---|---|
| S:0 | A=1，B=4 | A:1、B:4 | 从源点展开 |
| A:1 | T=7 | B:4、T:7 | 暂时走 A |
| B:4 | T 从 7 改为 5 | T:5、T:7 | 新项入堆，T:7 成为过期项 |
| T:5 | Z=6；回到 S 的候选 7 不改善 S=0 | Z:6、T:7 | 走 B 得到 Z 的最短代价 6 |
| Z:6 | 无 | T:7 | 目标已定型 |
| T:7 | 无 | 空 | 因 7 不等于 dist[T]=5，跳过 |

边权必须非负：定型当前最小距离顶点的证明依赖于之后经过边不会降低代价。若绕过下方代码的输入校验，另加 B→A、权重 −5，则 A 在距离 1 时已定型；处理 B:4 时，经过 B 到 A 的真实代价为 −1，定型规则会忽略它并错误保留 1。本文实现会在运行核心循环前对负权输入抛出 RangeError；该反例用来说明为什么它拒绝这种输入。负权图应改用能处理负边的算法（例如无负环前提下的 Bellman–Ford），不能因为某个负权样例恰好算对就使用 Dijkstra。

下面的最小堆仅按 distance 排序；它只服务此完整示例，与[优先队列的上浮和下沉](#43.%20%E6%80%8E%E6%A0%B7%E5%9C%A8%E4%B8%8D%E6%96%AD%E5%8A%A0%E5%85%A5%E4%BB%BB%E5%8A%A1%E6%97%B6%E6%8C%81%E7%BB%AD%E5%8F%96%E5%87%BA%E6%9C%80%E9%AB%98%E4%BC%98%E5%85%88%E7%BA%A7%EF%BC%9F)共享数组堆机制。代码把权重和距离限制为安全整数，并拒绝负权或超出安全范围的路径和。

> [!example]- 可运行：Dijkstra 最小堆实现
> ~~~javascript
> class MinHeap {
>   constructor() { this.items = []; }
>   get size() { return this.items.length; }
>
>   push(item) {
>     this.items.push(item);
>     let i = this.items.length - 1;
>     while (i > 0) {
>       const parent = Math.floor((i - 1) / 2);
>       if (this.items[parent].distance <= this.items[i].distance) break;
>       [this.items[i], this.items[parent]] = [this.items[parent], this.items[i]];
>       i = parent;
>     }
>   }
>
>   pop() {
>     if (this.items.length === 0) return null;
>     const root = this.items[0];
>     const last = this.items.pop();
>     if (this.items.length > 0) {
>       this.items[0] = last;
>       let i = 0;
>       while (true) {
>         const left = 2 * i + 1;
>         const right = left + 1;
>         let smallest = i;
>         if (left < this.items.length &&
>             this.items[left].distance < this.items[smallest].distance) smallest = left;
>         if (right < this.items.length &&
>             this.items[right].distance < this.items[smallest].distance) smallest = right;
>         if (smallest === i) break;
>         [this.items[i], this.items[smallest]] = [this.items[smallest], this.items[i]];
>         i = smallest;
>       }
>     }
>     return root;
>   }
> }
>
> function dijkstra(graph, source) {
>   for (const [from, edges] of graph) {
>     for (const edge of edges) {
>       if (!Number.isSafeInteger(edge.weight) || edge.weight < 0) {
>         throw new RangeError('Dijkstra requires non-negative safe-integer weights');
>       }
>       if (!graph.has(edge.to)) throw new RangeError('every destination must be a graph vertex');
>     }
>   }
>   if (!graph.has(source)) return { distances: new Map(), previous: new Map() };
>
>   const distances = new Map(Array.from(graph.keys(), vertex => [vertex, Infinity]));
>   const previous = new Map();
>   const settled = new Set();
>   const heap = new MinHeap();
>   distances.set(source, 0);
>   heap.push({ vertex: source, distance: 0 });
>
>   while (heap.size > 0) {
>     const current = heap.pop();
>     const vertex = current.vertex;
>     if (current.distance !== distances.get(vertex) || settled.has(vertex)) continue;
>     settled.add(vertex);
>
>     for (const edge of graph.get(vertex)) {
>       if (settled.has(edge.to)) continue;
>       const candidate = current.distance + edge.weight;
>       if (!Number.isSafeInteger(candidate)) throw new RangeError('path distance exceeds the safe integer range');
>       if (candidate < distances.get(edge.to)) {
>         distances.set(edge.to, candidate);
>         previous.set(edge.to, vertex);
>         heap.push({ vertex: edge.to, distance: candidate });
>       }
>     }
>   }
>   return { distances, previous };
> }
>
> function weightedPath(result, source, target) {
>   if (!result.distances.has(target) || result.distances.get(target) === Infinity) return null;
>   const path = [];
>   let vertex = target;
>   while (vertex !== source) {
>     path.push(vertex);
>     if (!result.previous.has(vertex)) return null;
>     vertex = result.previous.get(vertex);
>   }
>   path.push(source);
>   return path.reverse();
> }
>
> const weightedRoutes = new Map([
>   ['S', [{ to: 'A', weight: 1 }, { to: 'B', weight: 4 }]],
>   ['A', [{ to: 'T', weight: 6 }]],
>   ['B', [{ to: 'T', weight: 1 }]],
>   ['T', [{ to: 'S', weight: 2 }, { to: 'Z', weight: 1 }]],
>   ['Z', []]
> ]);
> const result = dijkstra(weightedRoutes, 'S');
> console.log(result.distances.get('Z'));                    // 6
> console.log(weightedPath(result, 'S', 'Z'));                // ['S', 'B', 'T', 'Z']
> console.log(weightedPath(result, 'S', 'unreachable'));      // null
> ~~~

该惰性堆实现每条边至多扫描一次，至多成功松弛并压入一条新项，故时间 O(V + (E + 1) log(E + 1))、空间 O(V + E)。若用带 decrease-key 的索引优先队列，通常可把堆空间降到 O(V)，时间写作 O((V + E) log V)。无论用哪一种实现，距离表、前驱表、堆项和 visited/settled 状态都要对应同一个图与同一组边权。

> [!info]- 来源
> - 邻接表遍历、BFS 按边数找最短路、首次发现时记录父边：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §4.1 “Undirected Graphs”](https://algs4.cs.princeton.edu/41graph/)，作者实现 [BreadthFirstPaths.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/BreadthFirstPaths.java.html)。BFS 原理同样适用于本页的有向邻接表。
> - DAG 才有拓扑序，以及顶点/边线性量级的 DFS 版本：[Algorithms, 4th ed., §4.2 “Directed Graphs”](https://algs4.cs.princeton.edu/42digraph/)，作者的队列版本 [TopologicalX.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/TopologicalX.java.html)。本页采用 Kahn 入度实现，示例输出由 Node.js 运行复算。
> - Dijkstra 的非负权前提、松弛、堆优先处理和索引优先队列复杂度：[Algorithms, 4th ed., §4.4 “Shortest Paths”](https://algs4.cs.princeton.edu/44sp/)，作者实现 [DijkstraSP.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/DijkstraSP.java.html)。本页为便于展示过期项，使用惰性重复入堆，复杂度另按本实现计。
## 45. 动态规划如何定义状态并安排更新顺序？

报表汇总里某些查询可能复用之前算过的子结果，但本篇用三个更小、可完整复算的例子说明一般机制。dynamic programming（动态规划，DP）把问题拆为有限状态；每个状态只保留后续转移需要的信息。先写递推关系和初始状态，再按依赖顺序计算，复用一维数组时还要追踪每个格子属于哪一轮。

### 状态如何消除重复计算？

若多个递归分支会请求同一个子问题，记忆化将结果保存后复用；自底向上迭代则按依赖次序计算状态。以 Fibonacci 数列为例：F(0)=0、F(1)=1、F(n)=F(n-1)+F(n-2)。朴素递归每层分叉，O(2ⁿ) 是一个时间上界，调用栈 O(n)；迭代每个 n 只更新一次，时间 O(n)、辅助空间 O(1)。

~~~javascript
function fibRecursive(n) {
  if (!Number.isSafeInteger(n) || n < 0) throw new RangeError('n must be a non-negative safe integer');
  if (n <= 1) return n;
  return fibRecursive(n - 1) + fibRecursive(n - 2);
}

function fib(n) {
  if (!Number.isSafeInteger(n) || n < 0) throw new RangeError('n must be a non-negative safe integer');
  if (n <= 1) return n;
  let previous = 0;
  let current = 1;
  for (let i = 2; i <= n; i++) {
    [previous, current] = [current, previous + current];
  }
  return current;
}
~~~

JavaScript Number 的整数运算只有在每个中间结果都落在安全整数范围内时才保证精确。F(78)=8,944,394,323,791,464 仍可精确表示；F(79)=14,472,334,024,676,221 已超过 2⁵³−1。相同限制也作用于楼梯方案计数，例如 climbStairs(78,[1,2]) 计算 F(79)；背包有限值相加也可能越界，甚至把两个有限 Number.MAX_VALUE 加成 Infinity。若要求大整数精确，用 BigInt 并调整初始值、返回类型和调用方；若背包值含小数，Number 结果本来就是二进制浮点近似。按精确整数契约时，输入值应为安全整数且所有候选和不超过 Number.MAX_SAFE_INTEGER。

### 计数问题的状态和循环顺序是什么？

爬楼梯示例定义 ways[total] 为按顺序选择合法步长、总和恰为 total 的方案数。ways[0]=1 表示空序列；每个合法正整数步长 step 贡献 ways[total-step]。输入要求步长为互异正整数，否则重复步长会重复计算同一选择。下面按目标总和再按步长转移。

~~~javascript
function climbStairs(n, steps) {
  if (!Number.isSafeInteger(n) || n < 0) throw new RangeError('n must be a non-negative safe integer');
  if (!Array.isArray(steps)) throw new TypeError('steps must be an array');
  for (let i = 0; i < steps.length; i++) {
    if (!Number.isSafeInteger(steps[i]) || steps[i] <= 0) {
      throw new TypeError('steps must contain positive safe integers without holes');
    }
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

steps=[1,2]、n=3 的计算是：ways[0]=1；ways[1]=ways[0]=1；ways[2]=ways[1]+ways[0]=2；ways[3]=ways[2]+ways[1]=3，对应 1+1+1、1+2、2+1。顺序有意义，1+2 与 2+1 是不同方案。空步长数组也有效：n=0 返回空序列方案 1，n>0 返回 0；`[1,,2]` 会在按下标校验时拒绝，避免 `some` 跳过数组洞。若 n 个台阶、k 种步长，含初始化和空边界的时间为 O((n+1)(k+1))，空间 O(n+1)。数组长度仍须能在当前运行时分配。

### 0/1 背包为何要从大容量向小容量更新？

定义 best[c] 为已处理物品中、总重量不超过 c 时可取得的最大价值。处理重量 w、价值 v 的物品时，转移为 max(best[c], best[c-w]+v)。每件物品只能用一次，所以 c 必须从 W 向 w 递减；若从小到大，best[c-w] 可能已包含当前物品，造成重复使用。

~~~javascript
function knapsack(capacity, weights, values) {
  if (!Number.isSafeInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative safe integer');
  if (!Array.isArray(weights) || !Array.isArray(values) || weights.length !== values.length) {
    throw new TypeError('weights and values must be arrays of equal length');
  }
  for (let i = 0; i < weights.length; i++) {
    if (!Number.isSafeInteger(weights[i]) || weights[i] < 0) {
      throw new RangeError('weights must contain non-negative safe integers without holes');
    }
    if (!Number.isFinite(values[i])) throw new TypeError('values must contain finite numbers without holes');
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

假设容量 W=4，有两件物品 (重量,价值)=(2,3)、(3,4)。初始 best=[0,0,0,0,0]。处理第一件后得到 [0,0,3,3,3]；第二件从容量 4 向下更新，得到 [0,0,3,4,4]，最优价值 4，可留下未用容量。若第一件按容量从小到大更新，best[2]=3 后又会用该值算出 best[4]=6，相当于把同一件物品用两次。

0/1 背包对 n 件、整数容量 W 的时间为 O((n+1)(W+1))，空间 O(W+1)，覆盖 n=0 或 W=0；这是伪多项式复杂度，因为 W 的数值可比其输入编码位数大得多。W=0 时仍会处理每件零重量物品一次；倒序循环在容量 0 也只更新一次，所以正价值零重量物品可各取一次。代码以零初始化，表示允许不装满且不要求最低价值；若要恰好装满，除 best[0]=0 外其余状态应初始化为不可达哨兵，并在转移时跳过不可达状态。若物品允许无限次且重量为正，才可从小容量向大容量更新；若零重量物品有正价值且可无限选，最优值没有有限上界。容量数组也必须能在当前运行时分配。

> [!info]- 来源
> - 动态规划状态、递推与更新顺序按三段代码的输入/输出和中间数组手工复算；Number 安全整数边界按 ECMAScript Number.MAX_SAFE_INTEGER=2⁵³−1 核对：[ECMAScript 2026 numbers](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)。
## 46. 分区如何改变快速排序的时间和空间代价？

报表 42 的页面可能要按数值指标排序。quicksort（快速排序）先选 pivot（基准值）再分区，分区大小决定递归树的高度；连续偏斜时，即使每层都正确排序，也会反复处理接近原规模的子数组。选择分区方式时还要看算法是否修改输入、是否复制数据以及递归深度。

### 三路分区怎样处理小于、等于和大于基准的值？

下面是易检查的数组构造版：每轮把值放入 lower、equal、higher 三个新数组，递归只处理两侧。例子以数组中间位置的值为所选 pivot；这不保证它是中位数。输入应是同一可比较域中的有限数字，否则 NaN 或混合类型会破坏比较的分区含义。

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

以 [5,2,4,1,3] 为例，pivot=4：

| 阶段 | 中间结果 |
|---|---|
| 分区 | lower=[2,1,3]，equal=[4]，higher=[5] |
| 递归 | quickSort(lower)=[1,2,3]，quickSort(higher)=[5] |
| 拼接返回 | [1,2,3]+[4]+[5]=[1,2,3,4,5] |

所有与 pivot 相等的值一次归入 equal，不再递归；因此大量相同值时三路分区可减少后续工作。

### 为什么分区平衡决定递归深度？

每次分区本身扫描 n 个值，成本 Θ(n)。若每次约分成两半，递推式 T(n)=2T(n/2)+Θ(n)：每层合计处理约 n 项，约有 log₂n 层，所以总时间 Θ(n log n)、递归深度 O(log n)。若一侧为空、另一侧含 n−1 项，递推式 T(n)=T(n−1)+Θ(n)，各层工作是 n+(n−1)+…+1=n(n+1)/2，因此总时间 Θ(n²)、栈深 O(n)。取数组中间下标作为 pivot 并不保证分区平衡。例如 [7,5,3,1,2,4,6] 的中点值先是 1；递归较大侧后，下一个中点又是 2，再接着是 3，连续成为当前最小值，产生这种偏斜切分。

这段数组构造实现不是原地排序。每个递归调用为 lower、equal、higher 分配新数组，随后还分配拼接结果；不能只把递归栈当作空间成本。若切分平衡，每层处理的元素总量为 O(n)，累计数组分配为 O(n log n)，沿一条递归路径同时保留的分区规模按 n+n/2+n/4+… 增长为 O(n)；若反复偏斜，递归栈深 O(n)，沿栈仍可引用长度约为 n、n−1、n−2… 的分区数组，累计分配及保留数组总量可达 O(n²)。这里的累计分配不是峰值存活内存；实际回收时机由运行时决定。若目标是生产排序，通常优先用内置排序并明确比较器。

### 内置排序何时修改数组，何时保留副本？

~~~javascript
const values = [80, 9, 12];
const sortedInPlace = values.sort((a, b) => a - b);

const copyInput = [80, 9, 12];
const sortedCopy = copyInput.toSorted((a, b) => a - b);
~~~

sort 会把 values 原地改为 [9,12,80]；toSorted 则让 copyInput 保持 [80,9,12] 并返回一个新数组，要求运行环境支持该方法。长度为 n 的返回副本至少要写出 n 个元素；排序本身的工作和副本存储要分开算。省略比较器时，元素按字符串比较，例如 80 会排在 9 之前。数值排序要显式给出比较器。ECMAScript 2019 及之后要求排序稳定：比较器判定相等的元素保留原相对顺序；具体采用何种排序算法是引擎实现细节。

> [!example] 数值排序比较器
> [80, 9, 12].sort() 会按字符串顺序得到 [12, 80, 9]；使用 (a,b)=>a-b 才按数值递增得到 [9, 12, 80]。若排序对象数组，比较器返回 0 的对象在稳定排序后保持输入中的相对次序。

> [!info]- 来源
> - 内置排序稳定性、比较器和原地 sort 语义：[ECMAScript 2026 indexed collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)，ECMAScript 2026。
> - 返回副本的 toSorted 语义：[ECMAScript 2026 indexed collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.tosorted)，ECMAScript 2026；Node.js v26.11.1 本地复算示例。
## 47. 文本算法应按码元、码点还是字素簇处理？

报表 42 的事件描述可能含 emoji、组合重音或其他扩展文字。JavaScript 字符串索引、Unicode 码点和用户看到的字符不是同一种单位：先定义任务要计数、比较或切分什么，再实现算法。这里第一次说明三个单位：UTF-16 code unit（UTF-16 编码单元）、Unicode code point（Unicode 码点）和 extended grapheme cluster（扩展字素簇）。

### 三种长度会怎样不同？

JavaScript String.length 返回 UTF-16 编码单元数。Array.from 对字符串迭代时把有效代理对组合成一个码点，孤立代理仍单独保留，但组合附加符仍是另一个码点。Intl.Segmenter 的 grapheme 模式按 locale（语言环境）与实现提供的分段规则给出字素簇；这通常接近用户感知字符，但规则可定制，不能把某个 Node 运行时的结果等同于当前 UAX #29 版本的每条边界规则。

~~~javascript
const sample = 'A😀e\u0301';
const codeUnits = sample.length;
const codePoints = Array.from(sample);
const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
const graphemes = Array.from(segmenter.segment(sample), part => part.segment);

console.log(codeUnits);              // 5
console.log(codePoints.length);      // 4
console.log(graphemes);              // ['A', '😀', 'é']
console.log(graphemes.length);       // 3
~~~

这里 A 占 1 个码元和 1 个码点；😀 是代理对，占 2 个码元、1 个码点；e 加 U+0301 组合重音占 2 个码元、2 个码点，却通常成为 1 个字素簇。字符计数不能代替存储大小：若限制请求字节数，还要另外按明确编码计算字节。

Array.from 不会自动把规范等价的不同码点序列变成相同序列。例如预组字符 é 与 e 加组合重音肉眼可相同，但码点逐个比较不同：'é' === 'e\u0301' 为 false，而 NFC 归一化后两者相等。若业务要求规范等价比较，可在明确边界使用 normalize('NFC')；保留原始输入时不要无意改写其码点序列。

### 回文和连续重复要比较什么单位？

原示例的回文函数按码点逆向比较，所以它把代理对当作单个元素，但不会把规范等价序列归一化；若要按用户可见单元比较，先用 Segmenter 切成字素簇。相同函数逻辑可接受不同切分结果：

~~~javascript
function isPalindromeByCodePoint(value) {
  const units = Array.from(value);
  for (let left = 0, right = units.length - 1; left < right; left++, right--) {
    if (units[left] !== units[right]) return false;
  }
  return true;
}

function splitGraphemes(value, locale = 'en') {
  const segmenter = new Intl.Segmenter(locale, { granularity: 'grapheme' });
  return Array.from(segmenter.segment(value), part => part.segment);
}

function isPalindromeByGrapheme(value) {
  const units = splitGraphemes(value);
  for (let left = 0, right = units.length - 1; left < right; left++, right--) {
    if (units[left] !== units[right]) return false;
  }
  return true;
}
~~~

这两个函数都用精确字符串相等比较；若文字规范化属于需求，应先明确是否按 NFC 归一化。UAX #29 的默认扩展字素簇是可复现的分段规则，但语言或应用可进行 tailor（定制），也不是编码字节长度。

最长连续重复示例按码点统计完全相同的连续项，并在并列时返回第一个最长段；空字符串返回空字符、长度 0。对 Array.from('😀😀A')，结果是字符 😀、长度 2，而按 UTF-16 下标遍历会把每个 emoji 拆成两个码元。

以 `AABB` 走查循环：第 2 个 A 使当前段长到 2；读到第一个 B 时先结算 A，best 变成 A/2；第 2 个 B 使当前段长到 2；循环最后一次以 i===length 结算 B。因更新条件是 `currentLength > bestLength` 而非大于等于，并列保留先出现的 A，尾段也不会漏掉。

~~~javascript
function longestConsecutive(value) {
  const characters = Array.from(value);
  if (characters.length === 0) return { char: '', len: 0 };

  let bestChar = characters[0];
  let bestLength = 1;
  let currentLength = 1;
  for (let i = 1; i <= characters.length; i++) {
    if (i < characters.length && characters[i] === characters[i - 1]) currentLength++;
    else {
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

### 数字显示和大小写转换如何明确边界？

展示数值通常使用 Intl.NumberFormat，并显式指定 locale，避免依赖用户机器默认区域。格式化规则仍可能受运行时国际化数据版本影响；若输出用于协议或稳定快照，不应把本地化显示当作机器可解析格式。手写版本仅接受可选负号和 ASCII 十进制数字组成的整数字符串，不接受小数、空格或本地化数字。

~~~javascript
function formatNumber(value, locale = 'en-US') {
  return new Intl.NumberFormat(locale).format(value);
}

function formatIntegerThousands(text) {
  if (typeof text !== 'string' || text.trim() !== text || !/^-?\d+$/.test(text)) {
    throw new TypeError('expected an integer string');
  }
  const sign = text.startsWith('-') ? '-' : '';
  const digits = sign ? text.slice(1) : text;
  return sign + digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
~~~

这个正则适合本例限定的 ASCII 整数字符串；普通回溯引擎可能在多个位置的前瞻中重复检查后缀，因此不对任意实现或输入规模声称线性时间。若要明确的单趟线性处理，可从右向左每三位分组再拼接；展示数字则优先使用 `Intl.NumberFormat`。

大小写切换示例只变换 ASCII A–Z 与 a–z，其他码点保持不变。它不是适用于所有语言的大小写转换：Unicode 大小写映射可能依赖 locale，且转换前后长度也未必相同。

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

### Trie 怎样共享前缀并限制候选输出？

在合成报表 42 的描述搜索中，输入框要查找以已输入前缀开头的标签。Trie（前缀树）把键拆成一串单位，让有相同前缀的键沿着同一条路径前进；本例沿用本章的码点单位，按 Unicode 码点建边。Array.from 会把有效代理对组合成一个码点，所以 😀 是一条边；组合重音若未归一化，则仍是另一条码点边，不等同于视觉上的一个字素簇。

匹配合约选择 NFC（Normalization Form C，规范化形式 C）：写入键和查询前缀都先规范化，把规范等价的码点序列映射到同一路径。因而预组字符 café 与 cafe 加 U+0301 的查询相同；键以规范化后的形式枚举。NFC 不是去重音或兼容字符折叠：单独输入 cafe 不匹配规范化后的 café，若产品要不区分重音或处理兼容字符，必须另外定义匹配规则。保存原输入展示时，可在 terminal 的 value 中保留显示文本。

| 插入键 | NFC 后的码点路径 | terminal 标记 |
|---|---|---|
| re | r → e | e 节点是完整键 |
| report | 与 re 共享 r → e，再接 p → o → r → t | t 节点是完整键 |
| reporter | 继续共享 report，再接 e → r | 最后一个 r 是完整键 |
| review | 与 re 共享 r → e，再从 v 分支 | 最后一个 w 是完整键 |
| 😀report | 😀 → r → e → p → o → r → t | t 节点是完整键 |
| 先 café，后 cafe 加 U+0301 | 两次写入经 NFC 后都走 café 的同一条路径 | 第二次写入覆盖第一次的 value |

每个节点有一张从码点到子节点的 Map 和一个 terminal（键结束）标记。只有 terminal 为 true 才表示完整键；“存在这段前缀”不等于“前缀本身也是键”。因此 re 可以既是完整键，也有通向 report 和 review 的后续分支。共享路径存一次，但每个前缀节点及子边 Map 都占内存。

下面实现插入、精确查询和有限前缀枚举。枚举从前缀节点开始做 depth-first search（DFS，深度优先搜索）；terminal 先于后代输出，因此前缀本身若也是键会先出现。子边按 Map 的插入顺序访问，所以结果不承诺字典序；limit 限制返回候选数，显式栈按需取一个子边，不会为了遍历先复制整张子边表。

> [!example]- 可运行：码点 Trie
> ~~~javascript
> class TrieNode {
>   constructor() {
>     this.children = new Map();
>     this.terminal = false;
>     this.value = undefined;
>   }
> }
>
> class CodePointTrie {
>   constructor() {
>     this.root = new TrieNode();
>   }
>
>   normalizeKey(key) {
>     if (typeof key !== 'string') throw new TypeError('key must be a string');
>     return key.normalize('NFC');
>   }
>
>   nodeFor(key) {
>     let node = this.root;
>     for (const codePoint of Array.from(this.normalizeKey(key))) {
>       node = node.children.get(codePoint);
>       if (!node) return null;
>     }
>     return node;
>   }
>
>   insert(key, value) {
>     const normalized = this.normalizeKey(key);
>     let node = this.root;
>     for (const codePoint of Array.from(normalized)) {
>       if (!node.children.has(codePoint)) node.children.set(codePoint, new TrieNode());
>       node = node.children.get(codePoint);
>     }
>     node.terminal = true;
>     node.value = value;
>   }
>
>   has(key) {
>     const node = this.nodeFor(key);
>     return node !== null && node.terminal;
>   }
>
>   lookup(key) {
>     const node = this.nodeFor(key);
>     return node !== null && node.terminal
>       ? { found: true, value: node.value }
>       : { found: false };
>   }
>
>   keysWithPrefix(prefix, limit = 20) {
>     if (!Number.isSafeInteger(limit) || limit < 0) {
>       throw new RangeError('limit must be a non-negative safe integer');
>     }
>     const normalizedPrefix = this.normalizeKey(prefix);
>     const start = this.nodeFor(normalizedPrefix);
>     if (start === null || limit === 0) return [];
>
>     const results = [];
>     const path = [];
>     const stack = [{ node: start, entered: false, children: null }];
>     while (stack.length > 0 && results.length < limit) {
>       const frame = stack[stack.length - 1];
>       if (!frame.entered) {
>         frame.entered = true;
>         if (frame.node.terminal) {
>           results.push(normalizedPrefix + path.join(''));
>           if (results.length === limit) break;
>         }
>         frame.children = frame.node.children.entries();
>       }
>
>       const next = frame.children.next();
>       if (next.done) {
>         stack.pop();
>         if (stack.length > 0) path.pop();
>       } else {
>         const [codePoint, child] = next.value;
>         path.push(codePoint);
>         stack.push({ node: child, entered: false, children: null });
>       }
>     }
>     return results;
>   }
> }
>
> const trie = new CodePointTrie();
> trie.insert('re', 'prefix is also a complete key');
> trie.insert('report', 'report label');
> trie.insert('reporter', 'reporter label');
> trie.insert('review', 'review label');
> trie.insert('café', 'precomposed spelling');
> trie.insert('cafe\u0301', 'decomposed spelling replaces the same normalized key');
> trie.insert('😀report', 'emoji-prefixed key');
>
> console.log(trie.has('café'));                  // true
> console.log(trie.lookup('cafe\u0301'));         // { found: true, value: 'decomposed spelling replaces the same normalized key' }
> console.log(trie.keysWithPrefix('re', 3));      // ['re', 'report', 'reporter']
> console.log(trie.keysWithPrefix('rep', 10));    // ['report', 'reporter']
> console.log(trie.keysWithPrefix('unknown', 5)); // []
> console.log(trie.keysWithPrefix('', 2));        // first two keys in trie traversal order
> ~~~

若键有 m 个码点，在 Map 子边查找按平均常数时间估算时，插入和精确查询需 O(m) 时间；更严谨地说，时间是沿 m 条边执行的 Map 操作总成本。令 p 为输入前缀长度；按常见的线性 Unicode 规范化实现估算，前缀规范化、Array.from 转成码点数组和定位节点共需 O(p) 时间，规范化结果字符串与临时码点数组合计 O(p) 空间。设 DFS 实际访问 S 个节点，d 是访问路径的最大深度，L 是返回键的码点总数，r 是实际返回项数：遍历和构造结果的时间按 O(p + S + L) 估算；显式栈帧和码点路径数组各占 O(d) 空间，返回的字符串另占 O(L)，结果数组含 O(r) 个引用。因此不计 Trie 本身的总额外空间为 O(p + d + L + r)。limit 只限制返回条数，不保证访问节点数或字符总数也为 O(limit)。若需要按语言区域排序的建议项，必须另外定义排序规则；本实现的 Map 插入顺序不等于语言排序。哈希表适合完整键的精确查找，不能直接定位整组前缀候选；排序列表可以先二分找到同前缀键的起点再顺序输出；Trie 用更多节点和 Map 结构换取沿前缀直接定位。只有前缀查询足够常见时，这种空间取舍才值得。

> [!info]- 来源
> - JavaScript 字符串的 UTF-16 表示及字符串迭代按码点处理：[ECMAScript 2026 text processing](https://tc39.es/ecma262/2026/multipage/text-processing.html)，String value 与 StringIterator。
> - JavaScript NFC 规范化 API：[ECMAScript 2026, §22.1.3.15 String.prototype.normalize](https://tc39.es/ecma262/2026/multipage/text-processing.html#sec-string.prototype.normalize)；该方法按最新 Unicode Standard 的规范化形式处理输入。
> - 构造器入口：[ECMA-402 2026 §8.2.7 `Intl.NumberFormat`](https://tc39.es/ecma402/2026/#sec-intl.numberformat)、[§8.2.10 `Intl.Segmenter`](https://tc39.es/ecma402/2026/#sec-intl.segmenter)；格式化机制见 [§16 NumberFormat Objects](https://tc39.es/ecma402/2026/#numberformat-objects)，分段机制见 [§19 Segmenter Objects](https://tc39.es/ecma402/2026/#segmenter-objects)。Node.js v26.11.1 只用于复算本例行为，不据此断言运行时采用 UAX #29 rev.49。
> - 字素簇默认边界与适用限制：[Unicode Standard Annex #29, Unicode 18.0.0, Revision 49](https://www.unicode.org/reports/tr29/tr29-49.html)，2026-09-01；以 extended grapheme cluster 作默认分段，允许声明定制。
> - 数字安全整数上限：[ECMAScript 2026 Number.MAX_SAFE_INTEGER](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)，2⁵³−1。
> - Trie 的前缀路径、完整键终端标记和前缀枚举：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §5.2 “Tries”](https://algs4.cs.princeton.edu/52trie/)，作者实现 [TrieST.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/TrieST.java.html) 使用 256 路扩展 ASCII；本页使用 Map 子边与码点，避免把该 ASCII 实现误当成通用 Unicode 代码。
> - 规范等价与 NFC 规范化形式：[Unicode Standard Annex #15, Unicode 18.0.0, Revision 58, §1.1 “Canonical and Compatibility Equivalence” 与 §1.2 “Normalization Forms”](https://www.unicode.org/reports/tr15/tr15-58.html)，2026-08-12。NFC 选择及其对前缀语义的影响按本节契约说明。
> - 子边迭代顺序：[ECMAScript 2026, Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)，Map iterator 按插入顺序产生条目。
## 48. 为什么连续扫描往往比链表遍历快？

假设一段代码要累计一组事件的时长。它可以把事件放在连续数组里，也可以让每个节点保存一个指向下一节点的指针。两种表示都要访问 n 项，工作量都是 O(n)；差别在于处理器何时能知道下一次读取的地址，以及这次读取会带来哪些相邻数据。本例解释访问机制，不代表实测速度。

~~~mermaid
flowchart TD
    A["数组：已知基址与下标 i"] --> B["计算第 i 项地址"]
    B --> C["下一项地址也可独立计算"]
    C --> D["规则访问可能被预取，多次读取可重叠"]
    E["链表：读取当前节点"] --> F["从当前节点读取 next"]
    F --> G["next 到达后才知道下个节点地址"]
    G --> H{"依赖读取未命中缓存？"}
    H -->|是，且没有独立工作| I["关键路径等待数据"]
    H -->|是，但有独立工作| J["处理器可先执行其他工作"]
    H -->|否| K["下一节点很快可用"]
~~~

图中的比较只针对一条遍历路径。处理器可能继续执行无关指令或其他独立读取；一次缓存未命中不会冻结整个 CPU。

### 延迟与带宽限制的是不同事情

central processing unit（CPU，中央处理器）访问数据时可能从寄存器、不同层级的 cache（缓存）或 DRAM（动态随机存取存储器）取得数据。实际层数、容量、带宽和延迟都取决于处理器与系统配置；程序不能假设固定层级或固定耗时。

latency（延迟）表示一次请求从发出到数据可用所需的时间。bandwidth（带宽）表示一段时间内能够传送多少数据。若流式循环每项平均传输 s 字节、可用带宽为 B，且循环已经受带宽限制，那么吞吐上限约为 B/s 项每秒。这个估算不包含计算时间，也不能预测一次依赖读取的等待时间。

cache line（缓存行）是缓存与一致性协议常用的数据传输粒度，具体大小依处理器而异。读取一个地址时，缓存填充通常会带入邻近字节；随后访问相邻元素可能已经命中缓存。这是 spatial locality（空间局部性）。短时间重复使用同一数据更可能仍在缓存中，则是 temporal locality（时间局部性）。这些是访问机会，不是每次都命中的保证。

Wulf 与 McKee 将处理器计算能力与内存供数能力逐渐扩大的差距称为 memory wall（内存墙）。当处理器等待数据或数据带宽饱和时，增加算术指令吞吐未必能提高整体速度；但计算密集、数据已在缓存或请求彼此独立的程序不一定受内存墙限制。

### 连续地址让后续读取容易提前安排

在 C 里，数组第 i 项的地址写作 `&events[i]`。若改用字节地址表示，才是字节基址加上 i 乘以元素字节数；不能把 C 的 struct 指针加法再乘一次 `sizeof`。读完当前项之前，下一项地址已经确定。对顺序访问，许多硬件预取器能识别访问模式；在数据依赖允许时，处理器还可让若干次独立读取同时在途。memory-level parallelism（MLP，内存级并行度）就是能同时等待的独立内存请求数量。

~~~c
for (size_t i = 0; i < count; i++) {
    total += events[i].duration;
}
~~~

这里的地址规律只说明 CPU 有机会提前取后续项。编译器是否向量化（SIMD，单指令多数据）、读取能重叠多少，还取决于数据依赖、别名关系、循环计算和目标处理器。`total` 的累加本身也有依赖，因此不能只凭代码外形承诺某种吞吐量。

### 链表遍历必须先取到下一个指针

链表循环每轮都要先读取当前节点，再从它读取 `next`。只有 `next` 到达后，CPU 才知道下一项的位置。这种 pointer chasing（指针追逐）形成地址依赖链，限制单条遍历能并行发出的独立请求数量。

~~~c
for (struct event_node *node = head;
     node != NULL;
     node = node->next) {
    total += node->event.duration;
}
~~~

如果 `next` 已在缓存里，遍历可能很快；如果节点分散在内存中，前一节点的读取会把下一次读取推迟。支持乱序执行的处理器仍可执行这条链以外的独立工作，其他线程或另一条独立链也可能产生在途请求。若缺失数据位于关键依赖路径、又没有有用工作可继续，相关指令才会停下来等它。顺序流式预取器通常比对数组更难预测普通指针链；特定处理器或软件预取可改善某些模式，但需要测量确认。

### 渐进复杂度没有包含布局、移动与分配

两种遍历的算法复杂度都可为 O(n)，但这不代表耗时相同。差别不是“链表常数时间、数组线性时间”这么简单：

- 数组按下标访问通常为 O(1)；中间插入或删除要移动后续项，工作量为 O(n)，但移动范围连续，运行库或 CPU 可使用优化过的批量操作。
- 链表按值查找通常为 O(n)。只有已经持有目标节点和所需链接时，插入或删除才需有限次指针更新、可视为 O(1)；若先扫描定位，整个操作仍为 O(n)。
- 分配节点、缓存未命中、节点大小、锁竞争和访问顺序都可能改变实际成本。对象池能改变分配成本，却不保证链表顺序就是地址顺序。

因此，主要工作是按顺序扫描时，连续数组常是更好的起点；若系统频繁改动已知节点、要求节点地址稳定，或同一对象要参加多个关系，链表可能更合适。先按操作和所有权选择，再测量代表性数据规模与访问模式。Linux 内核文档也提醒，能满足需求的简单数组通常比链表更有局部性。

### “数组”在语言中不总是同一种布局保证

C 普通数组的元素连续，多维数组按行优先排列。C++ `std::vector<T>` 对 `T` 非 `bool` 保证连续容器语义；`vector<bool>` 是专门化，不属于这项保证。C++ `std::list<T>` 的标准规定操作与复杂度，不规定具体节点布局。

ECMAScript 规定 JavaScript `Array` 的索引属性、长度和操作行为，不承诺像 C 数组那样连续存储。引擎可对常见数组作优化；以 V8 为例，元素类型可有 packed（紧凑）与 holey（稀疏）等内部种类，这是 V8 的实现选择。`TypedArray` 提供固定数值元素类型，视图关联到 `ArrayBuffer` 的字节范围；也不能据此从 JavaScript 推断物理地址、缓存行或跨实现布局。

### 其他数据结构也会受访问模式影响

| 对比 | 何时可能改变选择 |
|---|---|
| 小范围线性搜索与二分搜索 | 二分比较次数更少，但会跳到不同位置；小数组是否更快取决于规模、比较成本和缓存状态。 |
| 行遍历与列遍历 | 行优先布局中，按最后一维顺序扫描较连续；跨距读取会改变缓存利用率。 |
| 伪共享与写入争用 | 多个 CPU 访问同一缓存行，且至少有一方写入时，彼此独立的字段也可能触发缓存一致性流量；纯并发读取不构成伪共享。Linux 的 `perf c2c` 可用于定位受争用的缓存行，再结合结构布局工具检查对应字段。 |
| B+ 树与红黑树 | 页式 B+ 树将多个键放在节点页内并支持叶层范围扫描；内存中的指针式红黑树逐节点查找。主导成本可能是存储页、缓存未命中或更新。 |
| 无分支代码与可预测分支 | 去掉分支可能增加无效工作或数据依赖；分支预测稳定时，保留分支也可能更快。 |
| 扁平与节点式哈希表 | 扁平表可密集组织元数据和分组探测；节点式表可能更容易保持元素地址，但通常增加指针跳转。扩容、删除与引用稳定性也重要。 |
| 结构体填充 | 对齐和字段布局会影响对象大小；应查看目标 ABI 下的 `sizeof` 与成员偏移，再判断是否值得调整。 |
| 增加核心数 | 更多核心可执行更多独立工作，但共享带宽、一致性流量或同步争用可能成为瓶颈。 |

这些比较都是定位问题的线索，不是脱离负载的通用性能结论。

LRU 缓存常用 Map 从键定位已经存在的链表节点，再把该节点移动到最近使用端；前提是目标节点已由 Map 找到，随后改链只需有限次链接更新。若没有索引而要遍历链表找键，查找仍是 O(n)，指针追逐也没有消失。可继续看[队列、LRU 等数据结构的实际实现](#40.%20%E6%9C%80%E8%BF%91%E6%9C%80%E5%B0%91%E4%BD%BF%E7%94%A8%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E6%8C%89%E9%94%AE%E6%9F%A5%E6%89%BE%E5%B9%B6%E6%9B%B4%E6%96%B0%E6%9C%80%E8%BF%91%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F)。

**相关机制：** [数据结构怎样匹配访问方式，复杂度界何时成立？](#38.%20%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%A6%82%E4%BD%95%E5%8C%B9%E9%85%8D%E8%AE%BF%E9%97%AE%E6%96%B9%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F)说明链表更新所需的前驱与树高条件；[Linux 内核为什么把链表节点嵌入对象？](#49.%20Linux%20%E5%86%85%E6%A0%B8%E4%B8%BA%E4%BB%80%E4%B9%88%E6%8A%8A%E9%93%BE%E8%A1%A8%E8%8A%82%E7%82%B9%E5%B5%8C%E5%85%A5%E5%AF%B9%E8%B1%A1%EF%BC%9F)说明内嵌节点减少了哪种分配，以及为什么它仍然保留指针依赖。

> [!info]- 来源
> - 内存墙的提出背景：[Wulf 与 McKee，Hitting the Memory Wall: Implications of the Obvious（1995）](https://doi.org/10.1145/216585.216588)。
> - 预取、访问延迟与内存优化方向：[Intel 64 和 IA-32 架构优化参考手册（文档 248966-050US）](https://cdrdv2-public.intel.com/821612/248966-Optimization-Reference-Manual-V1-050.pdf)；微架构说明适用于相应 Intel 处理器，不代表所有 CPU 行为。
> - 链表局部性建议：[Linux 内核 Linked Lists in Linux](https://docs.kernel.org/core-api/list.html)，2026-11-06 核对。
> - 缓存行伪共享及其并发写入条件：[Linux 内核 False Sharing](https://docs.kernel.org/kernel-hacking/false-sharing.html)，2026-11-06 核对。
> - 连续容器保证：[C++ 草案 vector](https://eel.is/c++draft/vector)；C 数组定义：[WG14 C23 草案 N3047](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3047.pdf)。
> - JavaScript 索引集合语义：[ECMAScript 2026 Indexed Collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)；引擎数组种类示例：[V8 Elements kinds](https://v8.dev/blog/elements-kinds)。
> - 页式 B-tree 的实现范围：[PostgreSQL B-tree Implementation](https://www.postgresql.org/docs/current/btree.html)；密集哈希元数据示例：[Abseil Swiss Tables Design](https://abseil.io/about/design/swisstables)。
## 49. Linux 内核为什么把链表节点嵌入对象？

假设内核要把一个 work item（工作项）放进待处理队列，同时还要把同一对象放进审计队列。Linux 内核的 `struct list_head` 是一对 `next`、`prev` 链接；把它作为成员嵌进工作项，就能让通用链表代码只修改链接，不必为每种关系再分配独立包装节点。

~~~mermaid
flowchart LR
    Ready["ready_head"] <-->|next / prev| ReadyA
    ReadyA["工作项 A.ready_link"] <-->|next / prev| ReadyB["工作项 B.ready_link"]
    ReadyB <-->|next / prev| Ready
    Audit["audit_head"] <-->|next / prev| AuditA["工作项 A.audit_link"]
    AuditA <-->|next / prev| Audit
    subgraph ItemA["同一个 work_item A"]
        ReadyA
        AuditA
        PayloadA["id 与工作数据"]
    end
~~~

`ready_link` 与 `audit_link` 是同一对象内的两个不同钩子，同一个钩子在同一时刻只能属于一张链表。图中的 head 也是 `struct list_head`，不是额外的业务对象；空表时它的 `next` 与 `prev` 都指向自身。

### container_of 怎样从钩子找到对象？

Linux 链表节点不是一个含 payload 指针的单独 wrapper。`struct list_head` 本身就放在被链接的结构体内；`container_of(ptr, type, member)` 根据成员偏移，概念上从钩子地址减去 `offsetof(type, member)`，还原出外层对象地址。`list_entry()` 建立在这一机制上，`list_for_each_entry()` 则直接让循环变量指向外层结构体。

~~~c
struct work_item {
    u64 id;
    struct list_head ready_link;
    struct list_head audit_link;
};

static LIST_HEAD(ready_items);

static void inspect_ready_items(void)
{
    struct work_item *item;

    list_for_each_entry(item, &ready_items, ready_link) {
        /* item 是外层 work_item，可读取 item->id。 */
    }
}
~~~

这要求传入的指针确实指向指定类型中的那个成员；成员名和外层类型必须匹配。`container_of` 做的是地址计算，不会寻找节点，也不消除遍历时读取 `next` 的依赖。对象插入链表后也不能随意移动或复制，否则链表中保存的钩子地址就不再指向有效成员。

上面的遍历片段只展示宏怎样把钩子还原成外层对象；它假设队列在遍历期间不会被并发修改，并且其中对象仍然存活。共享队列的锁定方式见下一个完整示例。

### 插入、遍历和摘除分别改变什么？

下面的内核风格代码让两个关系共用一个互斥锁。初始化发生在首次插入前；`list_add_tail` 把当前链接放在 head 之前，因此队列顺序与入队顺序一致。

~~~c
#include <linux/list.h>
#include <linux/mutex.h>
#include <linux/types.h>

struct work_item {
    u64 id;
    struct list_head ready_link;
    struct list_head audit_link;
};

static LIST_HEAD(ready_items);
static LIST_HEAD(audit_items);
static DEFINE_MUTEX(items_lock);

static void init_work_item(struct work_item *item)
{
    INIT_LIST_HEAD(&item->ready_link);
    INIT_LIST_HEAD(&item->audit_link);
}

static bool enqueue_ready(struct work_item *item)
{
    mutex_lock(&items_lock);
    /* 检查与插入共用一把锁，避免重复挂入同一钩子。 */
    if (!list_empty(&item->ready_link)) {
        mutex_unlock(&items_lock);
        return false;
    }
    list_add_tail(&item->ready_link, &ready_items);
    mutex_unlock(&items_lock);
    return true;
}

static bool record_for_audit(struct work_item *item)
{
    /* audit_link 独立于 ready_link，但同样只能加入一张表。 */
    mutex_lock(&items_lock);
    if (!list_empty(&item->audit_link)) {
        mutex_unlock(&items_lock);
        return false;
    }
    list_add_tail(&item->audit_link, &audit_items);
    mutex_unlock(&items_lock);
    return true;
}

static u64 sum_ready_ids(void)
{
    struct work_item *item;
    u64 total = 0;

    mutex_lock(&items_lock);
    list_for_each_entry(item, &ready_items, ready_link)
        total += item->id;
    mutex_unlock(&items_lock);
    return total;
}

static void clear_ready_links(void)
{
    struct work_item *item;
    struct work_item *next;

    mutex_lock(&items_lock);
    list_for_each_entry_safe(item, next, &ready_items, ready_link)
        list_del_init(&item->ready_link);
    mutex_unlock(&items_lock);
}
~~~

`list_add_tail` 和 `list_del_init` 只需改动固定数量的链接，链表长度不会增加这部分指针操作的数量。但这不是整个操作的耗时保证：调用者可能还要扫描查找节点、取得锁、等待缓存或管理对象本身。`list_del_init` 只把该钩子从队列摘下并重新初始化；它既不释放 `work_item`，也不会摘掉同一对象的 `audit_link`。

`list_for_each_entry_safe` 会在循环体删除当前节点前保存下一游标，因此适合“遍历时删除当前项”。这里的 safe 不提供多线程同步。上例用同一把锁保护所有读写；锁的类型与持有范围要符合调用上下文。互斥锁只适用于可以睡眠的上下文。

若 ready 队列依次含有 A.id=4、B.id=7，而 audit 队列含 A，`sum_ready_ids()` 返回 11。`clear_ready_links()` 后 ready 总和变为 0，但 A 仍在 audit 队列，不能释放 A。

### 对象生命周期和并发访问由谁负责？

嵌入链表不会自动管理外层对象的生命周期。释放对象前，需要摘掉所有仍挂入链表的钩子，并确认没有其他读者或引用者还会访问对象。一个工作项在待处理队列中已摘除、但仍留在审计队列时，仍然不能释放。

普通链表操作本身不负责并发安全。多个线程或 CPU 并发修改同一链表时通常要用合适的锁；只有读多写少、允许读者暂时看到已移除项且能延迟销毁时，才考虑 RCU（read-copy-update，读-复制-更新）。RCU 读者在 `rcu_read_lock()` 与 `rcu_read_unlock()` 之间使用 `list_for_each_entry_rcu()`；写者用 `list_add_rcu()` / `list_del_rcu()`，并仍须由写锁或既有协议串行化相互竞争的写操作。删除后等 grace period（宽限期）结束才能回收对象，例如由 `call_rcu()` 延后释放。RCU 是读侧和生命周期协议，不是把普通 `list_for_each_entry_safe` 换个名字。

### 内嵌节点什么时候划算？

当对象由当前模块拥有、地址在入链期间稳定、一个对象需要参加多种频繁更新的关系，且减少独立包装节点的分配和查找有实际价值时，侵入式链表很合适。每种同时存在的关系仍需一个钩子，每个 `list_head` 仍有两个指针；设计并没有消除链接存储成本。

它也不会把对象放到物理连续的内存中。相邻链表节点可能远隔内存，遍历时仍要先取当前节点的 next 指针，再按它到达下一处数据。应把它看作简化关系表示和已知节点更新的办法，不要把它当作解决缓存局部性的办法。主要操作是顺序扫描时，连续数组往往更合适，具体比较见[为什么连续扫描往往比链表遍历快？](#48.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)。

这也不是说所有非侵入式列表都会“给业务对象再包一层指针并分配两次”。C++ 标准规定 `std::list` 的容器语义与操作复杂度，不规定具体节点布局；以 GCC libstdc++ 为例，内部节点把 T 放在节点自带的对齐存储中。那是一个实现样本，不是所有 `std::list` 实现的布局保证。

**相关机制：** [数据结构怎样匹配访问方式，复杂度界何时成立？](#38.%20%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%A6%82%E4%BD%95%E5%8C%B9%E9%85%8D%E8%AE%BF%E9%97%AE%E6%96%B9%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F)说明已知节点与查找前驱的复杂度差别；[内存层次如何改变实际访问成本？](#48.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)比较连续读取与逐节点指针依赖。

> [!info]- 来源
> - Linux 链表结构、初始化、插入、遍历、删除与删除时遍历：[Linux 内核 Linked Lists in Linux](https://docs.kernel.org/core-api/list.html)，2026-11-06 核对。
> - list_add_tail、list_del_init 与 list_for_each_entry_safe 的当前实现和注释：[Linux mainline include/linux/list.h](https://github.com/torvalds/linux/blob/master/include/linux/list.h)，2026-11-06 核对。
> - RCU 链表的读写侧协议与延后释放：[Linux 内核 Using RCU to Protect Read-Mostly Linked Lists](https://docs.kernel.org/RCU/listRCU.html)，2026-11-06 核对。
> - std::list 标准不规定节点内存布局：[C++ 草案 list](https://eel.is/c++draft/list)；对照实现样本：[GCC libstdc++ stl_list.h](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/stl_list.h)。
## 50. 如何让设计原则减少真实的修改成本？

以下用一个合成的通用页面编辑器案例说明原则：用户可以添加标题和按钮、拖动节点、预览并发布页面。需求可能增加新的组件类型，也可能改变保存方式、预览表现或权限规则。设计的关键不是提前把所有细节都变成接口，而是识别哪些变化会一起发生、哪些变化应彼此独立，然后只为高频或高代价的变化建立边界。

设计原则是判断边界的工具。若一个原则无法指出当前代码中哪种改动会扩散，以及边界如何缩小扩散范围，它就还没有给出引入抽象的理由。

~~~mermaid
flowchart TD
    Change["需求变化"] --> Question["会迫使哪些模块一起改？"]
    Question --> Evidence["重复规则 / 依赖方向 / 行为契约"]
    Evidence --> Boundary["建立最小而稳定的边界"]
    Boundary --> Cost["计算新增间接层与维护成本"]
    Cost --> Decision{"减少的修改成本<br/>是否大于新增成本？"}
    Decision -->|是| Keep["保留边界"]
    Decision -->|否| Simplify["直接实现，待真实变化出现"]
~~~

### 单一职责：按共同变化原因聚合

**Single Responsibility Principle（单一职责原则，SRP）**关注模块是否有多个彼此独立的变化原因，而不是类里是否只有一个方法。页面编辑器的节点持久化规则与画布阴影样式可能由不同需求驱动，因此可以归入文档存储与呈现模块。反过来，把每个字段都拆成类，会让理解一次简单修改要跳过许多文件。

判断时列出真实的变更来源：谁提出变化、哪条规则必须同步修改、哪些调用者只关心其中一部分。只有当这些来源相对独立，且当前耦合确实让修改变贵时，再拆分职责。

### 开闭：为已知的变化点留扩展位置

**Open/Closed Principle（开闭原则，OCP）**主张让稳定部分能在预期变化点扩展，而不是每增加一种情况都改动核心。它不是“永远不修改旧代码”，也无法预先关闭所有未来变化。

若编辑器已经支持标题、按钮两种组件，并且类型校验和渲染逻辑各不相同，可以把定义按类型注册。下面的 `renderNode` 只演示类型分发；调用前由通用文档 schema 确认 `node` 和 `props` 是对象、`type` 是字符串，注册表负责识别受支持类型并校验该类型字段：

~~~javascript
const definitions = new Map([
  ['heading', {
    validate: node => typeof node.props.text === 'string',
    render: node => ({ tag: 'h2', text: node.props.text }),
  }],
  ['button', {
    validate: node => typeof node.props.label === 'string',
    render: node => ({ tag: 'button', text: node.props.label }),
  }],
]);

function renderNode(node) {
  const definition = definitions.get(node.type);
  if (!definition) throw new RangeError('unsupported component type');
  if (!definition.validate(node)) throw new TypeError('invalid node');
  return definition.render(node);
}
~~~

新类型可以通过同一契约加入，渲染入口不必增加另一条类型分支。若现在只有一种节点，普通条件判断也许更清楚。扩展点仍需维护命名、契约和注册时机。

### 里氏替换：子类型不能改变调用者依赖的行为

**Liskov Substitution Principle（里氏替换原则，LSP）**关注行为契约：调用者依赖基类或接口的保证，替代实现也应满足。若渲染器承诺每个已注册组件都能渲染，某个“只供预览”的子类型不能在普通渲染时突然抛出未支持异常；可以把预览能力单独建模为接口或可选能力。

判断替换关系时要看前置条件、后置条件和不变量，不只是方法名与类型签名。若某个子类型要求调用者先做额外检查，它可能不属于同一可替换集合。Liskov 与 Wing 对行为子类型的描述强调，这是一种语义关系。

### 接口隔离与依赖倒置：按调用者需要定义契约

**Interface Segregation Principle（接口隔离原则，ISP）**要求按客户端实际使用的能力切分契约。画布只需要“把节点渲染成视图”，发布服务需要“校验并序列化文档”；若两者都被迫依赖包含编辑、渲染、保存和发布的大接口，修改与测试都会牵动无关能力。

**Dependency Inversion Principle（依赖倒置原则，DIP）**让高层策略和底层细节通过稳定契约协作。发布流程表达“保存已校验修订”，存储适配器负责具体数据库调用。**dependency injection（依赖注入）**可以把适配器传给流程，但它只是组织依赖的一种技术，不等同于依赖倒置。

只有在替换存储、隔离测试或改变部署方式是真实需求时，这条边界才值得存在。若应用只有一个简单内存存储，数层接口可能只增加跳转。

### DRY、KISS 与 YAGNI 如何约束抽象？

DRY（Don't Repeat Yourself，不重复同一知识）针对必须保持一致的规则重复，不要求所有相似代码都合并。标题文本和按钮标签都用字符串，不表示它们需要相同业务模型；但“组件类型是否允许发布”的规则若复制在预览与发布两处，就容易不一致。

KISS（Keep It Simple，保持简单）要求方案与当前问题的复杂度相称。YAGNI（You Aren't Gonna Need It，尚未需要的能力先不实现）提醒团队别为没有证据的未来需求造扩展接口。它们不要求忽略已发生的耦合：当一次变更反复影响多处，抽象收益就有了证据。

### 用变化案例决定边界

新增图片组件时，依次问：它是否有不同配置、校验或渲染语义？规则未来是否会独立变化？所有调用者是否都需要了解图片逻辑？注册表是否真的减少改动范围？若答案支持稳定变化点，注册表可能有用；若只是固定页面的一次分支，直接写条件更好。

[前端架构怎样划分呈现、交互和数据所有权？](#51.%20%E5%89%8D%E7%AB%AF%E6%9E%B6%E6%9E%84%E6%80%8E%E6%A0%B7%E5%88%92%E5%88%86%E5%91%88%E7%8E%B0%E3%80%81%E4%BA%A4%E4%BA%92%E5%92%8C%E6%95%B0%E6%8D%AE%E6%89%80%E6%9C%89%E6%9D%83%EF%BC%9F)讨论状态归属；[页面编辑器何时需要设计模式？](#52.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E4%BD%95%E6%97%B6%E9%9C%80%E8%A6%81%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%EF%BC%9F)展示工厂、策略和通知怎样落实边界。

> [!info]- 来源
> - 行为子类型的契约基础：[Barbara Liskov 与 Jeannette Wing, A Behavioral Notion of Subtyping](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf)。
> - OCP、SRP 等面向对象原则讨论：[Robert C. Martin, Principles and Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。
## 51. 前端架构怎样划分呈现、交互和数据所有权？

以下沿用合成的页面编辑器案例：画布显示文档树，检查器编辑当前节点属性，工具栏新增组件，预览页呈现访客看到的页面。如果各处各存一份节点数据，拖动或重命名就可能让它们失步。架构应先说明每份状态由谁拥有、哪些模块能发出修改，再决定组件怎样拆分或代码如何部署。

~~~mermaid
flowchart TD
    Select["选择节点"] --> Session["编辑会话：selectedId / dragPreview"]
    Drag["拖动中的候选位置"] --> Session
    Session --> CanvasPreview["画布显示选中和拖动预览"]
    Session --> Inspector["检查器显示当前节点属性"]
    Commit["确认属性修改或放下排序"] --> Intent["命令表达已提交的编辑"]
    Intent --> Owner["文档状态所有者"]
    Owner --> Revision["生成新的文档修订"]
    Revision --> Canvas["画布读取新文档"]
    Revision --> Inspector
    Revision --> Preview["预览器读取同一修订"]
~~~

文档节点属于可保存页面内容；当前选中项、拖动状态和面板属于编辑会话；焦点和输入光标等短暂状态通常留在组件内部。不是所有状态都要进全局状态存储，但每种状态都应有清楚的所有者。

### 单向数据流让修改原因可追踪

unidirectional data flow（单向数据流）让状态所有者把当前数据传给视图，视图通过事件或命令请求变化。检查器不私下改写画布节点副本，而是发出“把 `heading-1` 的 `text` 改成‘欢迎’”这样的意图。

以下沿用同一个修订 12 的页面案例；完整文档与会话输入见[修订 12 的文档与编辑会话数据](#%E6%96%87%E6%A1%A3%E6%A0%91%E5%92%8C%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E8%AE%B0%E5%BD%95%E4%B8%8D%E5%90%8C%E4%BA%8B%E5%AE%9E)，可运行命令代码也在那里。选择、拖动预览和已提交修改走不同路径：

| 事件 | 编辑会话 | 文档修订 |
|---|---|---|
| 选中 `heading-1` | `selectedId` 设为 `heading-1` | `revision` 仍为 12，文本仍是“首页” |
| 在检查器确认标题改为“欢迎” | `selectedId` 仍为 `heading-1` | 所有者校验后产生 `revision` 13 |
| 把 `heading-1` 拖到 `button-1` 后的预览 | `dragPreview` 记录候选位置 | `revision` 仍为 13，节点顺序不变 |
| 在画布放下并确认排序 | 清除 `dragPreview` | 独立命令产生 `revision` 14，`rootIds` 变为 `['button-1', 'heading-1']` |

所以拖动中的每个鼠标移动都不需要写入可保存文档；只有放下并接受排序变更时才提交文档命令。React 官方状态共享指南用“将共享状态提升到最近共同父级”解释这种所有权；其他框架可以用不同机制实现同样约束。经典 Flux 模型让 action（动作）经过 dispatcher（分发器）到 store（状态存储），再由 store 通知 view（视图）；其他状态库采用不同契约，重点是让状态变化及其原因可追踪。

### 组件与分层分别解决什么问题？

**component-based architecture（基于组件的架构）**按可复用视图和交互边界拆分 user interface（用户界面，UI）。`Canvas` 呈现画布，`Inspector` 编辑属性，`NodeView` 呈现一种节点类型。组件接口应写明输入输出：数据与回调怎样传入，选择、修改、删除等意图怎样传出。不是每个组件都要持有状态、调用服务并执行副作用。

分层则按职责分开状态管理、领域命令、持久化适配和视图。小编辑器可能只需要几个清楚模块；只有一层确实承载独立规则或依赖边界时，再拆成独立包或服务。为每个组件都造“控制器—服务—仓库”容易使跟踪简单操作变慢。

文档树顺序也不等于最终绘制顺序。浏览器布局和 CSS stacking context（堆叠上下文）参与绘制；若编辑器显示精确图层，需要把节点顺序、定位和堆叠上下文规则一并纳入模型。

### 何时微前端有实际收益？

**micro-frontend（微前端）**按业务或团队边界拆分可独立开发、集成、发布的部分。可以构建时组合、运行时加载、用 iframe 或 Web Components；隔离、依赖共享、导航和样式方式各不相同。

页面编辑器的检查器与画布若由同一团队同步发布，放在一个模块化应用更简单。若多支独立团队分别负责组件库、编辑器和资产管理，且确实需要独立发布，微前端可能减少协调阻塞。此时仍要定义路由、权限、设计系统、可访问性、错误处理、遥测、依赖版本和加载失败处理，否则集成成本会变成运行时故障。

微前端是组织与部署边界，不是把普通组件拆成多个项目的同义词。若主要问题是共享状态或数据流不清，先解决状态所有权通常更直接。

### 怎样迁移微前端而不打断深链、身份与回退？

沿用一个合成的页面编辑器：文档 `assetId=42` 当前处于 `revision=12`，选中的节点是 `heading-1`。旧应用通过 `/editor/assets/42?panel=inspector&node=heading-1#canvas` 打开它，新入口使用 `/assets/42/edit?panel=inspector&node=heading-1#canvas`。路径和文档 ID 是本教学变体；页面文档与编辑会话状态仍按[编辑器数据模型](#53.%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E9%A1%B5%E9%9D%A2%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)的稳定节点 ID 和修订区分。`node=heading-1` 只是可恢复的界面选择，不会进入页面文档或修改 revision。新旧地址先并存，让旧书签、邮件链接和浏览器历史都有确定去向。

迁移时由同一个 shell（应用外壳）持有顶级路由、会话启动、公共导航与错误边界；路由注册表把旧路径交给 `EditorV1`，新路径先交给 `EditorV1`，再按用户 cohort（灰度分组）将一小部分流量映射至 `EditorV2`。两版可独立构建，但路由、参数和通用数据格式是容器与子应用之间的合同。路由决策须在挂载前作出：

| 地址或状态 | shell 的责任 | 子应用收到的输入 |
|---|---|---|
| 旧深链 `/editor/assets/42?panel=inspector&node=heading-1#canvas` | 迁移窗口内继续交给 V1；用户从页面主动打开新入口时才新增新路径 | `assetId=42`、`panel=inspector`、`node=heading-1`、`#canvas` |
| 新地址 `/assets/42/edit?panel=inspector&node=heading-1#canvas`，未进入 cohort | 路由仍由 `EditorV1` 处理，不让用户落入空白占位页 | 同一 `assetId` 与视图状态 |
| 同一新地址，进入 cohort | 动态加载 `EditorV2`，并显示加载或失败状态 | 同一 `assetId` 与视图状态，不另造一份身份 |
| 浏览器 Back / Forward | shell 独自响应 `popstate` 并重新匹配完整地址 | `panel` 和有效 `node` 从恢复的 URL 查询恢复；片段仍定位到 `#canvas` |

每个子应用只处理传给它的资源标识和视图状态，通过 shell 提供的 `navigate()` 或明确的同源链接请求跨边界导航。shell 是唯一的 history（历史记录）所有者，因此 V1/V2 不会各自安装互不知情的路由器、重复写 `pushState` 或抢先处理 Back。迁移窗口保留旧路由供旧书签与返回历史使用；用户从旧界面主动打开新入口时，shell 用 `pushState` 记录新路径，这样 Back 可回到原页面。若迁移窗口结束后需把旧路由作为别名改写到新路径，才用 `replaceState` 保留原有 query 与 fragment，避免用户按 Back 时在两个等价地址间循环。浏览器处理新地址的硬刷新请求时，静态宿主还须将已知前端路径回退到 shell HTML，同时仍把 `/api/` 请求交给 API 服务。

身份也由宿主边界明确归属。本例 shell 通过 `HttpOnly`、`Secure` 的同源会话 cookie 建立身份，给子应用 `assetId`、非敏感显示信息和受限的数据访问接口，不把访问令牌或会话凭据放入路由参数、DOM、共享状态广播或子应用的 prompt。V1 与 V2 都通过同源 API 读取 `/api/assets/42`；浏览器随请求带会话 cookie，服务端在每次读取和写入时验证当前主体是否能访问该资源。客户端允许显示哪个路由只决定可见页面，不能替代服务端资源鉴权。`node` 只在页面文档加载后与该 revision 的稳定节点 ID 对照；缺失或不存在的节点参数会清除选择并显示文档，而不是请求任意资源。若子应用部署到独立 origin（源），cookie、令牌和跨源身份方案要另外设计；不能假设同源会话自动跨域。

同一份页面文档以明确版本的 schema 交给 V1 和 V2。本轮只迁移入口，不修改文档字段或服务端数据协议，因此两版都能读取和写回 `revision=12` 的既有文档。若 V2 将来要写入新字段，只有在 V1 会原样保留未知字段、或迁移窗口的路由规则能保证旧版不会重新打开含新字段的数据时才可开放；仅仅让 V1 读入时忽略字段，不保证下一次保存时不会把它删掉。删除或重解释字段也要等 V1 不再负责读写。若当前 revision 仍是 12，V2 的未保存草稿不能只因它的动态 chunk 加载失败就被静默丢弃：在编辑开始前加载失败，shell 可以映射到 V1；编辑开始后若要切换实现，应先将草稿转换成共享会话格式或让用户留在当前编辑器处理，否则停止回退并保留草稿。服务端拒绝的未授权访问不应触发降级到另一个前端，避免把代码加载回退误当成授权绕过。

发布按路由逐步改变 owner：先让 shell 可加载两版并验证同一输入合同；再在限定 cohort 中把 `/assets/:assetId/edit` 分给 V2；确认直接深链与刷新、嵌套 query/fragment、V1↔V2 导航、Back/Forward、未授权资源拒绝、V2 chunk 加载失败和 V1 兼容读取都正确后才扩大分流。每个检查都对应一次可见状态变化，而不是只确认首页能挂载。若 V2 的加载率或错误率越过约定门槛，路由注册表将新地址恢复映射到 V1；保持该路径可用让已有书签和历史项继续打开旧实现。仍需保留两版 chunk 和向后兼容的数据合同，才可以在出现问题后真正回退，而不只是把 flag 改回去。

路由契约是微前端沟通的一种公开边界；改变 route schema 或版本映射时要与所有链接来源一起验收。实施过程借用[静态资源版本并存与入口回滚](../../frontend/tooling/build-tools.md)中的旧 chunk 保留规则；新旧服务端资源合同仍要遵循[HTTP API 的授权与条件更新契约](#3.%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F)。

**延伸阅读：**[设计原则怎样帮助定位真实变化边界？](#50.%20%E5%A6%82%E4%BD%95%E8%AE%A9%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99%E5%87%8F%E5%B0%91%E7%9C%9F%E5%AE%9E%E7%9A%84%E4%BF%AE%E6%94%B9%E6%88%90%E6%9C%AC%EF%BC%9F)、[页面编辑器何时需要设计模式？](#52.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E4%BD%95%E6%97%B6%E9%9C%80%E8%A6%81%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%EF%BC%9F)、[怎样建模页面文档、编辑会话和发布快照？](#53.%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E9%A1%B5%E9%9D%A2%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)。

> [!info]- 来源
> - 组件间共享状态的所有权：[React：Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)。
> - 堆叠上下文内的 CSS 绘制顺序：[W3C CSS 2.2, Appendix E](https://www.w3.org/TR/CSS22/zindex.html)。
> - 微前端的团队发布边界和集成权衡：[Martin Fowler, Micro Frontends](https://martinfowler.com/articles/micro-frontends.html)。
> - 路由作为容器与子应用之间的合同：[Martin Fowler, Micro Frontends, “Cross-application communication via routing”](https://martinfowler.com/articles/micro-frontends.html#Crossapplicationcommunicationviarouting)，核对日期 2026-11-09。
> - 同源历史写入、恢复与 `popstate`：[WHATWG HTML Standard, History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，持续更新规范，核对日期 2026-11-09。
## 52. 页面编辑器何时需要设计模式？

沿用合成的页面编辑器案例，编辑者要创建标题、按钮等节点，为不同类型校验配置，通知画布和检查器刷新，并共享组件定义。**design pattern（设计模式）**为这些重复结构取名，但模式本身不会替你决定状态所有者、权限边界或对象生命周期。先说清问题，再看模式是否能让变化集中而仍容易跟踪。

模式有代价：额外类型、注册步骤、调用层和清理责任。若间接层没有减小真实修改范围，普通函数或条件分支更清楚。

### 创建规则变多时，用工厂集中入口

**factory（工厂）**把创建规则放在一处：生成稳定 ID、填入默认属性并拒绝未知类型。它通常先是一个函数，不必马上设计成复杂层级。这样的简单工厂函数不自动等同于《设计模式》中的 Factory Method（工厂方法）或 Abstract Factory（抽象工厂）模式。

~~~javascript
const defaults = new Map([
  ['heading', { text: '新标题', level: 2 }],
  ['button', { label: '按钮', variant: 'primary' }],
]);

let nextId = 1;

function createNode(type) {
  const initialProps = defaults.get(type);
  if (!initialProps) throw new RangeError('unknown component type');
  if (!Number.isSafeInteger(nextId)) throw new RangeError('node ID counter exhausted');
  const id = 'node-' + nextId;
  nextId += 1;
  return { id, type, props: { ...initialProps }, children: [] };
}

const heading = createNode('heading');
// heading.id === 'node-1'; createNode('constructor') throws RangeError
~~~

多个入口若各自生成默认字段和 ID，很容易得到不一致节点，共用入口就有价值。若只在一处创建固定对象，直接写对象更简单。这里的 Number 计数器只在当前模块运行期间有效；越过安全整数范围时工厂会停止发号。可持久化文档或协作编辑还需要跨重启、跨窗口不冲突的 ID 生成方案。工厂生成的草稿并不代表权限或发布校验已经完成。

### 行为可互换时，用策略

**strategy（策略）**把不同算法放进同一调用契约。编辑器可按组件类型选择配置校验器；通用 schema 已先确认 node 是对象、type 是字符串且 props 是对象，这些策略只检查对应类型的特有字段并返回错误集合。

~~~javascript
const validators = new Map([
  ['heading', node => (
    typeof node.props.text === 'string' ? [] : ['标题文本必须是字符串']
  )],
  ['button', node => (
    typeof node.props.label === 'string' ? [] : ['按钮需要标签']
  )],
]);

function validateNode(node) {
  const validate = validators.get(node.type);
  return validate ? validate(node) : ['未知组件类型：' + node.type];
}

validateNode({
  id: 'button-1',
  type: 'button',
  props: { label: '发布' },
});
// []
~~~

调用者不需要理解每种组件的检查细节。新增策略是否真的避免集中式分支，取决于注册、类型管理和错误契约是否也统一。若规则少而稳定，普通 `switch` 可能更好。策略不能取代输入校验或授权检查。

### 多个视图订阅同一修订时，用观察者

**observer（观察者）**结构中，状态主体直接维护订阅者并通知变化。下面用 `DocumentNotifier`（文档通知器）只展示通知职责；文档数据仍由上游状态所有者持有。订阅者应能取消订阅，避免卸载视图继续被引用。浏览器 `EventTarget` 也是这种直接注册到目标对象的观察者式 API，见[DOM 事件与交互](../../frontend/browser-apis/dom-manipulation-and-events.md)。

~~~javascript
class DocumentNotifier {
  #listeners = new Set();

  subscribe(listener) {
    this.#listeners.add(listener);
    return () => this.#listeners.delete(listener);
  }

  notify(document) {
    for (const listener of this.#listeners) listener(document);
  }
}

const notifier = new DocumentNotifier();
const unsubscribe = notifier.subscribe(document => {
  console.log('画布收到修订', document.revision);
});

notifier.notify({ revision: 13 });
unsubscribe();
~~~

该循环是同步通知：若一个 listener 抛错，异常会向调用方传播，后续 listener 不会继续收到本轮通知；遍历期间新增或删除 listener 也遵循 Set 迭代器的实时行为。这个小例没有隔离回调异常或冻结订阅快照。

**publish-subscribe（发布订阅）**常通过主题或中介路由消息，让发布者不必掌握每个接收者。若插件要监听 `document:saved`，典型实现会从 `listenersByTopic.get(topic)` 取得 Set 并同步通知，其中每个 Set 保存该主题的订阅者；取消时从同一 Set 删除 listener。它可能减少直接依赖，但全局事件名和隐式调用会让修改来源难以追踪。简单父子组件回调已足够时，不用事件总线。实际 API 可能混合两种形式，应看订阅由谁持有、消息如何路由。

### 共享实例有明确范围时，才用单例

**singleton（单例）**让某个范围通过统一入口访问一个共享实例。例如一个编辑器应用实例可以持有一份组件注册表。在 JavaScript 中，模块变量通常由当前模块实例共享；worker、进程、重复加载的模块副本之间不自动共享同一个对象。

全局单例会隐藏依赖，也可能让多个编辑器或测试互相污染。显式创建 `EditorRuntime` 并传给使用者通常更易测试。必须说清“一份”是每个模块、应用、进程还是其他范围。若该类仍暴露公有构造器，调用者通常仍能直接创建额外实例，访问器并不会自动阻止这种创建。

### 用设计原则检查模式是否合适

工厂和策略可支持开闭原则，但若它们没有缩小修改范围，就不需要硬套。观察者让变化通知多个视图；依赖倒置要求高层编辑流程依赖通知契约，而非绑死具体全局总线。每个订阅者的生命周期也仍需明确。

新增图片节点时，工厂建立默认配置、校验策略检查属性、状态所有者接受“插入图片”命令，生成新修订后再通知画布。模式说明局部对象怎样协作；文档结构、撤销历史、发布版本与冲突处理见[页面文档和发布快照的数据模型](#53.%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E9%A1%B5%E9%9D%A2%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)。组件之间的数据所有权见[前端架构边界](#51.%20%E5%89%8D%E7%AB%AF%E6%9E%B6%E6%9E%84%E6%80%8E%E6%A0%B7%E5%88%92%E5%88%86%E5%91%88%E7%8E%B0%E3%80%81%E4%BA%A4%E4%BA%92%E5%92%8C%E6%95%B0%E6%8D%AE%E6%89%80%E6%9C%89%E6%9D%83%EF%BC%9F)。

> [!info]- 来源
> - 工厂、策略、观察者等模式的适用情境和权衡：[Gamma、Helm、Johnson、Vlissides, Design Patterns: Elements of Reusable Object-Oriented Software](https://www.oreilly.com/library/view/design-patterns-elements/0201633612/)。
> - 模式与设计原则应服务于变化边界：[Robert C. Martin, Principles and Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。
> - Set 的实时迭代语义：[ECMAScript 2026, Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-set-iterator-objects)。
## 53. 怎样建模页面文档、编辑会话和发布快照？

以下用一个合成的通用页面编辑器案例：编辑者正在修改 revision 12 的首页，页面含标题和报名按钮；编辑者需要改文案、拖动排序、撤销修改并发布审核后的版本。若把页面内容、当前选中项、拖动中的临时位置和公开输出塞进同一对象，简单选择也可能触发保存和历史记录，发布时也难以确定实际使用哪个版本。

先分开三个生命周期：可保存文档、只服务当前编辑器会话的状态，以及从某个文档修订派生的发布快照。

~~~mermaid
flowchart TD
    Command["编辑命令"] --> Validate["按结构与业务规则校验"]
    Validate --> Document["页面文档 revision 13"]
    Document --> History["撤销 / 重做历史"]
    Document --> Preview["编辑预览"]
    Document --> PublishCheck["发布校验"]
    PublishCheck --> Snapshot["不可变快照 revision 13"]
    Snapshot --> PublicPage["访客页面"]
    Session["编辑会话：选中 ID / 面板"] --> Canvas["画布与检查器"]
    Document --> Canvas
~~~

### 文档树和编辑会话记录不同事实

文档要保存页面事实：节点稳定身份、组件类型、属性和子节点。编辑会话记录当前选择、焦点面板、拖动候选目标等短暂 UI 状态。

~~~javascript
const documentState = {
  schemaVersion: 1,
  revision: 12,
  rootIds: ['heading-1', 'button-1'],
  nodes: {
    'heading-1': {
      id: 'heading-1',
      type: 'heading',
      props: { text: '首页', level: 1 },
      style: { position: 'absolute', top: 100, left: 200 },
      children: [],
    },
    'button-1': {
      id: 'button-1',
      type: 'button',
      props: { label: '报名', action: { kind: 'navigate', pageId: 'form' } },
      children: [],
    },
  },
};

const editorSession = {
  selectedId: null,
  openPanel: 'inspector',
  dragPreview: null,
};
~~~

`rootIds` 表示顶层顺序；`nodes` 按 ID 索引，便于定位和局部更新。示例采用已提交文档中的森林规则：根 ID 不重复，根节点不能同时作为子节点；每条父子边只出现一次，每个非根节点恰有一个父节点；所有节点都能从某个根到达，且不形成环。只检查 ID 唯一、引用存在和无环还不够，因为两个父节点仍可能引用同一个孩子，文档里也可能留下无法从根到达的孤儿节点。新节点在尚未挂到树上时可以先留在编辑会话的拖动草稿中，提交命令前再检查这些约束。

较小编辑器也可用嵌套树，避免过早规范化，但仍需保持相同的单父和根归属规则。示例中的 `style` 是产品选择持久化的布局配置；如果它只用于画布临时呈现，则应留在编辑会话。`selectedId` 是对节点的引用，不是节点属性；切换选择不推进文档修订、不进入撤销历史，也不影响发布内容。

### 稳定身份与命令使修改可追踪

数组下标会因插入和排序改变，不适合作为长期节点身份。稳定 ID 让检查器、历史记录与协作消息指向同一节点。**command（命令）**把用户意图表示为可检查操作，例如把 `heading-1` 的 `text` 改为“欢迎”。

下面的代码承接上节定义的完整 `documentState`，包括 `schemaVersion`、`rootIds`、标题样式和报名按钮；它只更新标题文本，不重新声明或裁剪初始文档。

~~~javascript
function updateNodeText(document, id, text) {
  const node = document.nodes[id];
  if (!node || node.type !== 'heading') {
    throw new RangeError('heading does not exist');
  }

  return {
    ...document,
    revision: document.revision + 1,
    nodes: {
      ...document.nodes,
      [id]: { ...node, props: { ...node.props, text } },
    },
  };
}

const revision13 = updateNodeText(documentState, 'heading-1', '欢迎');
// revision13 仍有 rootIds=[heading-1, button-1]，button-1 未变；只改标题并从 12 变为 13。
~~~

撤销和重做可以保存前后状态快照，也可以记录带逆操作的命令。快照简单但占更多存储；逆操作紧凑，却必须正确处理删除、移动和并发修改。输入字段可以每次击键更新，也可本地缓冲到失焦再提交；提交到文档的修改仍须经过一致验证路径。

### `schema`（结构描述）描述形状，业务规则解释含义

**component registry（组件注册表）**为每种类型提供配置形状、渲染器和可选校验器。`schema`（结构描述）可声明标题文本是字符串、按钮标签必填。JSON Schema 2020-12 可校验 JSON 结构，但应用还需检查引用页面是否存在、用户是否有权发布，或组件树是否允许特定父子关系。

未知类型、缺失 ID、非法属性和悬空引用都应在持久化或发布前给出可定位错误。客户端校验改善反馈，但授权应由可信服务端重新检查。不要让渲染阶段以空白组件静默掩盖无效文档。

### 文档顺序不等于全部绘制顺序

子节点顺序可定义图层面板中的逻辑顺序，但浏览器绘制还受定位、`z-index` 和 **stacking context（堆叠上下文）**影响。若产品提供“置顶”或“置底”，要定义它改的是节点顺序、同一堆叠上下文内的层级，还是更高层渲染模型。单独重排数组不能保证元素跨越 CSS 上下文覆盖另一个元素。

### 发布绑定确切修订，避免混入未校验草稿

发布服务应选择具体文档修订，执行结构校验、引用检查、权限检查和资源确认，再生成公开页面所需数据或制品。快照应记录 `documentId`、`revision`、`schema` 版本等来源。若构建期间只引用“当前文档”，草稿更新可能让未校验内容混入产物。仅固定文档修订还不足以重现输出：快照应同时固定组件注册表、渲染器和会影响页面的外部资源版本，或保存确切制品并封存/固定它引用的外部资源；否则重渲染或浏览仍可能读到新素材，显示效果随时间变化。

草稿修订和公开版本可并存：编辑生成 revision 14 时，访客仍看到已校验的 revision 13。发布完成后原子切换活动版本引用；回滚则重新指向已发布快照，而不是把旧内容复制进当前草稿。

### 协作、传输与冲突解决需要分别设计

`WebSocket` 能传输编辑事件，却不会自动决定两人同时移动同一节点时谁胜出。单写者模型可让服务端排序命令；锁能防并发但增加等待。operational transformation（操作转换，OT）通过转换并发操作维护规定的一致性；conflict-free replicated data type（无冲突复制数据类型，CRDT）可在满足其收敛条件时合并副本更新。两种方案都要求定义操作格式、冲突语义与版本兼容。

按离线需求、即时合并、服务端排序和审计要求选择机制。即便采用 CRDT，树结构约束、组件 schema 和发布校验仍然必要。协作是数据所有权与更新协议的一部分，不能因使用 WebSocket 就认为冲突已解决。

**相关机制：**[前端架构怎样划分状态所有权？](#51.%20%E5%89%8D%E7%AB%AF%E6%9E%B6%E6%9E%84%E6%80%8E%E6%A0%B7%E5%88%92%E5%88%86%E5%91%88%E7%8E%B0%E3%80%81%E4%BA%A4%E4%BA%92%E5%92%8C%E6%95%B0%E6%8D%AE%E6%89%80%E6%9C%89%E6%9D%83%EF%BC%9F)说明谁持有文档与会话状态；[页面编辑器何时需要设计模式？](#52.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E4%BD%95%E6%97%B6%E9%9C%80%E8%A6%81%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%EF%BC%9F)说明创建、校验和通知的局部实现。

> [!info]- 来源
> - JSON Schema 2020-12 文档与校验规范：[JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)。
> - 堆叠上下文中的绘制顺序：[W3C CSS 2.2, Appendix E](https://www.w3.org/TR/CSS22/zindex.html)。
> - 组件共享状态的单一所有权示例：[React：Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)。
> - CRDT 的副本收敛条件：[Shapiro 等，Conflict-free Replicated Data Types（2011）](https://perso.lip6.fr/Marc.Shapiro/papers/2011/CRDTs_SSS-2011.pdf)。
> - OT 中并发操作转换与一致性属性：[Sun 等，Achieving Convergence, Causality Preservation, and Intention Preservation in Real-Time Cooperative Editing Systems（1998）](https://www.cs.cityu.edu.hk/~jia/research/reduce98.pdf)。
## 54. Scrum 怎样让团队检查并调整工作？

假设团队正在开发页面编辑器，目标是让用户创建内容并安全发布。产品方向可能需要数月才能实现，单个 Sprint（冲刺周期）只能完成其中一部分；团队需要不断判断工作是否仍有价值、遇到阻碍时是否要调整计划。

Agile（敏捷）是一组强调协作、可用软件、客户合作和响应变化的价值观与原则；Scrum 是用于复杂工作的轻量框架，规定团队职责、事件、工件和承诺。Product Goal（产品目标）、Product Backlog（产品待办列表）、Sprint Goal（Sprint 目标）、Sprint Backlog（Sprint 待办列表）、Increment（增量）与 Definition of Done（完成定义）在框架中共同提供方向与质量边界。框架创造检查与适应的节奏，但不会自动保证估算准确、交付质量或用户价值。

~~~mermaid
flowchart TD
    ProductGoal["Product Goal（产品目标）<br/>让非开发者安全创建并发布简单页面"] --> Backlog["有序的 Product Backlog（产品待办列表）"]
    Backlog --> Planning["Sprint Planning（Sprint 计划）<br/>为什么 / 做什么 / 怎样做"]
    Planning --> SprintGoal["Sprint Goal（Sprint 目标）<br/>访客能看到已发布标题页"]
    SprintGoal --> Work["Sprint Backlog（Sprint 待办列表）：所选工作与执行计划"]
    Work --> Daily["Daily Scrum（每日 Scrum）：检查进展并调整计划"]
    Daily --> Work
    Work --> Increment["符合 Definition of Done（完成定义）的可用 Increment（增量）"]
    Increment --> Review["Sprint Review（Sprint 评审）：检查结果并讨论下一步"]
    Review -->|产品方向与待办反馈| Backlog
    Review --> Retro["Sprint Retrospective（Sprint 回顾）：改进协作和质量"]
    Retro --> Planning
~~~

### 敏捷价值观不是一套固定流程

《敏捷软件开发宣言》强调四组价值：个体与互动高于流程与工具、可工作的软件高于详尽文档、客户合作高于合同谈判、响应变化高于遵循计划。右侧内容仍有价值；宣言表达的是左侧受到更高重视。它没有要求团队放弃文档、计划、流程或合同。十二条原则还提到可持续节奏、持续技术卓越、简洁与定期反思等做法。

把敏捷理解成“完全不做计划”会错过重点：计划应根据反馈持续调整，而不是一次承诺后就不再检查。文档、验证和法规证据也可以服务于快速而可靠的反馈。

### Scrum 用目标和工件建立透明度

**Scrum Team（Scrum 团队）**包含 **Product Owner（产品负责人）**、**Scrum Master（Scrum 引导者）**和 **Developers（开发者）**三类职责；它们是责任，不必对应固定职位。Product Owner 对产品价值和 Product Backlog 管理负责，可以委托待办列表的具体管理活动但仍对效果负责；Scrum Master 帮助团队按 Scrum 运作、提升有效性并协助解除障碍；Developers 负责创建可用增量、维护 Sprint Backlog 计划并达到 Definition of Done。

| 工件 | 对应承诺 | 页面编辑器案例中的作用 |
|---|---|---|
| Product Backlog（产品待办列表） | Product Goal（产品目标） | 持续排序创建、编辑、预览和发布的工作，朝产品目标前进。 |
| Sprint Backlog（Sprint 待办列表） | Sprint Goal（Sprint 目标） | 包含目标、所选工作和 Developers 的执行计划；计划可随学习调整。 |
| Increment（增量） | Definition of Done（完成定义） | 与以往增量集成、满足产品质量标准的一步可用成果。 |

例如，Product Goal 可以是“让非开发者安全创建并发布简单页面”。一个 Sprint Goal 可以是“访客能看到包含标题的已发布页面”。团队可将存储节点、预览页面和最小校验作为候选工作；只有满足完成定义并整合到产品的部分才是 Increment。一轮 Sprint 中可以形成多个 Increment，只要每个都满足 Definition of Done 并集成到产品。

### Sprint 事件让计划贴近现实

Sprint 是一个月以内的固定长度事件，包含 Sprint Planning、Daily Scrum、Sprint Review、Sprint Retrospective 和全部工作活动；Sprint 容纳其余四个正式事件。Scrum Guide 不规定两周的固定节奏；团队选择能形成稳定检查与反馈、又不拖慢调整的长度。

Sprint Planning（Sprint 计划）讨论为什么这个 Sprint 有价值、可以做什么、如何完成。团队建立 Sprint Goal、选择适合的 Product Backlog 项，Developers 制定执行计划。进入 Sprint 后，Developers 可根据新信息调整 Sprint Backlog，并与 Product Owner 澄清和协商范围，以保护 Sprint Goal。

Daily Scrum（每日 Scrum）是 Developers 检查朝 Sprint Goal 的进展并调整计划的 15 分钟事件，不是每个人向主管轮流汇报昨日、今日和阻碍的固定格式。团队选择最能帮助协同工作的形式。

Sprint Review（Sprint 评审）是团队与利益相关者检查结果、讨论环境变化并协作决定下一步的工作会话。它不是发布审批关卡；符合 Definition of Done 的增量可按产品需要在 Review 前发布。Sprint Retrospective（Sprint 回顾）检查人际协作、流程、工具与质量，挑选可落实的改进。

### 遇到变化时，保护目标并重谈范围

若页面发布服务的权限校验失效，访客可能看到未授权内容，这会直接威胁“访客能看到已发布标题页”所要求的安全发布。Developers 应先确认影响、向 Product Owner 说明修复与复测所需工作，再共同判断是否延后非核心样式微调以保护 Sprint Goal。若目标本身已失去价值，Product Owner 可取消 Sprint，而不是要求团队继续假装原计划仍适用。

常见误区可从工件和事件的用途识别：

- 把 Sprint Backlog 当作冻结合同，会让计划无法反映实际学习。
- 把 Daily Scrum 当作人员考核汇报，会挤掉团队协作和适应计划的机会。
- 把 Sprint Review 当作单向演示或发布审批，会削弱共同检查和调整的目的。
- 只保留仪式名称、忽略透明、检查和适应，会失去框架的工作机制。

若使用 Scrum，应按其定义运行并检查结果；若不适合，也可采用其他匹配产品复杂度、反馈周期和约束的协作方式。

> [!info]- 来源
> - Scrum Guides 当前官方版本为 2020 年 11 月版；本文按其角色、事件、工件和承诺定义：[The Scrum Guide](https://scrumguides.org/scrum-guide.html)，[官方版本下载页](https://scrumguides.org/download.html)。
> - 敏捷价值观及左右两侧的关系：[Manifesto for Agile Software Development](https://agilemanifesto.org/)。
## 55. 怎样准备有事实支撑的行为面试回答？

准备面试时，先读岗位职责和组织公开信息，再从自己的真实经历里挑出能说明相关能力的材料。一个有说服力的回答可以按“背景—个人行动—结果或证据”展开。描述团队成果时，区分自己的贡献和团队工作；没有可核实的数字，就说清观察到的变化，不要编造指标、夸大权限或借用别人的故事。

面试也不是单向考试。候选人需要判断职责、团队协作、支持制度与工作方式是否适合自己，可以在回答和提问中逐步补全信息。

### 用事实组织行为题答案

**behavioral interview（行为面试）**会询问过去怎样处理具体情境。先确认问题关注的能力，再挑一个最相关的例子。回答要让听者理解发生了什么、自己为什么采取这些行动，以及结果如何被观察到。

| 部分 | 需要说明什么 | 可用提示 |
|---|---|---|
| 背景 | 目标、限制、风险和自己的职责 | 哪件事最重要？我负责哪一部分？ |
| 行动 | 自己作出的判断与执行步骤 | 我先确认什么，再做了什么？ |
| 结果 | 可核实的产出、影响或学习 | 具体观察到什么变化，怎样确认？ |

可先用一句话说明背景，再说两三项关键行动，最后交代结果和后续反思。团队成功不等于个人可以认领全部成果；说清“团队完成了什么”与“我负责哪一部分”会更可信。

### 优势、短板与技能缺口

谈优势时，选一个与岗位需求相关的能力，并提供例证。只说“我学习能力强”无法让面试官判断证据；可以说明在真实任务中如何拆解陌生知识、验证理解并应用到结果。

谈短板时，选择真实且正在改善的发展方向，交代具体练习和可观察进展。不要把“工作太认真”这类伪装成优点的答案当作诚实反思，也不要承诺没有依据的掌握日期。若缺少某项经验，可以说明目前没有在目标场景中使用过，再指出相关基础与将如何学习、验证新工具。

### 讨论紧急任务与加班安排

被问到“过去遇到紧急任务时怎么做”时，用实际发生的案例回答；被问到“如果今天临时出现紧急任务”时，再说明拟采取的判断和行动。两者都需要交代紧急程度、可用容量和风险，以及沟通与取舍：确认截止时间和影响，列出当前时间内能完成的范围，向负责人同步冲突，让相关人一起决定延后、缩小范围、增加支援或改变发布计划。

> [!example] 虚构练习场景，不是个人经历
> 假设页面要在 16:00 发布，当前还在调整次要按钮样式；15:10 时，发布前权限检查发现未授权访客可以打开页面。候选人先用授权与未授权测试账号复现问题，记录受影响页面并告知负责人；团队决定暂停样式调整，修复访问校验，再由另一人复测两种权限。复测记录显示，未授权账号被拒绝访问，授权账号仍可正常查看；团队据此恢复发布，按钮样式移到后续任务。这里用可检查的复测结果说明修复效果，没有编造效率提升比例。整个案例是虚构练习；真实回答应替换为本人实际承担的步骤与证据。

若问题是在确认“能否接受加班或值班”，则需要说明自己能承担的安排，并问清频率、轮换、紧急响应要求与补偿；这不是让候选人再讲一个行为题故事。偶发故障和长期以加班填补容量不足是不同工作条件。可以进一步询问优先级如何调整、团队如何避免事故反复发生，再判断实际要求是否合适。

### 解释为什么适合岗位

把岗位需要与自己能证明的经历对应起来，而不是复述公司口号：

1. 复述一项明确职责或目标。
2. 给出自己承担过的相近任务与具体行动。
3. 说明结果或学到的东西，并指出如何应用到目标岗位。
4. 说清为何希望做这类工作。

### 了解薪酬与岗位条件

面试前研究与岗位、资历、地点和总薪酬构成相关的当前范围。若职责和级别尚不清楚，可以先询问岗位预期与薪酬区间；若需要先给数字，则说明范围和假设，并保留讨论奖金、福利与工作条件的空间。薪酬数据会随地区、行业与时间变化，应在面试前重新核实。

### 研究公司与团队

用当前公开材料了解产品、用户、岗位所在团队和近期方向，再把自己的经历与一项具体需求相连。不要把对团队内部实践的推测说成事实；将仍未知的部分记成面试问题。

### 提前准备能帮助判断工作的提问

根据谈话中已回答的内容，选择仍未了解的问题：

- 这个岗位前几个月最重要的结果是什么？
- 工程师通常如何参与代码评审、技术决策和知识分享？
- 团队怎样安排上线、值班和紧急响应？
- 如果工作优先级冲突，谁参与排序，如何沟通取舍？
- 团队如何支持技术成长与职责发展？

结束时感谢面试官，重申一个具体的兴趣理由，并在后续流程尚未说明时询问下一步。若问题已在谈话中回答，可用剩余时间追问相关细节。

**相关背景：**[Scrum 怎样让团队检查并调整工作？](#54.%20Scrum%20%E6%80%8E%E6%A0%B7%E8%AE%A9%E5%9B%A2%E9%98%9F%E6%A3%80%E6%9F%A5%E5%B9%B6%E8%B0%83%E6%95%B4%E5%B7%A5%E4%BD%9C%EF%BC%9F)说明 Product Goal、Sprint Goal 和 Sprint Review 等团队协作用语。

> [!info]- 来源
> - [Princeton Career Development：行为题回答](https://careerdevelopment.princeton.edu/interview-guide/types-interview-questions/behavioral-or-situational)支持用情境、任务、个人行动和结果组织回答，并区分个人贡献与团队成果。本章将情境与任务合在“背景”中；权限回归案例是用于解释取舍过程的虚构练习。
