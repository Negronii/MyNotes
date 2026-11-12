# Engineering Foundations

> Generated from the [engineering-foundations reading map](../../engineering-foundations/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. 两个请求争夺最后一件库存时，怎样保证只预留一次？

**案例：** 账户 `acct-17`、主体 `user-17` 要预留 `SKU-7`，初始库存 `available = 1`。浏览器发送携带稳定操作键 `reserve-demo-208` 的 POST；请求 A 是首次尝试，B 可能是并发到达的重放。数据库必须保证不同操作不能把库存扣成负数，同一作用域键也不能提交两条预留记录。

本页的建表和并发时序以 **PostgreSQL 18 Read Committed（读已提交）**为准。复合键 `(account_id, principal_id, idempotency_key)` 标识一次逻辑操作；规范化业务参数的指纹用于识别同键请求是否仍表达同一意图。本文选定的 API 契约是：**成功提交的预留才绑定操作键；库存失败回滚且不占键；同键同指纹重放返回同一预留记录的当前状态。**这不是“逐字节重放第一次 HTTP 响应”。

### 为什么先读再无条件写会超卖？

如果两个不同操作先后 `SELECT available`，都读到 1，再按旧读数无条件写成 0，最终库存虽为 0，两个调用方却都可能得到“预留成功”。读取只是观察当时的值；它没有把“库存仍大于零”这个条件附着到之后的写入上。

把条件放进扣减语句，并把成功操作记录写在同一事务中：

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

`inventory.sku` 的主键使每个 SKU 只有一行，`CHECK` 与 `NOT NULL` 一起禁止负数和未知库存；单独的 `CHECK` 不会拒绝表达式为 `NULL` 的值。`reservations` 的复合主键使同一账户、主体和操作键最多保存一条成功结果；外键让预留指向存在的 SKU。记录在重放承诺窗口内保留，`status` 可从 `reserved` 变为 `cancelled`，但取消不会释放这个作用键或删除其历史结果。约束如何作用于所有写入方，以及索引如何服务读取，见[如何用约束保护业务规则并为读取建立索引？](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F)。

> [!info] SQL 方言边界
> `$1`、`$2` 等是 PostgreSQL 位置参数，由驱动对**每条语句分别**绑定；编号不会跨语句共享一组参数。SQLite 的参数形式另有 `?`、`?NNN` 和命名参数，不能不经方言转换就照抄。本页的并发结论也不应直接套到其他数据库。若另建 SQLite 对照表，需在每条连接启用外键；普通 SQLite 表的类型声明不等同 PostgreSQL 的强类型约束，可选用 SQLite 3.37+ 的 `STRICT` 表或适当检查。

### 条件更新怎样让两个并发请求竞争？

#### 先查操作键是快路径，不是并发裁决

API 先按当前认证得到的账户和主体授权，再规范化业务参数并计算指纹。可先查询已提交的操作记录：

~~~sql
SELECT request_fingerprint, sku, status
FROM reservations
WHERE account_id = $1
  AND principal_id = $2
  AND idempotency_key = $3;
~~~

**这条 SELECT 自己绑定三个参数：**`$1 = acct-17`、`$2 = user-17`、`$3 = reserve-demo-208`。同键同指纹返回该预留记录的**当前** `status`；同键异指纹返回冲突。若记录状态已是 `cancelled`，重放仍返回该记录的当前状态，不会重新扣库存或把它“复活”。

快查没有找到记录，只能说明本条 SELECT 的语句快照里没有**已提交且可见**的记录；原事务可能仍在执行。不能据此断言旧操作已回滚，也不能跳过后面的行锁与唯一约束。

如果快查未命中，服务在一个事务中条件扣减并插入成功操作记录。每条语句的 `$1` 都从自己的绑定开始：UPDATE 只绑定 SKU；INSERT 另行绑定作用域键、指纹和 SKU。

~~~sql
BEGIN ISOLATION LEVEL READ COMMITTED;

UPDATE inventory
SET available = available - 1
WHERE sku = $1 AND available > 0
RETURNING available;
-- UPDATE 的绑定：$1 = SKU-7。
-- 恰好返回一行才执行 INSERT；返回零行则 ROLLBACK 并跳过 INSERT。

INSERT INTO reservations
    (account_id, principal_id, idempotency_key, request_fingerprint, sku, status)
VALUES ($1, $2, $3, $4, $5, 'reserved');
-- INSERT 的绑定：$1 = acct-17，$2 = user-17，$3 = reserve-demo-208，
--               $4 = fingerprint-A，$5 = SKU-7。

COMMIT;
~~~

UPDATE 的 `RETURNING` 返回实际更新行的新值：库存从 1 扣到 0 时，它返回**一行，值为 0**；“返回零行”才表示没有可扣减的库存行。两条 SQL 的参数编号各自从 `$1` 开始，不是一个跨语句的五参数列表。

> [!info] 更新行数为什么是业务判断
> `inventory.sku` 的主键保证每个 SKU 只有一行，因此这里最多更新一行。恰好一行才表示扣减成功；零行后要在新事务按幂等契约回查。若这条 SELECT 仍未看到已提交记录，API 才能按本例契约返回这次库存失败；这只表示该语句快照当时不可见，不保证另一个事务稍后不会提交同键记录。若 UPDATE 影响多行，说明实际 schema 没有维持本例的 SKU 唯一性。

![PostgreSQL 18 Read Committed 下，SKU-7 已提交库存、A 的事务内版本、行锁等待和 B 的重检状态](../../engineering-foundations/databases/resources/database-fundamentals-inventory-row-lock.svg)

图中 A 的未提交 `available = 0` 对其他事务不可见；A 同时插入的操作记录也尚不可见。B 等待 A 持有的 SKU 行锁。A 提交时，库存 0 和 `reserve-demo-208` 记录一同可见；B 随后在新行版本上重检 `available > 0`，条件为假，UPDATE 返回零行，所以 B 不执行 INSERT。B 回滚本次尝试，再以新事务按键查记录。

如果 A 回滚，库存更改和未提交记录一起撤销。等待中的 B 重检原值 1，条件成立时可扣减、写入该作用键并提交。行锁释放不表示前一个请求成功；结果取决于事务最终提交还是回滚。

#### 零行或唯一冲突后，先回滚再开新事务查询

如果 B 的 UPDATE 返回零行，可能是 SKU 不存在或当前无库存；如果 INSERT 因复合主键冲突报错，本事务也不能保留之前的库存扣减。PostgreSQL 的普通唯一约束错误会使当前事务进入失败状态。两种路径都先结束整笔尝试，再用**另一条独立绑定的 SELECT**查询：

~~~sql
-- UPDATE 无行，或 INSERT 因唯一键报错后：
ROLLBACK;

BEGIN ISOLATION LEVEL READ COMMITTED;
SELECT request_fingerprint, sku, status
FROM reservations
WHERE account_id = $1
  AND principal_id = $2
  AND idempotency_key = $3;
-- 这条新 SELECT 独立绑定：$1 = acct-17，$2 = user-17，$3 = reserve-demo-208。
COMMIT;
~~~

这次 SELECT 的 `$1` 到 `$3` 与快查一样映射到账户、主体、键，但它是新语句、重新绑定；前面的 UPDATE/INSERT 参数不在这里延续。新事务取得新的 Read Committed 语句快照。

API 在已重新授权的作用域内比较指纹：这条新 SELECT 找到同键同指纹记录，就返回该记录的当前状态；异指纹就返回冲突。若 SELECT 仍未看到已提交记录，API 可按业务规则报告这次 SKU 不存在或已售罄。它不能据此断言并发请求之后不会提交。**失败回滚不占键**，所以完全相同的 POST 日后可在补货后成功；失败期间也没有一条“失败结果”供 API 永久重放。是否区分“不存在”和“售罄”，可通过另一次库存读取实现，但它只说明那次读取的新状态。

成功绑定的记录须在承诺的重放窗口内留存。响应未知时，浏览器重放原 POST；API 在 POST 处理过程中查记录，而不是要求浏览器调用本例未定义的“按键 GET”。窗口与重试边界见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

#### 库存仍有余量时，同一操作键由唯一约束裁决

为了单独观察唯一约束路径，下面**只把 SKU-7 初始库存从 1 改为 2**。A 与 B 仍是同一 POST：账户、主体、SKU、操作键、请求参数和 `fingerprint-A` 全相同。A 未提交前，B 的快查也看不到 A 的记录。

![SKU-7 初始库存为2时，相同请求的 B 临时扣减后因唯一键冲突整笔回滚](../../engineering-foundations/databases/resources/database-fundamentals-idempotency-unique-conflict.svg)

A 把库存从 2 改成 1，并和预留记录一起提交。B 等待行锁后基于新值 1 重检，条件仍成立，所以本事务暂时把库存从 1 改到 0。B 随后插入同一复合主键，数据库不允许第二条记录。**不能只撤销 INSERT**：那会让 B 的临时扣减留在库里。B 必须 `ROLLBACK` 整笔尝试；库存恢复为已提交的 1，A 的记录仍在。新事务读到同键同指纹的 A 记录，API 返回同一预留记录的当前状态。

这个单 SKU 时序中，两个 UPDATE 先被库存行锁串行化；B 进入 INSERT 时 A 已提交，所以这里的唯一冲突立即判定，并没有等待未提交的唯一索引插入。其他并发插入写法可能在唯一性检查时等待未提交的竞争者结束，再判定冲突。本例的安全性来自原子事务、复合主键和整笔回滚，不是“预查曾经没有记录”。

#### 同键但不同 SKU 的未提交边界

复合主键只在尝试写入 `reservations` 时裁决键冲突，并不会预先锁住所有使用该键的请求。假设 A 正在事务内预留有货的 `SKU-7`，还没提交；B 复用 `reserve-demo-208`，却改为无货的 `SKU-8`。SKU 是业务参数，因此 B 的指纹不同于 A。B 的快查看不到 A 尚未提交的记录，UPDATE 只触及 SKU-8 并返回零行；B 回滚后新事务查询时，A 的记录仍不可见。B **可以先返回无库存失败**，而 A 随后提交 SKU-7 的预留。若 B 之后再次提交 `SKU-8` 和 B 原有的其他请求参数，并继续使用 `reserve-demo-208`，快查会看到 A 的 SKU-7 记录并因指纹不同返回冲突。

| 时点 | A：`SKU-7` | B：`SKU-8`，复用同一键 | 可见性与结果 |
| --- | --- | --- | --- |
| A 尚未提交 | 事务内 `1 → 0`，操作记录未提交 | 快查没有可见记录 | B 的快查不能判断 A 已完成或已回滚 |
| B 尝试 | 仍持有 `SKU-7` 行锁 | 库存为 0，UPDATE 返回零行 | B 不碰 `SKU-7`，也没有执行 INSERT |
| B 回查 | 操作记录仍未提交 | 新事务 SELECT 仍无可见记录 | B 可以先返回无库存；A 随后仍可提交 |

这里没有承诺 B 必须等待 A，也没有承诺立即把 B 判为参数冲突，因为 B 在失败前没有尝试 INSERT，也没有占用键。如果 B 有库存并到达 INSERT，唯一约束才可能让它等待 A 的事务，然后在 A 提交后拒绝重复键；若 A 回滚，则 B 的 INSERT 可能成功。若产品要求**所有未提交的同键请求**都先裁决键与参数，需另行设计明确的占键/claim 协议；本例的最小成功记录模式不提供该承诺。

### 提交成功但响应超时，怎样认出原操作？

一次 POST 超时只说明浏览器没有收到响应。它不能单独区分请求未到服务器、数据库事务回滚、原事务仍在进行，或提交成功但 HTTP 响应丢失。以最后一种情况为例，数据库已经同时保存 `SKU-7.available = 0` 和 `(acct-17, user-17, reserve-demo-208, fingerprint-A)` 的预留记录；浏览器仍处于 unknown outcome（未知结果）。

![浏览器、API 和 PostgreSQL 间的提交、响应丢失与原 POST 重放顺序](../../engineering-foundations/databases/resources/database-fundamentals-response-loss-replay.svg)

浏览器在未知结果时重放**原 POST**，使用同一作用域键和原业务参数；本例没有按操作键查询的 GET 契约。API 重新验证当前主体权限，按账户、主体和键查持久记录并核对指纹。同键同指纹返回该预留记录的**当前状态**；若记录已取消，返回 `cancelled`，不会再次扣库存。这里承诺恢复的是同一业务记录与效果，不要求 HTTP 状态码、响应时间戳或字节表示和首次响应完全相同。RFC 9110 的幂等定义关注重复请求的预期效果；本页的记录及当前状态约定是这个 API 示例的具体契约。

若 API 查不到记录，结论仍只是“这条 SELECT 没看到已提交记录”，不能据此断定旧事务已回滚。相同 SKU 上仍由行锁、条件 UPDATE 和唯一约束决定后续结果；跨 SKU 的未提交边界见上一节，失败可先于另一事务提交返回。浏览器继续使用原 POST 与原键，不生成新键把重试伪装成第二项购买。

库存更新和操作记录必须处于同一数据库事务。如果扣减先提交、操作键之后另行写入，进程可能在两者之间崩溃；重试就无法判断是旧操作还是新购买。

这个事务只覆盖本数据库，不能同时提交远端支付或消息队列副作用。若要通知队列，应把待发指令作为 outbox 记录和本地业务效果一同提交，再由发送端重试投递；远端仍须以自己的业务键去重或核对，见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。本节的未知结果发生在 HTTP 响应交付路径；若还要承诺数据库故障后的提交持久性，需一并核对同步提交和存储 flush 配置，见[事务隔离与预写日志能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 同一库存不变量怎样用于抽奖？

抽奖服务可提供公开只读的 `GET /draws/{campaignId}`，返回活动规则、时间和可见状态；已认证参与者以 `POST /draws/{campaignId}/entries` 提交请求。服务先验证当前主体权限，再按 `(campaign_id, principal_id, idempotency_key)` 查该操作：同键同指纹且已有参与结果时，返回已保存的抽取结果和当前领奖状态，即使活动已关闭；同键异指纹返回冲突。只有该查询未看到已提交操作记录，才检查活动是否开放和参与资格，再尝试建立新参与记录。参与表必须有 `UNIQUE (campaign_id, principal_id)`，让同一参与者即使用不同操作键并发提交，也只能有一个参与结果。活动关闭要返回明确的 `campaign-closed` 状态。

若写参与记录时唯一约束冲突，先回滚本次事务并在新事务按同一 `(campaign_id, principal_id, idempotency_key)` 重新查询：查到同键同指纹已提交结果，说明这是同一 POST 的并发重放，应返回该结果；查到同键异指纹则返回操作键冲突；仍未看到该操作键时，才把 `(campaign_id, principal_id)` 冲突处理为“已经参与”，不把换键重试当作同一抽奖结果。这样既能恢复并发同键请求的已提交结果，也由唯一约束裁决换键重复参与。其他规则冲突应返回明确状态，不让浏览器从通用错误猜测结果。

本例把“报名已接受但奖品库存为零”定义为已完成的未中奖结果：服务在同一事务保存参与记录和权威 `no-prize` 结果，之后同键重放仍取回该结果，不会重新抽一次。如果某活动把库存不足定义为拒绝报名，则那次尝试不保存完成结果、不占键；活动规则必须选择其中一种语义。有限奖品的扣减与参与、中奖结果、待领取状态仍需同事务提交。随机性与审计须符合活动承诺；统计事件不能决定资格或权威中奖结果。抽奖操作记录也要在约定的重放窗口内保留。

`GET /draws/{campaignId}/entries/{entryId}` 只向当前结果所有者返回本人结果与领取状态。独立的 `POST /prizes/{prizeId}/claims` 再验证中奖记录所有者，只收集履约所需资料并写入履约状态；后台活动管理权限应比公开读取和本人参与更严格。旧档案保留导航入口，见[归档抽奖 API 规则入口](../../archive/front-end/Deprecated_Interview_Notes/prize-draw-api-invariants.md)。

**接下来：** 本页解释原子库存写入、操作结果和局部事务边界。NULL、连接与分组改变报表查询的方式见[SQL 空值、连接与分组会怎样改变报表 42 的结果？](#7.%20SQL%20%E7%A9%BA%E5%80%BC%E3%80%81%E8%BF%9E%E6%8E%A5%E4%B8%8E%E5%88%86%E7%BB%84%E4%BC%9A%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E6%8A%A5%E8%A1%A8%2042%20%E7%9A%84%E7%BB%93%E6%9E%9C%EF%BC%9F)；隔离级别、WAL 和崩溃恢复见[事务隔离与预写日志能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - Read Committed 的语句快照、并发 `UPDATE` 等待以及在提交的新行上重检 `WHERE`；前一个更新者回滚时后一个可以继续：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1，核对于 2026-11-11。
> - `UPDATE ... RETURNING` 只返回实际更新行的新值；位置参数在各个预备语句内绑定：[PostgreSQL 18, UPDATE](https://www.postgresql.org/docs/18/sql-update.html)，§UPDATE；[PREPARE](https://www.postgresql.org/docs/18/sql-prepare.html)，§PREPARE，核对于 2026-11-11。
> - 主键、唯一、外键、CHECK 与 NOT NULL 的约束行为：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)，§5.5.1–5.5.5，核对于 2026-11-11。
> - 事务把多步写入作为一个全有或全无的边界、提交时一同可见、回滚撤销；错误后须回滚到保存点或结束失败事务：[PostgreSQL 18, Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html)，§3.4；[ROLLBACK](https://www.postgresql.org/docs/18/sql-rollback.html)，核对于 2026-11-11。
> - 竞争插入同一唯一键时等待并根据另一事务提交或回滚裁决：[PostgreSQL 18, INSERT](https://www.postgresql.org/docs/18/sql-insert.html)，§INSERT；[Index Uniqueness Checks](https://www.postgresql.org/docs/18/index-unique-checks.html)，§63.5，核对于 2026-11-11。本页单 SKU 时序展示行锁先串行化、插入时胜者已提交的具体路径。
> - 幂等方法重复请求的预期效果应等同于单次请求：[RFC 9110, §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)，核对于 2026-11-11。RFC 不规定本例响应序列化或取消后的当前状态；这些是上文声明的 API 契约。
> - SQLite 外键默认关闭、须由应用启用；动态类型、`STRICT` 表及参数语法：[SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html)，§1–2；[STRICT Tables](https://www.sqlite.org/stricttables.html)，§1–2；[SQL Language Expressions](https://www.sqlite.org/lang_expr.html)，§4 Parameters，核对于 2026-11-11。
## 2. 浏览器请求如何到达 HTTP 响应？

**案例背景。** 查看者已登录，并获准读取报表 42。浏览器先前收到版本 8 的 JavaScript Object Notation (JSON，JavaScript 对象表示法) 表示，以及 Entity Tag (ETag，实体标签) 验证值 `"report-42-v8"`；浏览器把正文和 ETag 一并存入私有 HTTP 缓存。页面脚本再次读取报表时，以浏览器 Fetch API（网页请求接口）的默认缓存模式调用 `fetch()`，需要在仍有权限时看到当前版本。缓存可以跳过不必要的网络传输，但不能替服务端决定这次是否仍有权读取。

本章跟着 `https://reports.example` 上这次读取走完请求、服务端判断和页面取得结果。Hypertext Transfer Protocol (HTTP，超文本传输协议) 规定方法、目标资源、状态和表示的含义；HTTP/1.1、HTTP/2、HTTP/3 用不同线格式和连接承载这些语义。先看本例需要访问网络的路径，上排向服务端发送请求，下排把结果交回页面。

![报表读取从页面请求到可交付响应的路径](../../engineering-foundations/networking/resources/http-request-route.svg)

图只画本例的网络路径：假设 Service Worker（服务工作线程）继续转发，页面脚本没有手写条件字段；浏览器按 Cookie 策略附加会话凭据，并由 HTTP 缓存根据已存 ETag 自动加入验证字段。服务端必须先检查当前身份与报表权限，再判断表示是否变化。线上 `304` 经浏览器缓存更新后，页面通常收到原 `200` 状态和已存正文；线上 `200` 交付新正文；拒绝时页面进入错误分支，不拿旧正文冒充成功。若 Service Worker 自己合成响应，该响应遵循应用自己的授权与缓存策略。键匹配且策略允许直接复用的新鲜响应可以跳过网络；某些指令或配置也允许复用特定过期响应，但不适用于本例的 `no-cache` 路径。

### 浏览器把报表请求表达成什么？

Uniform Resource Identifier (URI，统一资源标识符) 标识目标资源，方法说明调用方希望对资源执行什么操作。请求还可带查询参数、字段和内容；响应带状态码、字段及可选内容。服务端返回的 representation（表示）是面向该请求选定的媒体类型、语言等形式，不一定等同于数据库里的一行记录。

下面用 HTTP/1.1 可读文本展示缓存自动生成的验证请求。页面表达普通 GET，并选择 JSON 与语言偏好；浏览器按 Cookie 策略附上 Cookie，而 HTTP 缓存从已存 ETag 生成 `If-None-Match`。网页脚本不能任意手设 `Cookie` 字段。HTTP/2 和 HTTP/3 传输同样的语义，但线上不会使用这段逐行文本。

~~~http
GET /api/reports/42 HTTP/1.1
Host: reports.example
Accept: application/json
Accept-Language: zh-CN, en;q=0.8
Cookie: __Host-session=<opaque-session-id>
If-None-Match: "report-42-v8"
~~~

此前保存的响应节选可以是下面这样。为明确持久连接中的正文边界，`Content-Length` 是所示 JSON UTF-8 字节数（不计代码块排版换行）；示例省略 `Date` 等不影响这里讨论的字段。

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Language: zh-CN
Content-Length: 63
ETag: "report-42-v8"
Cache-Control: private, no-cache
Vary: Accept-Language

{"id":42,"title":"Service health","status":"ready","version":8}
~~~

若当前权限仍允许读取、表示没有变化，网络上可以只出现下面这个无正文的验证响应节选。完整响应还包含源站时钟可用时要求发送的 `Date` 字段：

~~~http
HTTP/1.1 304 Not Modified
ETag: "report-42-v8"
Cache-Control: private, no-cache
Vary: Accept-Language
~~~

`Accept` 表示调用方能处理或偏好的响应媒体类型；`Content-Type` 说明消息内容是什么媒体类型；`Accept-Encoding` 表示调用方支持的内容编码，`Content-Encoding` 说明表示是否经过 `gzip`、`br` 等压缩，解码后仍得到该媒体类型。`Accept-Language` 表达语言偏好，`Content-Language` 标记该表示面向的自然语言；服务器可以没有首选语言的版本。`Vary: Accept-Language` 告诉缓存只有在语言请求字段匹配时才能复用这个表示。若请求有正文，`Content-Type` 描述的是该请求正文，而不是整个 HTTP 消息。

请求凭据与资源授权是另一条线：Cookie 或 `Authorization` 可以提供认证信息，application programming interface (API，应用程序接口) 仍须根据当前主体、租户和资源检查授权。跨源读取也由浏览器的 Cross-Origin Resource Sharing (CORS，跨源资源共享) 规则控制；某些跨源请求会先发 `OPTIONS` 预检。允许浏览器脚本读取响应不等于允许该用户读取报表，详见[浏览器安全控制分别保护什么信任边界？](#6.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AE%89%E5%85%A8%E6%8E%A7%E5%88%B6%E5%88%86%E5%88%AB%E4%BF%9D%E6%8A%A4%E4%BB%80%E4%B9%88%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C%EF%BC%9F)。

safe method（安全方法）表示调用方预期只读取、不改变目标资源状态；服务端仍可能记录访问日志等附带效果。idempotent method（幂等方法）表示把同一请求重复应用多次，其预期服务器效果与应用一次相同，而不要求每次响应相同。例如第一次 DELETE 可以回 204，第二次回 404，资源最终仍不存在。GET 和 HEAD 既安全又幂等；PUT 和 DELETE 幂等但不安全。PATCH 是否幂等由补丁操作和 API 契约决定，POST 默认不保证幂等。PUT 正文描述成功后目标资源应呈现的状态，不必然表示未提交字段要被清空。方法语义不能确认连接中断前的业务副作用是否已提交；未知结果要用稳定的业务请求标识确认，见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info] HTTP 方法与 REST 不是一回事
> Representational State Transfer (REST，表述性状态转移) 是一组架构约束，包括客户端与服务端分离、无状态交互、可缓存、统一接口和分层系统；代码按需下发是可选约束。统一接口还要求以资源标识目标、用表示操纵资源、自描述消息以及超媒体控制。用 HTTP 方法和 JSON 不会自动满足全部约束；要称为 REST 风格，还要检查这些约束是否成立。

### 缓存何时直接交付，何时要问源站？

HTTP 缓存按响应的可缓存性、缓存键和新鲜度判断能否复用。`max-age=60` 表示响应只有在当前年龄小于 60 秒时才新鲜；年龄正好达到 60 秒时已经不新鲜。按默认缓存规则，符合缓存键且策略允许直接复用的新鲜响应可以不问源站；有些指令或配置也会明确允许特定过期响应被使用，因此“已经过期”与“绝不送出”不是同一判断。本例的 `no-cache` 要求每次复用前验证。`private` 禁止共享缓存存储，却允许浏览器一类的私有缓存存储；它既不是用户间授权隔离，也不能保证内容保密。缓存通常按请求方法和目标 URI 区分表示，响应中的 `Vary` 再列出决定表示的请求字段，例如语言或编码偏好。缓存键和验证值必须覆盖 API 实际协商的表示范围，不能把它们当作对象权限检查。

`no-cache` 容许缓存保存响应，但禁止未验证就拿它满足后续请求；它不是“不要保存”。`no-store` 要求缓存不要存储这次请求或响应的内容，但也不能单独作为隐私保证。如果 `private, max-age=60` 的新鲜窗口内撤销了访问权限，浏览器仍可能在窗口结束前交付旧正文。若每次重用前都要重新确认访问权，应选择 revalidation（重新验证）策略；对敏感内容也可禁用存储。无论采取哪种缓存策略，API 的授权检查仍是最终边界；[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)继续说明逐次检查。

本例响应采用 `private, no-cache`，因此保存的响应每次复用前都要重新验证。默认 `fetch()` 缓存模式下，页面发普通 GET，HTTP 缓存在网络请求中自动附上已存的 `If-None-Match: "report-42-v8"`。服务器先确认请求者仍可读报表 42，再判断被选中的表示是否仍匹配这个 ETag。若权限已撤销，服务器按隐私政策回 `403` 或隐藏式 `404`；缓存不能用旧成功正文绕过授权。若权限有效且表示未变，网络回无正文的 `304 Not Modified` 和更新缓存所需的字段；缓存更新存储响应后，把存储的 `200` 与原正文交给页面。若表示已变，网络和页面都得到带新正文与新 ETag 的 `200`。

页面脚本若自己在默认缓存模式的请求字段中加入 `If-None-Match`，Fetch 会把缓存模式改为 `no-store`；这不是上面的自动重验证路径。此时网络 `304` 可以作为页面所见的 `304`，`response.ok` 为 `false`，也没有旧缓存正文自动拼回页面。通常应让浏览器缓存管理验证；只有应用明确要自己管理条件请求和 `304` 时，才手动设置验证字段。ETag 应针对被选中的表示生成；语言或媒体类型不同的版本要与 `Vary` 和验证逻辑保持一致。

### 请求何时需要 DNS、TCP、TLS 或 QUIC？

页面的请求先经过浏览器控制：Service Worker 可以根据自己的脚本响应或继续执行 `fetch`；之后由 HTTP 缓存决定可否复用、是否需要验证，或是否转向网络。Service Worker 缓存、浏览器 HTTP 缓存、域名地址缓存和连接池是不同的存储或快路径：命中其中之一不意味着其余几层也被命中。本文按 Service Worker 转发的路径讲解；若 Worker 自行合成响应，应用要自行保证它没有把已撤权用户的旧私有数据交付出去。Fetch 标准也将网络缓存和连接获取分开规定。

若需访问网络，浏览器会先找能服务该来源且仍可用的连接。已有连接能复用时，不必为每个请求重新解析域名或握手。缺少连接时，浏览器或系统解析器会检查 Domain Name System (DNS，域名系统) 地址缓存；没有仍有效的记录才向递归解析器查询，解析器也可能直接从缓存回答，或沿 DNS 委派逐级查询。资源记录中的 time to live (TTL，生存时间) 限定缓存保留期限；负缓存也可能暂存“名称不存在”的结果。因此连接关闭后地址仍可能可用，而 DNS 记录过期也不一定要求关闭现有连接。

Transmission Control Protocol (TCP，传输控制协议) 为应用提供有序可靠字节流；HTTPS 用 Transport Layer Security (TLS，传输层安全协议) 保护连接。QUIC 则在 User Datagram Protocol (UDP，用户数据报协议) 上提供多路复用的可靠流，并集成 TLS。它们不会替 API 验证用户身份或逐次授权资源，也不能确认超时的业务操作是否已经提交。域名解析或连接准备可能早于本次请求发生；HTTP/1.1 也可以承载明文 HTTP。

若新连接使用 TCP，常见建连过程是客户端发 SYN（synchronize，同步初始序号），服务端回 SYN-ACK（确认请求并给出自己的初始序号），客户端再以 ACK（acknowledgment，确认）收尾；TCP 给应用有序、可靠的字节流，但不会保留一次写入对应一次读取的消息边界。所谓“粘包”通常是把字节流误当消息队列；应用协议仍需用长度、分隔符或其他规则划分消息。连接关闭时，TCP 两个方向可以分别结束；一方向已关闭后，另一方向仍可发送数据，因此常见 FIN（结束标志）/ACK 关闭图示不表示每次都有固定四个独立报文。随后 HTTPS 上的 TLS 握手协商密钥并验证服务端证书中的服务身份是否与访问名称相符。QUIC 则在 UDP 上建立自己的连接和可靠流，并把 TLS 1.3 密钥协商纳入传输建连，不执行 TCP 三次握手。证书验证失败或连接失败属于传输/安全层失败，不是 API 返回了 500。

浏览器与服务端还要确定使用的 HTTP 版本。HTTPS 上的 HTTP/2 通过 TLS 的 Application-Layer Protocol Negotiation (ALPN，应用层协议协商) 识别 `h2`；HTTP/3 端点可由 `Alt-Svc` 等方式发现，浏览器随后尝试 QUIC。若网络阻断 UDP，客户端应尝试 TCP 承载的 HTTP 版本。成功复用连接时，本次请求跳过了新的地址解析和建连；没有复用时，协议协商才是新连接路径的一部分。

TLS 1.3 的恢复连接可以选择发送 zero round-trip time (0-RTT，零往返时间) early data（早期数据），在握手完成前把请求送出。早期数据可能被攻击者重放；HTTP 规则允许客户端在没有额外信息时把安全方法放进早期数据，并禁止发送不安全或安全性未知的方法。服务端仍要按资源判断是否可以安全地提前处理；可延迟处理、部署防重放措施，或在不愿承担重放风险时返回 `425 Too Early`（过早请求）。安全方法本身也可能触发附带效果，所以涉及不可重复业务副作用的接口还须有应用层重放防护和去重。恢复连接也不能保证业务操作只执行一次。

> [!info] 资源提示能提前准备什么？
> `preload` 提示浏览器尽早取得当前页面已确定会用的关键资源；`prefetch` 提示可以低优先级准备可能在后续导航使用的资源；`preconnect` 可以提前解析可信来源并准备连接；`dns-prefetch` 只提前查询来源的域名。浏览器会按实现与当前资源条件处理提示，并不保证照单全收。连接提示会占用连接与网络资源，适合确实很快要访问的来源。
>
> ~~~html
> <link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>
> <link rel="prefetch" href="/next-page.js">
> <link rel="preconnect" href="https://reports-cdn.example">
> <link rel="dns-prefetch" href="//reports-cdn.example">
> ~~~

### HTTP/1.1、HTTP/2 与 HTTP/3 怎样承载同一语义？

三个版本都能表达本例的 GET、目标 URI、协商字段和响应状态，但线上帧、连接并发与丢包等待不同。HTTP/1.1 用文本起始行和字段；消息是否含正文及边界由方法、状态、`Content-Length`、分块传输编码或连接结束等规则确定，正文自身可以是二进制。持久连接可复用，但它没有 HTTP 流多路复用层。它允许流水线发送多个请求，而服务器仍须按请求顺序返回对应响应，所以前一响应慢会令后一响应等待；客户端也可用多条连接并发请求。持久连接只复用请求与响应的通道，不表示服务端可以在没有请求时凭空推送 HTTP 响应。

HTTP/2 将字段块和内容装进二进制 `HEADERS`、`DATA` 等帧，并以流 ID 区分并发的请求/响应；HPACK 压缩字段块。帧可在同一 TCP 连接中交错，应用层不必等前一个响应完整结束才处理另一个流。HTTP/2 另有逐流和连接级流量控制；可发送额度耗尽时，相应的数据发送会等待补充额度。可是 TCP 仍要求按字节序交付：较早的 TCP 段丢失时，后续字节即使已抵达，也要等缺口重传，可能让该连接上的多个 HTTP/2 流一起停住。

HTTP/3 保持同一 HTTP 语义，将帧放到 QUIC 流上，并以 QPACK 压缩字段块。QUIC 对每条流实施 flow control（流量控制），连接总量也有额度；congestion control（拥塞控制）与网络资源则由连接共享。若图片流有缺口，而报表流的正文、字段和相关 QPACK 动态表项都已到达，图片流的缺口不会阻止报表流的数据被处理；要把报表响应视为完整，还必须收到其 QUIC 流发送方向结束的 FIN。连接级拥塞和流控会限制尚未发送的数据，不会让已经到达的报表字节重新等待；报表流自身有缺口或所需 QPACK 表项未到时，也不能完成响应。因此 HTTP/3 缓解了跨流队头阻塞，并不消除共享网络瓶颈。

**同样的 `GET /api/reports/42 → 200 + JSON`，线上怎样承载？**

![HTTP 语义、版本帧和传输承载的对应关系](../../engineering-foundations/networking/resources/http-version-layers.svg)

三行使用的输入与结果固定为 `GET /api/reports/42 → 200 + JSON`，只换版本怎样编码和调度它。HTTP 版本决定帧和流如何承载语义；`Content-Encoding: br` 一类表示压缩是另一层概念，不能与 HTTP/1.1 的分块传输或 HTTP/2、HTTP/3 的帧混为一谈。

**同一连接丢失一段数据，哪些流需要等待？**

![一段数据丢失时 HTTP/2 与 HTTP/3 的交付差别](../../engineering-foundations/networking/resources/http-head-of-line.svg)

在 HTTP/2 示例里，报告和图片的帧混在同一个 TCP 字节流；中间一段 TCP 数据丢失时，TCP 不会把其后的帧字节先交给 HTTP/2。HTTP/3 的图则假设报表响应流（包括结束方向的 FIN）已完整到达、所需字段可解码，而图片流有缺口；此时不再等待图片流，也不需要额外流控额度来交付已收到的报表字节。HTTP/1.1 的流水线等待发生在应用协议的响应顺序；HTTP/2 的跨流等待来自共享 TCP 的传输顺序；两种等待是不同层次的 head-of-line blocking（队头阻塞，HOL）。

在 HTTP/1.1 中，`Transfer-Encoding: chunked` 是消息分帧方式；`Content-Encoding: gzip` 描述表示本身的编码，解码前后媒体类型相同。HTTP/2 和 HTTP/3 用 DATA 等帧分段消息，帧自身不一定表示响应结束：HTTP/2 由最后一个 `HEADERS` 或 `DATA` 帧上的 `END_STREAM` 标志结束响应；HTTP/3 在服务端发送完最终响应后，由 QUIC 流发送方向结束（FIN）表明最终消息结束。它们不使用 HTTP/1.1 的 transfer-coding 字段。TCP 或 QUIC 给出的底层字节流/流边界也不是 WebSocket（可持续双向消息通道）、Server-Sent Events (SSE，服务器发送事件) 等应用消息的全部边界；应用协议仍要解释自己的帧、分隔符或事件。

### 服务端返回了什么，页面何时才能使用？

服务端路由请求后，先完成身份验证和报表级授权，再读取或修改资源并选择状态与表示。状态码只描述这次 HTTP 请求的处理结果类别，不描述整个业务生命周期，也不代表正文已完整到达。

| 响应与常见含义 | 需要留意 |
| --- | --- |
| **`1xx`**：继续处理的中间信息，如 `100 Continue` | 不是最终结果 |
| **`2xx`**：`200` 返回当前表示；`201` 已创建；`202` 已接受异步处理 | `202` 不表示报表作业已完成 |
| **`3xx`**：`304` 表示条件读取可复用此前存储的表示 | 304 无正文，只用于适用的条件 GET/HEAD |
| **`4xx`**：`400` 请求格式无效；`401` 缺少或无效凭据；`403` 拒绝；`404` 不存在或按策略隐藏；`409` 冲突；`429` 请求过多 | `401` 响应须给出适用的 `WWW-Authenticate` 认证质询 |
| **`5xx`**：`500` 未预期的服务端错误；`502` 上游响应无效；`503` 暂时不能处理；`504` 网关等待上游超时 | 这些是服务端或网关响应；客户端自己的等待超时没有 HTTP 状态码 |

浏览器 `fetch()` 收到 HTTP 响应后，即使状态是 `404` 或 `500`，也会兑现 Promise（异步承诺对象）；页面要检查 `response.ok` 或 `status`。在浏览器 HTTP 缓存自动重验证时，网络 `304` 已先被缓存层转换为存储的响应，所以页面看到 `200` 与原正文；若页面手动设置条件字段，线上 `304` 则可能作为页面的 `304`，`response.ok` 为 `false`，没有自动拼回的正文。响应头到达不代表正文读取完毕，`response.json()` 或流读取仍可能因连接中断、内容解码失败而拒绝；字节读完后，JSON 语法错误也会让解析失败。Axios 默认按 `validateStatus` 判断非 2xx 是否进入错误分支，HTTP 错误响应通常可从错误对象取得；设置 `validateStatus` 会改变此规则。XMLHttpRequest（浏览器传统异步请求 API）的 `load` 表示请求成功完成，`error` 表示传输失败，`timeout` 与 `abort` 表示各自的中止路径；`load` 不表示状态码是 2xx，仍要检查 `status`。需要上传进度时也仍可使用其上传事件。Axios 实例如何限定凭据、取消过期请求并校验运行时 JSON，见[Axios 如何连接 React 报表界面的 HTTP 请求？](../../archive/front-end/0-1_Learning_Notes/react_typescript/axios-in-react.md)。浏览器 API、客户端库和协议的错误边界不要互相代替。

**接下来：** 若报表页面要连续接收更新，还需决定消息方向、事件边界及断线恢复方式，见[何时选择轮询、SSE、流式 Fetch 或 WebSocket？](#19.%20%E4%BD%95%E6%97%B6%E9%80%89%E6%8B%A9%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)。实时通道同样要让每次连接重新授权，并且明确“重连”是否补齐中断期间的业务事件。

> [!info]- 来源
>
> - HTTP 通用语义、表示、字段、方法、安全性/幂等性、条件请求、状态码、CORS 外的协议边界：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§3、§6–§10、§11–§13、§15，2022-06；`401` 认证质询见 §11.3；核对于 2026-11-12。
>
> - 缓存键、`Vary`、新鲜度、`max-age`、`private`、`no-cache`、`no-store` 和条件验证：[IETF RFC 9111, HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)，§3–§5，2022-06；核对于 2026-11-12。
>
> - HTTP/1.1 消息语法、正文定界、持久连接和流水线：[IETF RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html)，§2、§6、§9，2022-06；HTTP/2 流、帧和 TCP 队头阻塞：[IETF RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html)，§1、§3–§6，2022-06；HTTP/3 与 QUIC 的映射和按流可靠交付：[IETF RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)，§1–§4，2022-06；均核对于 2026-11-12。
>
> - HTTP/2 字段压缩：[IETF RFC 7541, HPACK](https://www.rfc-editor.org/rfc/rfc7541.html)，§1–§2，2015-05；HTTP/3 字段压缩、动态表阻塞：[IETF RFC 9204, QPACK](https://www.rfc-editor.org/rfc/rfc9204.html)，§1–§2.1.2，2022-06；均核对于 2026-11-12。
>
> - TCP 连接建立、字节流和半关闭：[IETF RFC 9293, Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc9293.html)，§3、§3.5–§3.6.1，2022-08；QUIC 流与流量控制：[IETF RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)，§2–§4，2021-05；连接级拥塞控制：[IETF RFC 9002](https://www.rfc-editor.org/rfc/rfc9002.html)，§7，2021-05；QUIC 中的 TLS：[IETF RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html)，§4–§5，2021-05。TLS 1.3 现行版本与早期数据重放边界：[IETF RFC 9846, TLS 1.3](https://www.rfc-editor.org/info/rfc9846/)，2026-07，§1.2、§2、§8；HTTP 早期数据与 `425 Too Early`：[IETF RFC 8470](https://www.rfc-editor.org/rfc/rfc8470.html)，§2–§5，2018-09。均核对于 2026-11-12。
>
> - TLS 服务身份与访问名称匹配：[IETF RFC 9525](https://www.rfc-editor.org/rfc/rfc9525.html)，§1、§6，2023-11；DNS 委派和解析器缓存：[IETF RFC 1034](https://www.rfc-editor.org/rfc/rfc1034.html)，§4–§5，1987-11；DNS 负缓存：[IETF RFC 2308](https://www.rfc-editor.org/rfc/rfc2308.html)，§3–§5，1998-03。均核对于 2026-11-12。
>
> - Fetch 请求、连接获取、响应与 CORS：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，Living Standard，最后更新 2026-10-19，核对于 2026-11-12；XMLHttpRequest 事件与上传接口：[WHATWG XMLHttpRequest Standard](https://xhr.spec.whatwg.org/)，Living Standard，最后更新 2026-11-11，核对于 2026-11-12；Axios 的非 2xx 错误与 `validateStatus`：[Axios Error Handling](https://axios-http.com/docs/handling_errors)，当前文档核对于 2026-11-12。
>
> - 429 Too Many Requests 状态：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，§4，2012-04；资源提示类型：[WHATWG HTML Living Standard, Link types](https://html.spec.whatwg.org/multipage/links.html#linkTypes)，§4.6.8.5、§4.6.8.18–§4.6.8.20，核对于 2026-11-12。
>
> - REST 约束：[Roy T. Fielding, Architectural Styles and the Design of Network-based Software Architectures](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，第 5 章，2000。
## 3. 如何设计可预期的 HTTP API 契约？

API 契约说明调用方怎样构造请求、怎样识别成功和失败、怎样继续读取集合。HTTP 提供通用方法和状态语义；API 定义领域输入、返回结构、错误类别、分页规则与兼容政策。文档、类型注解、OpenAPI 描述和运行中的实现是不同层：写出 schema（结构模式）不证明已部署行为符合它。

**案例：** 浏览器向独立教学源站 `api-contracts.example` 请求 `GET /api/reports/42`。这个合成报表与网络协议章的 `reports.example` 报表不是同一个资源；编号、正文和 ETag 也彼此独立。报表存在且当前主体获准读取时，API 返回稳定 JSON；编号格式错误、报表不存在、认证缺失或访问被拒，各有调用方能识别的结果。列表按 ID 排序并显式给出下一页游标。正文还用同一独立 API 说明带 ETag 的编辑与 201/202 的后续状态。

示例域名、报表标识、内容和响应值都是教学数据；应用层政策会在正文中单独标明。

> **HTTP 片段约定：** 所有 `~~~http` 块只展示本段要讨论的字段，不是可直接发送的完整 HTTP/1.1 报文。主流程假定调用方带有有效凭据；为聚焦 API 契约，片段省略凭据，有些也省略 `Host`。带正文的请求片段没有展示 `Content-Length` 或 `Transfer-Encoding` 分帧字段；实际 HTTP/1.1 请求必须带 `Host`，并按正文长度正确分帧。

~~~http
GET /api/reports/42 HTTP/1.1
Host: api-contracts.example
Accept: application/json, application/problem+json
~~~

一个合法的成功表示是：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "api-contracts-report-42-v7"

{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

本章的详情表示要求 `id`、`title` 和 `delivery`；可选 `note` 在无值时省略，不以 JSON `null` 表示。集合项和 201 创建响应是摘要表示，包含 `id`、`title`、`status`，不包含详情中的 `delivery` 和 `note`。这些是本 API 明确的两个 JSON 形状。

路径里的 `42` 是 API 的资源标识，不是访问授权。每个请求都要由可信凭据确定当前主体，再检查其对租户和对象的权限，之后才读取或修改资源。本端点先认证，再做租户范围内的对象可见性检查；不存在和不可见统一返回 404。资源归属见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

### 错误契约怎样保留机器可判定的含义？

API 可以用 RFC 9457 Problem Details 表示错误，媒体类型为 `application/problem+json`。例如 ID 不存在或按隐私政策不可见时返回统一错误：

~~~http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{"type":"https://api-contracts.example/problems/not-found","title":"Report not found","status":404,"detail":"No report is visible under this identifier."}
~~~

客户端可依赖稳定的 `type` 或扩展错误码，而不应解析供人阅读的 `title`、`detail`。若正文含 `status`，它须与实际 HTTP 状态相同。不要回显秘密、内部异常栈或 SQL 文本。

本端点先验证认证凭据；因此未认证请求即使带非数字报表 ID 也返回 401。对象可见性按租户范围检查；报表不存在和主体无权读取都返回同一个 404 `type` 与中性详情。本端点选择隐藏式 404，不返回 403。其他允许披露资源存在的端点，可以用 403 表示已识别身份但拒绝访问。对处理请求正文之前就能确定的失败（例如未认证或对象不可见），先返回该失败；隐藏对象带陈旧标签仍为 404，不用 412 暗示对象存在。RFC 9110 的条件请求优先级说的是这类无需处理正文即可确定的失败，不表示所有字段级领域验证都必须先于 `If-Match`。已认证且对象可见时，不支持的媒体类型也在读取正文前确定，所以它与过时标签同时出现时先返回 415；缺少 `If-Match` 时也先处理此媒体类型失败。

| 条件 | 本例的结果 | 补充约定 |
| --- | --- | --- |
| 报表 42 存在、身份和资源权限都通过 | 200 + JSON | 定义成功表示中的稳定字段 |
| 缺少有效凭据，即使报表 ID 不是整数 | 401 + Problem Details | 先认证，再做报表 ID 的数字转换；发出 401 时提供适用的 `WWW-Authenticate` challenge，例如 `Bearer realm="reports"` |
| 报表不存在，或主体无权读取；即使带陈旧 `If-Match` | 404 + Problem Details | 本端点一律隐藏对象；两种情况使用相同 `type` 和中性详情，且在 `If-Match` 前返回 |
| JSON 语法无效，例如正文 `{` | 400 + Problem Details | 指明内容无法解析 |
| `Content-Type` 不受端点支持，例如 PATCH 未声明的补丁格式 | 415 + Problem Details | PATCH 资源在 OPTIONS 响应中用 `Accept-Patch` 公布补丁媒体类型；创建 fixture 只接受 `application/json` |
| 认证和语法解析通过后，字段值、路径 ID 或范围不符合本 API 契约 | 422 + Problem Details | 指出字段路径和稳定错误代码；本例把非整数路径 ID 选为 422 |
| 与当前状态冲突，例如重复标题 | 409 + Problem Details | 告诉调用方怎样刷新或解决冲突 |
| 单个 `If-Match` 标签是弱标签（例如 `W/"api-contracts-report-42-v7"`），或强标签不匹配 | 412 + Problem Details | RFC 要求强比较；不应用补丁，客户端读取当前表示并比较本地草稿 |
| `If-Match` 语法错误，或合法的 `*` / 标签列表被本端点拒绝 | 400 + Problem Details | HTTP 允许 `*` 和列表；本端点的单标签限制是应用政策。单个弱标签语法合法，不能归入此 400 分支 |
| 缺少本端点要求的 `If-Match` | 428 + Problem Details | 应用政策要求前置条件；RFC 6585 规定 428 响应不得被缓存 |
| 超过适用调用额度 | 429 + Problem Details | 定义额度作用域和可重试时机；确定时可附 `Retry-After`，且 429 响应不得被缓存 |
| 报表 999 不存在或被隐藏 | 404 + Problem Details | 与成功表示结构不同 |
| 服务暂时不可用，或发生未预期的服务端错误 | 503 或 500 + Problem Details | 只给稳定的机器类别，不回显栈或 SQL；写入结果未知时按幂等契约查询或恢复，不盲目重放 |

这是本 API 的映射政策，不是所有服务都必须采用的唯一表。`422 Unprocessable Content` 表示内容语法可理解但指令不能处理；本例把畸形 JSON 归为 400，把 JSON 可解析但字段不合规、以及非整数路径 ID 映射为 422。路径 ID 的状态码是本 API 额外约定。未认证和不可见对象是处理正文前即可确定的失败；其余字段解析、业务校验和条件请求的顺序由该端点实现定义，RFC 不要求把所有领域校验都放在 `If-Match` 之前。数据库并发不变量仍由原子写入负责。

### 如何用条件 PATCH 防止覆盖别人更新？

本例的编辑端点只返回一种规范 JSON 表示，而且任一可见字段变更都会推进资源版本，因此它可以用 `"api-contracts-report-42-v7"` 标记该表示。强 ETag（实体标签）必须随它所标记的表示数据变化；若内容协商或内容编码产生字节不同的表示，服务须给每种表示生成可区分的强标签，并让每个标签映射到用于原子写入检查的资源版本。压缩与未压缩表示不能共用同一个强标签。下面先读取唯一的 JSON 表示：

~~~http
GET /api/reports/42 HTTP/1.1
Host: api-contracts.example
Accept: application/json
~~~

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "api-contracts-report-42-v7"

{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

之后用户把交付方式切为下载，并删除可选备注。此资源只接受 JSON Merge Patch（JSON 合并补丁），所以请求声明媒体类型 `application/merge-patch+json`，并带上刚读到的强 ETag：

~~~http
PATCH /api/reports/42 HTTP/1.1
Host: api-contracts.example
Content-Type: application/merge-patch+json
If-Match: "api-contracts-report-42-v7"

{"delivery":{"channel":"download"},"note":null}
~~~

Merge Patch 的对象成员按名称递归合并：未出现的成员保持，`null` 表示删除成员，数组整体替换。应用补丁后的中间表示仍有旧 `recipients`，因为该成员在补丁里被省略；本合成 API 另规定下载模式不保存收件人字段，业务规范化随后移除它，并验证最终表示。若 `channel` 是 `email`，最终表示必须含至少一个合法收件人；不合法的最终文档整笔拒绝。Merge Patch 里的 `null` 不能同时表示“字段存在且值为空”；若资源必须保留显式 JSON null，应为该字段另定表示或选择别的补丁格式。

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "api-contracts-report-42-v8"

{"id":42,"title":"Monthly summary","delivery":{"channel":"download"}}
~~~

表单只序列化当前模式字段：切到 `download` 时不提交隐藏的 `recipients`。服务端通过该模式的领域规则移除不适用字段，因此它既遵守“补丁省略字段表示保持”的通用规则，也返回不含旧收件人的规范表示。若后来切回 `email`，一次新的补丁可把整个收件人数组替换为 `["editor@example.test","audit@example.test"]`；数组元素不是独立增删操作。

版本判断必须和写入处在一个原子条件里。下面的简化 SQL 假定主体到租户的授权已验证，且该授权在本次写事务提交前保持稳定；实际系统需由事务边界、授权行锁或等效约束保证这个前提。可以在事务中锁定并检查版本、合并和验证，然后执行版本条件更新；也可以把合并后的文档连同预期版本交给数据库条件更新：

~~~sql
UPDATE reports
SET document = :validated_document,
    version = 8
WHERE report_id = 42
  AND tenant_id = :authorized_tenant
  AND version = 7
RETURNING document, version;
~~~

如果权限可能在写入期间并发撤销，就不能仅依赖上面的租户和版本谓词：还要在写入的同一一致性边界内重核授权，例如锁住授权记录，或把当前授权谓词/版本纳入原子条件，并让撤销与写入按事务顺序发生。成功写入后再检查权限无法撤销已经发生的越权写入。条件更新返回一行并提交，服务才返回新表示和 ETag；返回 0 行只证明这次写入没有发生，不能单独证明是版本过期。记录可能已删除或版本已变化。服务用当前授权和租户范围重新读取：若对象现已不存在或不可见，按本例返回隐藏式 404；若对象仍可见但版本不再匹配，才返回 412。这个事后检查只区分失败原因，不替代写入时的授权原子性。不能先在事务外读到 v7、随后无条件更新：两次并发请求都可能检查 v7 后依次覆盖对方。

PATCH 的整份补丁必须原子应用：所有修改一起可见，或一项也不应用。这里的一行条件更新把版本比较与报表表示更新放在同一个数据库操作中；若一个补丁要改多行或其他持久状态，就要用同一事务覆盖全部改动和最终业务校验。

| 时点 | 用户甲 | 用户乙 | 数据库中的版本与结果 |
| --- | --- | --- | --- |
| 两人读取 | 保存 v7 表示和 ETag `"api-contracts-report-42-v7"` | 保存 v7 表示和 ETag `"api-contracts-report-42-v7"` | 当前版本 v7 |
| 甲提交 | `PATCH If-Match: "api-contracts-report-42-v7"`；条件更新匹配，提交 v8 | 仍在编辑 v7 草稿 | 当前版本 v8；甲收到 200 和 v8 标签 |
| 乙提交旧基线 | — | `PATCH If-Match: "api-contracts-report-42-v7"`；条件更新影响 0 行 | 此例中对象仍存在且可见、当前为 v8；没有应用乙的补丁，返回 412。删除或不可见时按前文返回 404 |
| 用户处理冲突 | — | 读取 v8，把 v7 基线、自己的草稿和当前 v8 比较；确认合并后才按新标签重提 | 直到新条件更新提交前都保持 v8 |

假设用户甲和乙都读到 v7。甲先提交后，当前表示成为 v8；乙仍用 v7 的编辑提交时，服务返回 412 Precondition Failed（前置条件失败），不自动覆盖、不自动重放：

~~~http
HTTP/1.1 412 Precondition Failed
Content-Type: application/problem+json

{"type":"https://api-contracts.example/problems/version-mismatch","title":"The report changed","status":412}
~~~

乙的客户端保留自己的草稿和 v7 编辑基线，重新读取 v8，再把基线、用户草稿与服务器当前表示进行比较；用户确认合并后才以新 ETag 再提交。若请求没有 `If-Match`，此合成端点选择 428 Precondition Required（要求前置条件）；这是一项端点政策。端点接受一个语法有效的实体标签值并用强比较：语法错误按 400 处理；`*` 和标签列表虽是 HTTP 合法语法，但因本端点规定只用单个标签，也按应用政策返回 400；单个弱标签语法有效，却不能通过强比较，因此与陈旧强标签一样返回 412。客户端在提交编辑时携带所保存的强 ETag；服务端能验证它是否以强比较匹配当前表示，但不能证明调用方真的曾读取过它。PATCH 方法本身不承诺安全或幂等；本端点的 `If-Match` 能阻止用旧版本重复应用，但若首个提交成功、响应丢失，重放旧标签也会得到 412，无法仅凭 412 判断是自己的首个写入还是别的用户修改。此时应重新读取并比较；需要精确确认首次副作用的端点还要保存操作幂等记录，见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。授权仍先于更改；412 不能替代对象授权结果。

这里选 JSON Merge Patch，不把 JSON Patch（JSON 操作补丁）当成同一语法：后者的 `application/json-patch+json` 正文是带 `add`、`remove`、`replace`、`move`、`copy` 或 `test` 的操作数组，数组元素和 `null` 按操作路径处理。服务应公开自己接受的媒体类型，例如通过 `Accept-Patch`，调用方也不能仅凭 HTTP 方法名猜补丁语义。

### 201 创建资源和 202 接受作业有什么区别？

`POST /api/reports` 创建的是一条报表资源。即使它的 `status` 先为 `queued`，`201 Created` 仍表示资源记录已经建立；它不声称成品已生成：

~~~http
POST /api/reports HTTP/1.1
Content-Type: application/json

{"title":"Weekly overview"}

HTTP/1.1 201 Created
Location: /api/reports/44
Content-Type: application/json

{"id":44,"title":"Weekly overview","status":"queued"}
~~~

若请求创建的是可能较久才完成的独立作业，账户报表案例按应用契约使用幂等键（`Idempotency-Key`）重复识别同一提交：

~~~http
POST /v1/accounts/acct-17/reports HTTP/1.1
Idempotency-Key: report-demo-208
Content-Type: application/json

{"reportId":42,"period":"2026-Q2","format":"csv"}

HTTP/1.1 202 Accepted
Location: /v1/jobs/job-demo-731
Content-Type: application/json

{"jobId":"job-demo-731","status":"queued","cancelRequested":false,"statusUrl":"/v1/jobs/job-demo-731"}
~~~

`202 Accepted` 只表示已受理，作业之后仍可能失败；状态地址让调用方继续查询。本账户报表契约把幂等键作用域定义为 `(account_id, principal_id, key)`，并把规范化请求指纹绑定到 `reportId`、时间范围和格式。数据库唯一约束裁决同键请求的胜者；竞争失败的一方先回滚整笔插入事务，再读回已提交的同键 job 并比较请求指纹。指纹相同则返回原 job 和状态地址，参数不同则返回冲突，不能把唯一约束本身说成已返回了 job。若 202 回执丢失，客户端用原幂等键和相同请求重发 `POST` 来找回结果；在幂等映射保留期内不要为这次重试换新键。job 状态和最小幂等映射保留到终态后 14 天；成功状态与结果引用共同提交、结果可见后，结果对象单独保留 7 天；两种保留期限解决不同问题。这里的 `Idempotency-Key` 行为是应用契约，不是 HTTP 状态码单独提供的保证。收到地址后，客户端用 `GET /v1/jobs/job-demo-731` 查询，而不是把 202 当作最终结果。具体事务和映射见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 分页怎样给出明确结束条件？

集合可能很大或持续变化，契约须规定页大小、确定性排序和结束信号。本例假设报表 ID 唯一，默认 `limit=2`、最大 100，按 ID 升序；`next_cursor` 是必返回字段，最后一页明确返回 JSON `null`。这是本 API 的表示选择：分页规范也可用不透明的 next-page token 表示结束。本例允许后续页在 1–100 范围内更改 `limit`；游标只定位下一项，筛选条件和排序若有变化则应重新开始列表。

~~~http
GET /api/reports?limit=2 HTTP/1.1
Host: api-contracts.example
Accept: application/json
~~~

~~~json
{"items":[{"id":41,"title":"Monthly overview","status":"ready"},{"id":42,"title":"Monthly summary","status":"ready"}],"next_cursor":"opaque-token-A"}
~~~

客户端原样传回不透明游标：

~~~http
GET /api/reports?limit=2&cursor=opaque-token-A HTTP/1.1
Host: api-contracts.example
Accept: application/json
~~~

~~~json
{"items":[{"id":43,"title":"Usage summary","status":"queued"}],"next_cursor":null}
~~~

这两页使用固定的三条演示数据：第一页 `[41, 42]` 续到 ID 42 之后，第二页 `[43]` 以 `null` 明确结束；只有客户端看见该结束标记才停止。短页不总表示没有后续数据，例如服务器可能按资源上限少返回几项，但仍提供游标。下面的内存复现把不透明 token 映射为偏移量，只适用于这组不变的演示数据：如果第一页后删除 ID 41，偏移量仍跳过两条，第二页会漏掉 ID 43。生产中的移动集合可把游标绑定筛选条件、授权范围、过期时间和最后一条记录的稳定复合键（如 `(created_at, id)`），下一页按键续读并每页重新授权；若要求固定快照，则必须让后续请求继续读取同一个快照。并列时间戳时，键集游标要同时保存两个排序键。

> [!example] 读完三条报表的分页回放
> 在这组固定数据中，ID 升序且页大小为 2：第一批是 `[41, 42]`，第二批是 `[43]`，返回 `next_cursor: null` 后停止。内存复现用偏移量映射 token；它不演示可变集合中的 keyset 或快照分页。若服务器因资源上限只返回 1 项但仍有后续数据，只凭短页就停止会漏项。运行代码会生成不透明 token。

### OpenAPI 怎样描述实际运行契约？

OpenAPI 记录操作路径、参数、请求/响应媒体类型、成功与错误响应、响应头及 schema，使人和工具可据此调用服务。框架可从请求/响应模型生成结构；自定义异常处理器也要在相应操作里声明错误响应。schema 可表达的约束要与运行时一致，例如仅含普通空格的标题既应在 `CreateReport` 的 JSON Schema 中被拒绝，也应在运行时返回 422；请求媒体类型和认证/授权等运行边界则要对照实际处理器单独核验。检查时按操作核对真实路径、状态码、媒体类型、创建响应的 `Location`、Problem `type`、分页字段必填性，以及 `next_cursor` 的 JSON Schema 是否同时允许字符串和 `null`。

下面的 FastAPI 复现定义裸应用前缀 `/api`，演示 GET/POST、验证、分页和 OpenAPI；它不实现上一节的 PATCH、Merge Patch、认证/租户授权、数据库唯一性或 ETag 并发写入。PATCH 合同使用 `/api/reports/42` 和 `Monthly summary` 的独立详情表示；可运行 fixture 是另一份独立最小数据集，GET 42 固定返回 `Service health` 摘要。创建路由用自定义 `APIRoute` 在 FastAPI 读取或解码正文前只接受 `application/json`，因此不支持的媒体类型即使正文不是合法 JSON，也先返回 415；支持的 JSON 媒体类型但正文格式错误才返回 400。媒体类型比较忽略大小写和参数。仅含普通空格的标题由请求 JSON Schema 的 `pattern` 与运行时校验共同拒绝。正文 `{"title":"   "}` 得到 422 Problem `type=.../validation`。fixture 不能证明 PATCH 表示、授权或并发写入；这些边界不能由 OpenAPI 生成结果替代。标题校验也有一个跨实现边界：JSON Schema 的 ECMAScript 正则与 Python `.strip()` 对 Unicode whitespace 的集合不同。例如以 ECMAScript 引擎执行此 `pattern` 时，单字符 `U+0085` 通过 `\S`，却被此 Python 运行时拒绝；`U+FEFF` 的结果相反。普通空格和长度样例通过，不等于 schema 与运行时对所有输入都一致。

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
> from fastapi.routing import APIRoute
> from fastapi.testclient import TestClient
> from pydantic import BaseModel, Field, field_validator
>
> PROBLEM_BASE = "https://api-contracts.example/problems/"
>
>
> class CreateReport(BaseModel):
>     title: str = Field(min_length=1, max_length=60, pattern=r"\S")
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
> class JsonOnlyRoute(APIRoute):
>     def get_route_handler(self):
>         original_route_handler = super().get_route_handler()
>
>         async def check_media_before_body(request: Request):
>             media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
>             if media_type != "application/json":
>                 raise ApiProblem(
>                     415, "unsupported-media-type", "Unsupported media type",
>                     "Send this resource using application/json.",
>                 )
>             return await original_route_handler(request)
>
>         return check_media_before_body
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
>     415: problem_content("Content-Type must be application/json"),
>     422: problem_content("Invalid title fields"),
> }
> CREATE_RESPONSES = {
>     201: {
>         "description": "Report resource created",
>         "headers": {
>             "Location": {
>                 "description": "URI of the newly created report",
>                 "schema": {"type": "string"},
>             }
>         },
>     },
>     **CREATE_ERRORS,
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
> create_router = APIRouter(prefix="/api", route_class=JsonOnlyRoute)
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
> @create_router.post("/reports", status_code=201, response_model=Report, responses=CREATE_RESPONSES)
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
> app.include_router(create_router)
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
>     for media_type in ("application/merge-patch+json", "text/plain"):
>         for body in ('{"title":"Ignored"}', "{"):
>             unsupported = client.post(
>                 "/api/reports", content=body, headers={"Content-Type": media_type}
>             )
>             assert unsupported.status_code == 415
>             assert unsupported.json()["type"] == PROBLEM_BASE + "unsupported-media-type"
>
>
>     created = client.post("/api/reports", json={"title": " Weekly detail "})
>     assert created.status_code == 201 and created.json()["id"] == 44
>     assert created.json()["title"] == "Weekly detail"
>     assert created.headers["location"] == "/api/reports/44"
>     duplicate = client.post("/api/reports", json={"title": "weekly detail"})
>     assert duplicate.status_code == 409
>     assert duplicate.json()["type"] == PROBLEM_BASE + "duplicate-title"
>     media_parameters = client.post(
>         "/api/reports", content='{"title":"Case variant"}',
>         headers={"Content-Type": "Application/JSON; charset=UTF-8"},
>     )
>     assert media_parameters.status_code == 201 and media_parameters.json()["id"] == 45
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
>     assert {"400", "409", "415", "422"} <= set(post["responses"])
>     assert "404" not in post["responses"]
>     assert "Location" in post["responses"]["201"]["headers"]
>     request_body = post["requestBody"]["content"]
>     assert set(request_body) == {"application/json"}
>     title_schema = spec["components"]["schemas"]["CreateReport"]["properties"]["title"]
>     assert title_schema["minLength"] == 1 and title_schema["maxLength"] == 60
>     assert title_schema["pattern"] == r"\S"
>     page_schema = spec["components"]["schemas"]["Page"]
>     assert "next_cursor" in page_schema["required"]
>     cursor_types = {part.get("type") for part in page_schema["properties"]["next_cursor"]["anyOf"]}
>     assert {"string", "null"} <= cursor_types
>     print("GET /api/reports/42 -> 200; missing -> 404; invalid ID -> 422")
>     print("malformed JSON -> 400; unsupported media type -> 415; blank/overlong title -> 422; duplicate -> 409")
>     print("page [41, 42] -> [43]; required next_cursor=null ends the listing")
>     print("OpenAPI routes and per-operation responses match the demonstrated paths")
>
>
> check()
> ~~~
>
> 此示例用内存中的偏移量映射演示游标边界；进程重启后令牌会失效，也未绑定筛选条件、排序或身份。未知或过期游标返回 400，调用方应从第一页开始；本例允许续页更改 `limit`，但筛选条件或排序变化要重新开始。生产集合可使用基于索引的键集游标，并对每一页重新授权。页面内容由这三条记录计算，不代表性能测量结果。

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

这里的 `links` 数组是本 API 自订的 JSON 结构，不是通用的 HTTP 链接编码。只有当媒体类型或 API 契约定义了关系名的含义与可用状态转移时，客户端才有足够信息按链接继续操作；给任意 JSON 加一个 `href` 字段本身并不会自动提供这些语义。

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
> - 错误正文的类别标识、状态、标题、详情和扩展字段：[IETF RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)，§3–§4，2023-07；核对于 2026-11-12。
> - 400、401 challenge、403、404、409、422、201 与 202 的 HTTP 语义及条件请求失败优先级：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§9、§11.6.1、§13.2.1、§15，2022-06；核对于 2026-11-12。428 和 429 分别见 [IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html) §3–§4；两种响应都不得缓存，2012-04；核对于 2026-11-12。
> - HTTP/1.1 请求的 `Host` 要求和消息正文分帧：[IETF RFC 9112, HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html)，§3.2、§6.3，2022-06；核对于 2026-11-12。正文中的请求报文都明确标为片段。
> - 表示验证器、强 ETag、不同内容编码需用不同强标签，以及 `If-Match` 强比较：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§8.8.1、§8.8.3.3、§13.1.1，2022-06；核对于 2026-11-12。
> - PATCH 的方法语义、整份补丁原子应用及 `Accept-Patch`：[IETF RFC 5789, PATCH Method for HTTP](https://www.rfc-editor.org/rfc/rfc5789.html)，§2、§3.1，2010-03；核对于 2026-11-12。
> - `application/merge-patch+json` 的成员省略、`null` 删除和整体数组值语义：[IETF RFC 7396, JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396.html)，§2，2014-10；核对于 2026-11-12。JSON Patch 的操作媒体类型与操作数组见 [IETF RFC 6902](https://www.rfc-editor.org/rfc/rfc6902.html)，§3–§4，2013-04；核对于 2026-11-12。
> - 操作、参数、媒体类型、响应和 schema 的接口描述：[OpenAPI Specification v3.2.1](https://spec.openapis.org/oas/v3.2.1.html)，2026-09-10，§4–§5；核对于 2026-11-12。代码环境当前生成 3.1.0；运行时版本由 `app.openapi()['openapi']` 决定，规范文件描述契约但不保证实现遵循它。
> - 不透明 page token、除 page size 外的续页参数一致，以及短页不代表结束：[Google AIP-158, Pagination](https://google.aip.dev/158)，2019-02-18，Guidance；核对于 2026-11-12。
> - FastAPI 请求模型、响应模型、自定义错误处理，以及用 `APIRoute.get_route_handler()` 在原请求处理器前检查请求：[Request Body](https://fastapi.tiangolo.com/tutorial/body/)、[Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)、[Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)、[Custom Request and APIRoute](https://fastapi.tiangolo.com/how-to/custom-request-and-route/)，官方文档核对于 2026-11-12。代码运行环境为 FastAPI 0.128.0、Starlette 0.47.2、HTTPX 0.28.1；运行回放另核验了媒体类型优先级与 OpenAPI 输出。
> - Pydantic 2.11 的前置字段校验器及 JSON Schema 生成：[Validators](https://docs.pydantic.dev/2.11/concepts/validators/)、[JSON Schema](https://docs.pydantic.dev/2.11/concepts/json_schema/)，官方版本文档核对于 2026-11-12；代码运行环境为 Pydantic 2.11.7。
> - REST 超媒体约束及由表示提供状态转移：[Roy Fielding, Architectural Styles and the Design of Network-based Software Architectures, §5.1.5](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，2000；核对日期：2026-11-12。
## 4. Cookie 会话与 OIDC 令牌怎样建立身份？

**合成案例。** `user-17` 打开 `https://reports.example.test`，准备读取租户 `tenant-a` 的报表 `42`（`Service health`）。报表应用由 Backend for Frontend（服务于前端的后端，BFF）处理浏览器请求；资源 API 位于 `api.reports.example.test`，Identity Provider（身份提供方，IdP）的固定签发者是 `https://idp.identity.test`。本例的 BFF client ID 固定为 `reports-bff-client`，IdP metadata 声明支持 RFC 9207 的 authorization-response `iss` 参数。该 IdP 签发的 ID Token 中，`iss`（签发者）是 `https://idp.identity.test`，代表用户的 `sub`（主体）是 `idp-user-4821`；应用把 `(iss, sub)` 映射到本地账户 `user-17`。这些标识和主机名都是虚构的；能否读取报表 42 仍由 API 按当前成员关系和资源状态逐次授权，见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

这几种凭据回答不同的问题：浏览器 Cookie 让报表应用找到自己的本地会话；OAuth 授权码流程让应用向授权服务器请求 API 访问权限；OpenID Connect（OIDC）ID Token（身份令牌）把身份提供方的认证结果交给登录客户端。ID Token 不替 API 授权，浏览器会话也不是 API Access Token（访问令牌）；访问令牌必须由授权服务器按 API 资源配置签发。本例选用后端代理浏览器请求的 BFF：Access Token 和 Refresh Token 保存在服务端，浏览器日常请求只持有不透明会话 Cookie。若用户请求可选 IdP 退出，浏览器顶层导航会附带已验证的 ID Token hint；它不是 API 凭据。

### 登录后，Cookie 会话怎样识别请求？

登录完成后，BFF 生成新的随机会话 ID，在服务器端保存会话记录，再用 `Set-Cookie` 让浏览器以后带回这个 ID：

~~~http
Set-Cookie: __Host-session=<random-opaque-id>; Path=/; Secure; HttpOnly; SameSite=Lax
~~~

这里的 `__Host-` 前缀要求 `Secure`、`Path=/` 且不带 `Domain`。因此这个 Cookie 由 `reports.example.test` 设置并限定在该主机；它不会随发往 `api.reports.example.test` 的请求发送。`HttpOnly` 阻止脚本通过非 HTTP API 读取 Cookie，`SameSite=Lax` 允许合适的跨站顶层安全导航，但不允许它代替 CSRF 防护。RFC 10017 §6.1.3.2 推荐 host-only、HTTP-only 的会话 Cookie 配置；本例通过 `__Host-` 前缀和显式 `HttpOnly` 属性实现。确需在跨站嵌入请求中附带 Cookie 时，`SameSite=None` 必须与 `Secure` 同用；浏览器的第三方 Cookie 策略仍可能阻止它。本例的匿名事务 Cookie 也设为 `Lax`，这样 IdP 的跨站顶层 GET callback 才会带回浏览器绑定值。BFF 指南对会话 Cookie 建议 `SameSite=Strict`；本例为保留外部顶层导航使用 `Lax`，因此对所有改变状态的请求仍检查 CSRF token，并校验精确的 `Origin`。若部署能使用 `Strict`，应按实际登录回跳路径验证体验；同站的兄弟子域也可能发起跨源请求，不能只靠 SameSite。

请求到达 BFF 后，服务端查找对应的会话记录，并检查服务端保存的过期时间、撤销状态和账户状态。Cookie 只是 HTTP 字段，有 Cookie 本身不代表请求已认证；同一机制也可承载偏好等非身份数据。此例的 Cookie 只带随机标识，不包含 `user-17`、角色或租户权限；认证成功后，会话映射到本地账户。自建会话 ID 应由密码学安全随机数生成器生成，至少有 128 位熵；业务身份和会话状态保存在服务器端，而不是从 ID 中解码。

Cookie 是浏览器自动附带的凭据，因此 BFF 的业务变更请求（包括退出）都要先验证会话绑定的跨站请求伪造（CSRF）令牌，并把请求 `Origin` 与该 BFF 的精确来源比对；缺失或不匹配时，拒绝请求且不执行操作。一种直接做法是把每个已登录会话的防伪值放在页面启动数据中，浏览器在非安全方法的自定义请求头中回传，BFF 将它与服务器端会话值比较。这个防伪值保护应用操作，不能拿 OIDC 的 `state` 代替。业务 `GET` 只读，不应通过它更新数据。OIDC 登录入口虽然会创建短期事务记录，但这是独立的协议端点；回调仍须通过匿名 Cookie、`state`、PKCE 和 `nonce` 的事务校验。`SameSite=Lax` 只提供部分跨站请求防护；来自同站兄弟子域的请求仍需由服务端的防伪检查拦截。

会话 ID 本身是可重放凭据。登录成功、密码重置或权限等级变化时，应用应销毁旧 ID 并签发新的 ID，避免攻击者预先固定的匿名会话在登录后继续有效。密码重置策略和管理员撤销也应使受影响的服务器端会话失效。空闲超时和绝对超时由服务端执行；退出时也要先撤销服务器记录，再让浏览器删除 Cookie。浏览器删掉 Cookie 只会停止后续自动发送，不能让已经复制的旧 ID 失效。

本页 Cookie 只认证到报表 BFF。浏览器不会把它自动转给报表 API；BFF 从服务端会话中取出 API 访问令牌，再由 BFF 发起请求。Cookie 的主机、站点、源和自动发送条件见[浏览器安全控制分别保护什么信任边界？](#6.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AE%89%E5%85%A8%E6%8E%A7%E5%88%B6%E5%88%86%E5%88%AB%E4%BF%9D%E6%8A%A4%E4%BB%80%E4%B9%88%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C%EF%BC%9F)。

### Cookie 会话和 Bearer 令牌各保留什么状态？

| 凭据 | 谁持有、发给谁 | 接收方验证什么 | 生命周期与边界 |
| --- | --- | --- | --- |
| 浏览器会话 Cookie | 浏览器发给 `reports.example.test` | BFF 用不透明 ID 查找仍有效的服务器端会话 | 退出时可撤销本地会话；Cookie 不证明 API 权限 |
| OIDC ID Token | Token Endpoint 返回给 BFF；可选登出时，已验证的 ID Token hint 随浏览器顶层请求发给固定 IdP | 客户端按 OIDC 验证签发者、客户端受众、时效和认证事务 nonce | 说明 IdP 认证结果；hint 不是报表 API 的 bearer credential |
| API Access Token | BFF 用 `Authorization: Bearer …` 发给报表 API | API 按令牌类型验签或查询状态，并确认签发方、API 受众、时效和允许的 scope/用途 | 取得 API 调用资格；不取代 API 对租户和报表的本地授权 |
| Refresh Token（刷新令牌） | 刷新时由 BFF 发给 IdP Token Endpoint；撤销时发给受信 revocation endpoint | IdP 检查 client、grant、有效期和轮换/绑定状态 | 换取新 Access Token；不得放进浏览器或发送给资源 API |

Bearer token（持有者令牌）是可重放凭据：拿到令牌的人能在它有效期间尝试使用。Access Token 可以是不透明字符串，也可以是 JSON Web Token（JWT，JSON Web 令牌）。API 对不透明令牌可调用 introspection（令牌状态查询），也可能缓存查询结果；缓存越久，撤销状态延迟可见的窗口越长。对自包含 JWT，API 按受信密钥、允许的算法、`iss`、`aud`、令牌用途、有效期和授权范围验证签名与声明，不必每次回 IdP 查状态，但离线验证通常会让已撤销令牌继续有效到过期，除非 API 另做撤销查询或拒绝列表。

JWT 是一种声明格式，不是“已验证身份”的同义词。签名 JWT 的载荷通常可被读取；签名能证明声明未被修改且由受信签发者签出，不提供保密性。只 Base64URL 解码，不是验签。ID Token 与 API Access Token 即使都采用 JWT 格式，也要检查各自不同的受众和用途。

本例选择 BFF 是为了让访问令牌和刷新令牌留在服务端。BFF 用 Cookie 会话代表浏览器查找该用户的令牌集合，再把 API Access Token 附加到固定的报表 API 请求中。服务端要限制可代理的主机、路径和方法，避免把用户令牌带到调用方任意指定的目标。`HttpOnly` 防止脚本直接读取 Cookie，但不能阻止页面中的恶意脚本借浏览器会话向 BFF 发请求；BFF 仍须防跨站脚本（XSS）和 CSRF。若应用改为浏览器内 OAuth 客户端，则它属于公开客户端（public client），不能把共享静态密钥当作保密客户端凭据；应使用授权码加 PKCE，并接受浏览器脚本执行环境对令牌的影响。把 Access Token 放进 `localStorage` 等脚本可读存储会让 XSS 能直接读取并外传；改用 HttpOnly Cookie 不会阻止被控脚本代发同源请求，也不能免除 CSRF。若授权服务器向公开客户端发 Refresh Token，则必须使用发送者约束或每次使用后轮换来检测重放。

### 授权码流程如何确认身份并建立应用会话？

OAuth 2.0 是授权框架；只有请求 OIDC 的 `openid` scope 并按 OIDC 验证 ID Token，客户端才按该协议获得身份断言。这个 BFF 是 OAuth 机密客户端（confidential client），API 是资源服务器，IdP 的授权服务器和 OpenID Provider（OP，OpenID 提供方）是本例固定信任方。流程先取得授权，再将受验证的身份绑定到本地账户和服务端会话：

1. **开始事务。** 浏览器打开 BFF 的登录入口。BFF 从受信配置选择 IdP 的 issuer、authorization endpoint、token endpoint、client ID `reports-bff-client` 和精确登记的 callback `https://reports.example.test/oidc/callback`；不能从任意请求参数拼出 IdP 或 API 目标。BFF 建立短期服务器端事务记录，包含随机一次性 `state`、OIDC `nonce`、随机 PKCE `code_verifier`、预期 `iss`、callback URI、创建时间和未使用状态。它用短期 `__Host-oidc-tx` Cookie 将匿名浏览器上下文与事务记录关联，属性为 `Path=/; Secure; HttpOnly; SameSite=Lax`，且不带 `Domain`。同一匿名上下文可索引多个未完成事务；只有 state 与该浏览器 Cookie 同时匹配的回调才继续。
2. **发起授权。** 对每次事务，BFF 用新的 32 个随机字节生成无填充 Base64URL `code_verifier`，再计算 `code_challenge = BASE64URL(SHA-256(ASCII(code_verifier)))`，并显式发送 `code_challenge_method=S256`。省略这个字段时，RFC 7636 的默认值是 `plain`，不会自动替客户端选择 SHA-256。这组参数使用 PKCE（Proof Key for Code Exchange，授权码交换证明密钥）：`code_verifier` 留在 BFF，`code_challenge` 发给 IdP。BFF 把浏览器重定向到固定 IdP，参数包括 `response_type=code`、`client_id`、精确 `redirect_uri`、`scope=openid reports.read`、`state`、`nonce`、`code_challenge` 和 `code_challenge_method=S256`。`reports.read` 是请求给 API 的权限范围；它不会自行证明 `user-17` 属于 `tenant-a`。若部署支持 RFC 8707，可用 `resource` 指明 API；否则客户端和 IdP 必须使用双方预先约定的 API 受众（audience）。
3. **认证并回调。** IdP 在自己的页面认证用户，并按策略要求其同意授权。随后它用一次性短期 code 导航回已登记的 callback，带上原 `state` 和 `iss`。本例的 IdP metadata 已配置 `authorization_response_iss_parameter_supported=true`，所以 BFF 要求响应（包括错误响应）必须带 `iss`，并与该事务的预期 issuer 精确比对；缺失或不匹配都拒绝。BFF 还要求请求中的 `__Host-oidc-tx`，用它找到属于当前浏览器的事务，然后以单次原子条件更新同时核对 state、过期/未消费状态并标为已消费，避免并发回调重复兑换 code。部署若使用不支持 RFC 9207 的 IdP，应采用不同 callback URI 或其他 mix-up 防护，不可把本例的 `iss` 检查静默降成可选。Cookie 缺失、state 不匹配、事务重放、issuer 错误或 IdP 返回授权错误时，本事务停止，不交换 code，也不创建登录会话。

前三步确认回调属于发起登录的浏览器，并在校验成功时消费该事务。图中红色分支表示事务校验失败就停止；此时还没有向 Token Endpoint 兑换 code。

![OIDC 登录第一段：浏览器绑定授权事务并校验回调](../../engineering-foundations/security/resources/web-sessions-and-oidc-login-transaction.svg)

通过回调校验后，BFF 才拿同一事务保存的 verifier 进入后端兑换；拿到令牌后还要验证身份，才建立应用会话。

4. **兑换 code。** callback 只处理固定参数并返回到固定的应用内路径，不把 `return_to` 等未验证值作为外部重定向地址。BFF 通过已验证的传输层安全（TLS）后端连接调用 Token Endpoint，发送 `grant_type=authorization_code`、code、相同的 `redirect_uri`、秘密 verifier 和 confidential client authentication。IdP 验证 code 尚未使用、绑定到该 client/redirect URI、PKCE challenge 匹配后，返回 ID Token、Access Token 以及可能的 Refresh Token。PKCE 把 code 兑换限制在持有 verifier 的本次事务；`state` 把浏览器回调绑回发起的事务；`nonce` 把 ID Token 绑回这次身份认证。三者目的不同，不能把任一响应值直接当作已验证输入。 RFC 9700 允许在确认授权服务器支持 PKCE 时依靠 PKCE 保护授权回调免受 CSRF；本例仍显式绑定并检查 Cookie、state 和 nonce。这个协议端点的保护不能代替报表业务变更请求的防伪检查。
5. **验证身份并绑定本地账户。** BFF 在使用 ID Token 中的身份前，按 OIDC 规则验证签名和受信算法（或适用时使用下方所述的 Token Endpoint TLS 例外）、精确 issuer、`aud`、有效期和本次事务的 `nonce`；若请求包含 `max_age`，也检查 `auth_time`。本例的唯一受信 audience 是 `reports-bff-client`，因此 `aud` 必须只含此 client；若另一部署允许额外 audience，必须逐个明确列入信任配置并拒绝其他值。`azp` 仅在启用产生该 claim 的扩展/profile 时按其规则验证。再用稳定键 `(iss, sub)` 查找本地身份绑定。本例只有查到 `(https://idp.identity.test, idp-user-4821) → user-17` 时才识别成本地用户；不要仅凭可能变化或未验证的 email 自动合并账户。若这是把 IdP 账户链接到一个已登录的本地账户，应另外要求该本地账户的有效近期认证和明确确认，再建立唯一的 `(iss, sub)` 绑定。
6. **建立新会话。** BFF 将身份、会话 ID、有效时间和 API grant 关联保存在服务器端，销毁匿名上下文及任何登录前 session ID，然后签发全新的 `__Host-session` Cookie。匿名 session ID 不得升级后继续复用。ID Token 用来验证面向 BFF 的身份；API Access Token 必须面向报表 API。若 IdP 没有为该 API 签发匹配 audience 和 scope 的令牌，BFF 不得把 ID Token 或其他 audience 的 Access Token 送给 API。

BFF 建成自己的会话后，用户才有了访问报表应用的登录态。这个结果仍不替代资源 API 的逐次授权。

![OIDC 登录第二段：兑换授权码、绑定本地身份并签发新会话](../../engineering-foundations/security/resources/web-sessions-and-oidc-code-binding.svg)

授权响应中的 code 可能出现在浏览器历史、代理日志或 Referer 中。callback 应是无第三方脚本、图片和链接的最小端点，设置 `Referrer-Policy: no-referrer`，日志不得记录 code、state、token 或 Cookie；成功后立即转到不含敏感参数的固定页面。固定 callback、单次 code、PKCE 和事务过期缩短泄漏后的可用性，但不能把“浏览器绝不会留下 callback URL”当作保证。OAuth 安全最佳实践还禁止开放重定向；若要返回用户原路径，只接受服务端允许的站内路径。详细的 token 受众与 API 授权边界见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

> [!info] 单点登录不会替每个应用建立相同的本地会话
> IdP 的单点登录（Single Sign-On，SSO）会话可以让同一浏览器再次访问其他已注册应用时免于重新输入凭据，但 IdP 策略、同意要求或认证时效仍可能要求用户再次交互。每个应用仍须独立校验自己的回调、验证 ID Token、绑定本地身份并创建自己的 Cookie 会话。某个应用退出本地会话，不会自动结束 IdP 的 SSO 会话，也不会让其他应用的会话一并退出。

> [!info] Token Endpoint 的受限签名校验例外
> OIDC Core 对经已验证 TLS 连接直接从 Token Endpoint 收到的 Authorization Code Flow ID Token 规定一条窄例外：客户端可以用 Token Endpoint 的 TLS 服务器身份验证替代 ID Token 签名校验。它不适用于从浏览器、其他 API 或不可信来源取得的 ID Token；其他场景仍须按 OIDC 规则验证签名。

### 调用、刷新与退出分别撤销什么？

**调用报表 API。** 浏览器向 `reports.example.test` 发起只读 GET，请求自动携带 `__Host-session`；这个请求不带 CSRF token，因为安全方法不得改变业务状态。若浏览器请求改为改变状态的操作，BFF 才要求会话绑定的防伪 token 和精确 `Origin` 校验。BFF 查到有效会话后，用 Token Endpoint 返回的 `expires_in`（或经过验证的令牌到期声明）维护本地到期时间；未到期才把 bearer 发给 `api.reports.example.test`，到期则先进入下方刷新流程，本次 API 请求尚未发送。API 仍是最终验证者：它验证 Access Token，再把令牌标识的 API 主体映射为 `user-17`，依照当前租户成员关系、报表归属和动作授权。请求路径里的 `tenant-a`、`42` 是调用方选择的未可信资源标识，不是主体或授权证明。Cookie 建立 BFF 会话，Access Token 供 API 识别调用资格，授权结果由 API 作出。

![浏览器用 Cookie 调用 BFF，BFF 再用 API Access Token 调用报表 API](../../engineering-foundations/security/resources/web-sessions-and-oidc-api-call.svg)

**刷新令牌。** BFF 在第一次发送 API 请求前发现 Access Token 已到期，就按同一授权 grant 取得刷新锁或合并为一个 in-flight 刷新；其他 worker 的请求等待后重新读取会话，避免并发发送同一旧 Refresh Token。持锁的请求才通过可信 TLS 连接向固定 Token Endpoint 发送 Refresh Token，并用 confidential client authentication。成功后，BFF 仍须以“会话有效且 grant/版本仍与发起刷新时相符”为条件，在释放锁前原子保存新的 Access Token；若 IdP 返回轮换的 Refresh Token，也在同一次更新中替换旧值。条件不符就丢弃结果并停止本次调用，不能因迟到的刷新响应恢复已退出或已撤销的会话。只有条件写回成功，才用新 Access Token 首次发送原 API 请求。这个并发写入约束由 BFF 实现；本地退出不能追溯取消已提交给远端的请求。若没有 Refresh Token，或 IdP 明确返回 `invalid_grant` 表示 grant/token 已无效、过期或撤销，本例停止 API 调用并要求重新授权；因为此案例把 API grant 与 BFF 会话绑定，失效 grant 也会结束这条令牌会话。若产品分开保存本地身份会话和 API grant，可只停用 grant、保留有效 Cookie，但仍须拒绝本次 API 调用。网络超时、5xx、其他不表示 grant 失效的错误或结果不明时，只失败本次 API 调用；不能据此推断 grant 已失效，也不要盲目重发旧 Refresh Token，应按错误和 IdP 恢复/幂等策略处理。IdP 可能仍保有 SSO session，因此新的授权流程不一定要求重新输入密码。Refresh Token 永不发给浏览器或 API。

![Access Token 到期时，BFF 在服务端刷新并处理拒绝分支](../../engineering-foundations/security/resources/web-sessions-and-oidc-refresh.svg)

**退出与撤销。** 页面用 `fetch` 向 BFF 发受 CSRF 防护的 POST `/logout`，携带会话 Cookie、自定义防伪 header 和精确来源。若本次要请求 IdP SSO 退出，BFF 先从活动会话取出已验证的 ID Token，作为必需的 `id_token_hint`，并为一次性退出 `state` 建短期事务；若要撤销上游令牌，也先保存要提交的 Refresh Token。然后撤销服务器端本地会话；即使旧 Cookie 被复制，服务端也拒绝已失效的记录。若本次请求 IdP SSO 退出，BFF 在同一个 200 JSON 响应中清除 `__Host-session`、设置 host-only 的 `__Host-oidc-logout-tx`（`Secure; HttpOnly; Path=/; SameSite=Lax`），并返回用受信 IdP metadata 中 HTTPS `end_session_endpoint` 组装的固定允许 URL。URL 中包含 `id_token_hint`、精确登记的 `post_logout_redirect_uri` 与 `state`，浏览器能看到并把 hint 发送到该固定 IdP 退出端点；页面和 callback 使用 `Referrer-Policy: no-referrer`，hint 不会发给 API，也不是 API Access Token。否则，响应只清理本地 Cookie 并给出已退出状态。

若应用保存 Refresh Token，可独立地通过可信 HTTPS 连接向 IdP 撤销端点发 POST，并以机密客户端凭据认证。RFC 7009 的 200 不说明调用前 token 一定有效或刚刚才撤销；503 表示客户端应假定 token 仍有效，可按策略稍后重试。远端不可用不影响本地 session 已撤销和 Cookie 已清除，但不能宣称上游 token 已即时撤销。浏览器若要请求 IdP 退出，页面显式执行 `window.location.assign(logoutUrl)` 做顶层导航；`fetch` 自己跟随 302/303 只处理该 fetch 的重定向，不会把当前页面变成 IdP 页面。本例登记顶层 GET 的 `post_logout_redirect_uri`，使 Lax 事务 Cookie 能随 IdP 回跳送回 BFF；BFF 再用 Cookie 找 state、精确比对并原子消费。

撤销 Refresh Token 后，IdP 是否同时撤销同一 grant 的已有 Access Token，取决于 IdP 的撤销行为；这与资源 API 如何观察已撤销状态是两个条件。API 每次查询状态时可在 IdP 撤销生效后拒绝，introspection 缓存则会引入观察延迟；只离线验证未过期签名 JWT 的 API 通常会接受到 token 到期，除非另有撤销机制。API 对 `tenant-a`/`42` 的当前授权也仍由 API 根据自己的数据作出，不会因为浏览器清 Cookie 自动失效。

退出报表应用的本地 Cookie session、撤销 OAuth grant/token、结束 IdP 的 SSO session 是三项不同操作。本例顶层导航把浏览器送到受信的 HTTPS `end_session_endpoint`，附带已验证的 `id_token_hint`、精确登记的 `post_logout_redirect_uri` 和一次性 `state`。其他应用是否同时结束本地会话，取决于是否另外配置并联动 IdP 的前通道/后通道退出机制；单个应用退出不构成全局退出保证。某些 IdP 也可能要求额外交互。

![应用本地退出、上游令牌撤销与可选 IdP SSO 退出的不同结果](../../engineering-foundations/security/resources/web-sessions-and-oidc-logout.svg)

### 本地密码验证后，应用还要做什么？

若应用本身验证密码，它仍须建立自己的服务端会话，不能把密码校验结果塞进可由客户端修改的字段。数据库存储带随机盐的专用密码哈希及其算法、成本参数，不保存明文或快速通用散列；在线登录入口还要限制尝试速率。数据库泄漏后，攻击者可以离线反复猜测密码；Argon2id 的内存与计算成本让每次猜测更昂贵，和入口的在线限速解决不同问题。OWASP 当前给出的 Argon2id 基线示例为 19 MiB 内存、2 次迭代、并行度 1；部署应基于自身硬件和并发调优，而不是把最低示例当作性能目标。Salt 不需要保密；可选 pepper 是数据库之外的服务器秘密，需要有密钥保护、轮换和恢复方案。

密码验证成功后，应用同样要销毁匿名 session ID、签发新的随机 ID、建立有服务端超时的本地会话。它只代表本地认证；不会凭空产生 OIDC ID Token、OAuth API grant 或 API Access Token。

> [!info]- 来源
> - Cookie 基本模型：[IETF RFC 6265, HTTP State Management Mechanism](https://www.rfc-editor.org/rfc/rfc6265.html)，§4–§5；属性、`__Host-` 前缀、SameSite 站点与发送条件：[IETF Internet-Draft draft-ietf-httpbis-rfc6265bis-22](https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis-22)，§4.1.2.5–§4.1.3.2、§5.6.7、§8.8；该版本是 2025-12 发布的 Internet-Draft，标示 2026-06 到期，不是正式 RFC。Datatracker 仍列其为当前 I-D，RFC Editor 的 [RFC-to-be 10025 final-review 页面](https://queue.rfc-editor.org/final-review/rfc10025/) 于 2026-11-13 仍显示 Final Approval Pending，因此不能称 10025 已发布或已取代 RFC 6265。
> - BFF 授权码架构、服务器端 token、会话 Cookie、刷新和 CSRF 要求：[IETF RFC 10017, OAuth 2.0 for Browser-Based Applications](https://www.rfc-editor.org/rfc/rfc10017.html)，BCP 212，§6.1.1–§6.1.3；2026-08。
> - Session-bound synchronizer token、请求 header 回传、精确 Origin/Referer 校验和 SameSite 的局限：[OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)，§Synchronizer Token Pattern、§Using Standard Headers to Verify Origin、§Limitations of SameSite；核对于 2026-11-12。
> - OAuth 授权码请求与兑换参数：[IETF RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html)，§4.1.1–§4.1.4；Bearer 请求头：[RFC 6750](https://www.rfc-editor.org/rfc/rfc6750.html)，§2.1；安全最佳实践，包括精确 callback、state/PKCE、mix-up、code/Referer 泄漏、开放重定向、受众限制和 Refresh Token 保护：[RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)，§2.1–§2.3、§4.1–§4.5、§4.11、§4.14；2025-01。
> - PKCE verifier、challenge 和 S256：[IETF RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html)，§4.1–§4.3、Appendix B；issuer 参数防多授权服务器 mix-up：[RFC 9207](https://www.rfc-editor.org/rfc/rfc9207.html)，§2；资源指示参数：[RFC 8707](https://www.rfc-editor.org/rfc/rfc8707.html)，§2。
> - OIDC 身份请求、ID Token 验证与可依赖 claim：[OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html)，§3.1.2.1、§3.1.3.7、§5.7；2023-12-15。RP 发起退出：[OpenID Connect RP-Initiated Logout 1.0](https://openid.net/specs/openid-connect-rpinitiated-1_0-final.html)，§2–§3；Final 1.0。
> - 联邦身份绑定不可仅以 email 自动合并、添加/删除链接身份前要求当前本地认证：[OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)，§Secure Federated Account Linking；核对于 2026-11-12。
> - Token 撤销及返回语义：[IETF RFC 7009](https://www.rfc-editor.org/rfc/rfc7009.html)，§2；不透明 token introspection 与 `active` 状态：[RFC 7662](https://www.rfc-editor.org/rfc/rfc7662.html)，§2.2；JWT 验证算法与用途隔离：[RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html)，§3。
> - 会话标识熵、登录后轮换、服务端失效和超时：[OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)，§Session ID Entropy、Renew the Session ID After Any Privilege Level Change、Session Expiration；核对于 2026-11-12。
> - Argon2id 参数、随机盐与 pepper：[OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)，§Argon2id、Peppering；核对于 2026-11-12。
## 5. 如何逐次授权租户内的报表资源？

Authentication (身份认证) 确认请求代表哪个主体；authorization (授权) 判断该主体此刻能否对指定资源执行指定动作。路径中的租户是调用方选择的上下文；请求正文、缓存键和队列消息里的用户 ID、租户 ID、角色名或报表编号也不能自行证明权限。

**合成案例：** 浏览器请求 `GET /api/tenants/tenant-a/reports/42`。上游会话检查已把请求映射到可信主体 `user-17`；路径里的 `tenant-a` 和 `42` 是调用方选择的范围与资源编号，服务端仍须查验。当前成员表显示该主体是 `tenant-a` 的 `reader`，报表 42 属于 `tenant-a`，标题为 `Service health`。`reader` 只有 `report:read`，不能由此推出刷新或导出权限。

> [!warning] 缓存命中的前提：对象身份不能悄悄变化
> 本例没有额外的单报表访问控制规则，报表归属不变；在缓存或任务有效期间不删除报表行，也不复用 `(tenant_id, id)`。若系统允许删除、迁移或复用编号，缓存命中前必须核验仍是同一对象及当前访问规则，或在变更时可靠失效相关副本，并定义待执行任务的行为；本例不实现这些机制。

本例把无成员、无动作权限和该租户内资源不存在统一隐藏为 `404`，这不是所有 API 必须采用的状态码策略。隐藏错误码、缓存键、任务记录字段和撤权时点也都是本案例的约定，实际系统要根据资源生命周期和任务副作用定义。

| 请求状态 | 当前数据条件 | 本例结果 |
| --- | --- | --- |
| `user-17` 请求 `tenant-a` 的 `report:read` / 42 | 当前成员是 `reader`，复合键 `(tenant-a, 42)` 存在 | `200`，返回 `Service health` |
| `user-29` 请求 `tenant-b` 的 `report:read` / 73 | 当前成员是 `reader`，复合键 `(tenant-b, 73)` 存在 | `200`，返回其租户的 `Usage summary` |
| `user-29` 请求 `tenant-b` 的 `report:read` / 42 | `user-29` 是 `tenant-b` 的 `reader`，但 `(tenant-b, 42)` 不存在 | `404`，不读取 `tenant-a` 的 42 |
| `user-29` 请求 `tenant-a` 的 `report:read` / 42 | 没有当前 `tenant-a` 成员关系 | `404`，按本例隐藏策略处理 |
| `user-17` 被移出 `tenant-a` 后重读或执行排队任务 | 成员关系已撤销，即使缓存已有旧正文 | API 按隐藏策略返回 `404`；本例 worker（从队列取任务并执行的服务端进程）拒绝继续执行 |

这些都是用户范围的响应；本例的 HTTP 适配层对报表正文和隐藏授权结果设置 `Cache-Control: private, no-store`，要求合规 HTTP 缓存不存储这些响应。下面的 Python `read_api` 只返回状态码和正文，不实现该 HTTP 响应头。RFC 9110 允许 `404` 启发式缓存，因此不能靠状态码本身阻止缓存或完成授权。下文的命中/未命中则是独立的服务端应用数据缓存。

![已验证主体与调用方路径各自进入授权检查，当前成员和动作通过后才转入缓存取数](../../engineering-foundations/security/resources/web-security-and-authentication-request.svg)

### 从可信主体到报表 42 的读取，需要经过哪些检查？

1. 认证层先把 Cookie 会话或访问令牌映射为可信主体。不要把请求头或请求体里的 `user_id` 当作登录结果；凭据和联邦登录见[Cookie 会话与 OIDC 令牌怎样建立身份？](#4.%20Cookie%20%E4%BC%9A%E8%AF%9D%E4%B8%8E%20OIDC%20%E4%BB%A4%E7%89%8C%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E8%BA%AB%E4%BB%BD%EF%BC%9F)。
2. 将路径里的 `tenant-a` 当作用户选择的范围，查该主体此刻在该租户的成员关系。用户可在不同租户拥有不同角色；客户端报来的 `tenant_id` 和 `role` 都不能取代服务端当前状态。
3. 将动作和对象一起检查：`reader` 可执行 `report:read`，不因此获得 `report:refresh`、`report:export` 或管理权限。有效会话只说明主体是谁，不说明此动作获准。未明确授予的动作默认拒绝。
4. 数据读取按 `(tenant_id, report_id)` 过滤。不要先按全局编号装入私有对象，再依赖隐藏链接、难猜 ID 或 UI 隐藏完成授权。
5. 对缓存、附件和后台任务等旁路逐一确认同一授权条件确实生效。worker 的服务账号最小权限限制其调用能力，不替最终用户的资源授权。

#### 角色能授予什么动作，资源检查还要做什么？

Role-Based Access Control (RBAC，基于角色的访问控制) 用 `reader`、`admin` 等角色归纳允许动作，适合表达租户成员的常见权限。本例的 `reader` 只对应 `report:read`。角色不能证明报表 42 属于当前租户，也不能阻止本应在每次请求重查的成员关系变旧。若采用单报表分享、部门属性或其他关系条件，策略还要把这些条件加入对象访问判断。

### 数据库与缓存怎样保持同一授权范围？

把租户和报表编号分别作为绑定值传入 SQL：

下面的 `?` 是本页 Python `sqlite3` 复现使用的占位符写法；实际语法按数据库驱动选择。无论占位符如何书写，都把值作为参数绑定，不要用字符串拼接组成条件。

~~~sql
SELECT id, title, body
FROM reports
WHERE tenant_id = ? AND id = ?;
~~~

参数绑定防止输入改写 SQL 语法；授权检查决定当前主体能否读取绑定后的对象。两者解决不同问题：绑定参数后读取 `report_id=73` 仍可能越权；完成授权但拼接 SQL 仍可能被注入。动态排序字段通常不能作为一般参数绑定，应从固定允许列表里选择。

本例的数据库用复合主键 `(tenant_id, id)` 标识租户内报表；这使每个租户的编号空间明确。查询仍须保留两个谓词，因为主键约束数据形状，并不判断当前用户是否有权读该行。队列里的任务引用也应按同一复合身份解析。

这里的缓存指服务端应用数据缓存，不是浏览器或共享 HTTP 缓存。API 先重查当前成员和 `report:read`，只有通过后才用 `(tenant_id, subject, report_id)` 查缓存；缓存键限制副本范围，但本身不是授权凭据。未命中时按复合键执行 SQL，只有读到属于该租户的行才填充同一范围的缓存。缓存命中还依赖开场约定的对象生命周期；缓存键不能证明对象没有被删除、迁移或复用。参见[如何控制数据库缓存的新鲜度？](#12.%20%E6%80%8E%E6%A0%B7%E7%BC%93%E5%AD%98%E6%95%B0%E6%8D%AE%E5%BA%93%E8%AF%BB%E5%8F%96%E5%B9%B6%E8%AF%B4%E6%98%8E%E9%99%88%E6%97%A7%E7%AA%97%E5%8F%A3%EF%BC%9F)。

![已授权的请求按租户主体对象查应用缓存，未命中再按复合键查询，匹配行与不存在分别返回200与404](../../engineering-foundations/security/resources/web-security-and-authentication-cache.svg)

### 后台任务如何继续执行相同的访问政策？

排队前先按任务的实际动作授权，再由服务端保存可信任务记录。队列消息只携带任务 ID；worker 按 ID 取出已经保存的请求人、租户、动作和报表编号，不把消息正文当成这些字段的权威来源。任务 ID 只是定位记录的值，不是权限凭据。

本例选择“执行时仍须有权限”：排队时 `user-17` 可读 `tenant-a` 的 42，worker 开始执行前重新查该用户的当前成员关系与动作权限；若成员已撤销，任务在读取缓存或报表正文前就被拒绝。这里的“当前”指 worker 检查时读到的成员状态；若生产环境的读副本或授权缓存会滞后，撤权生效期限须由系统明确，已经通过检查的执行是否中途停止也需按产品定义。若另一产品定义为“已受理任务继续”，它应持久化可审计的受理授权决定，并明确后续读取、导出等副作用仍受哪些控制；这不是本例的选择。

下面的复现只排队读取现有报表，因此 `enqueue_read_job` 要求 `report:read`。高成本导出或重算必须单独授权 `report:export` 或 `report:refresh`；不能从 `reader` 推出，也不能因执行者是 worker 而放宽。`run_job(job_id, cache)` 接收已保存的任务 ID，并把报表对象返回给 worker 调用方；示例用直接函数调用代替队列消息交付，不实现 broker 或结果投递。worker 的服务身份限制它能调用哪些存储或服务，任务仍以已记录的用户、租户和动作应用本例策略。

![任务在提交时按当前权限受理；队列只传任务 ID；worker 取回服务端记录后复验当前权限，通过后复用应用缓存或租户复合键查询，并把报表对象返回调用方；成员被撤销时在读取正文前拒绝](../../engineering-foundations/security/resources/web-security-and-authentication-worker.svg)

任务处理的持久受理、outbox 发布和队列确认见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)；队列确认分别见[发布者确认和消费者确认分别证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

输入输出可以直接按上面的状态表理解：甲的成员读取甲的 42 返回 200；乙的成员读取乙命名空间中不存在的 42 返回 404；失去成员关系后，API 仍按隐藏策略返回 404，尚未开始的 worker 任务抛出拒绝异常。完整 SQLite 复现放在折叠示例中。

> [!example]- SQLite 授权、缓存与任务复现
> 示例使用标准库 SQLite 和合成数据；`principal_for` 的主体参数视为认证中间件已经验证，不实现 Cookie 或签名令牌。路径租户值仍是调用方输入，只有成员查询通过后才成为本例的有效范围。
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
>     requester TEXT NOT NULL, action TEXT NOT NULL, report_id INTEGER NOT NULL
> );
> INSERT INTO memberships VALUES ('tenant-a', 'user-17', 'reader');
> INSERT INTO memberships VALUES ('tenant-b', 'user-29', 'reader');
> INSERT INTO reports VALUES
>     ('tenant-a', 42, 'Service health', 'Synthetic private data A');
> INSERT INTO reports VALUES
>     ('tenant-b', 73, 'Usage summary', 'Synthetic private data B');
> """)
>
> # verified_subject comes from authentication middleware, never from request JSON.
> def principal_for(tenant_id, verified_subject):
>     row = db.execute(
>         "SELECT role FROM memberships WHERE tenant_id=? AND subject=?",
>         (tenant_id, verified_subject),
>     ).fetchone()
>     if row is None:
>         return None
>     return {"tenant_id": tenant_id, "subject": verified_subject, "role": row[0]}
>
> ROLE_ACTIONS = {
>     "reader": {"report:read"},
>     "admin": {"report:read"},
> }
>
> def permits(principal, action):
>     return principal is not None and action in ROLE_ACTIONS.get(principal["role"], set())
>
> def read_report(principal, report_id, cache):
>     if not permits(principal, "report:read"):
>         raise PermissionError("no current report:read permission")
>     key = (principal["tenant_id"], principal["subject"], report_id)
>     if key not in cache:
>         row = db.execute(
>             "SELECT title, body FROM reports WHERE tenant_id=? AND id=?",
>             (principal["tenant_id"], report_id),
>         ).fetchone()
>         if row is None:
>             return None
>         cache[key] = {"title": row[0], "body": row[1]}
>     return cache[key]
>
> def read_api(tenant_id, verified_subject, report_id, cache):
>     # 隐藏政策把无成员、无动作权限和资源不存在统一映射为 404。
>     principal = principal_for(tenant_id, verified_subject)
>     if not permits(principal, "report:read"):
>         return (404, None)
>     report = read_report(principal, report_id, cache)
>     return (404, None) if report is None else (200, report)
>
> def enqueue_read_job(tenant_id, verified_subject, report_id, cache):
>     principal = principal_for(tenant_id, verified_subject)
>     if not permits(principal, "report:read"):
>         raise PermissionError("cannot enqueue without current report:read")
>     if read_report(principal, report_id, cache) is None:
>         raise PermissionError("cannot enqueue an unreadable report")
>     cursor = db.execute(
>         "INSERT INTO jobs (tenant_id, requester, action, report_id) "
>         "VALUES (?, ?, ?, ?)",
>         (principal["tenant_id"], principal["subject"], "report:read", report_id),
>     )
>     db.commit()
>     return cursor.lastrowid
>
> def run_job(job_id, cache):
>     job = db.execute(
>         "SELECT tenant_id, requester, action, report_id FROM jobs WHERE id=?",
>         (job_id,),
>     ).fetchone()
>     if job is None:
>         raise PermissionError("unknown job")
>     tenant_id, requester, action, report_id = job
>     principal = principal_for(tenant_id, requester)  # 执行时重查成员
>     if not permits(principal, action):
>         raise PermissionError("requester no longer has the task permission")
>     body = read_report(principal, report_id, cache)
>     if body is None:
>         raise PermissionError("job target is missing from its recorded tenant")
>     return body
>
> cache = {}
> report_a = {"title": "Service health", "body": "Synthetic private data A"}
> report_b = {"title": "Usage summary", "body": "Synthetic private data B"}
> assert permits(principal_for("tenant-a", "user-17"), "report:read")
> assert not permits(principal_for("tenant-a", "user-17"), "report:export")
> assert read_api("tenant-a", "user-17", 42, cache) == (
>     200, report_a
> )
> assert read_api("tenant-b", "user-29", 73, cache) == (200, report_b)
> assert read_api("tenant-b", "user-29", 42, cache) == (404, None)
> assert read_api("tenant-a", "user-29", 42, cache) == (404, None)
> completed_job_id = enqueue_read_job("tenant-a", "user-17", 42, cache)
> assert run_job(completed_job_id, cache) == report_a
>
> # 另建尚未开始的任务；撤权测试使用这个新 ID，不重跑已完成的任务。
> pending_job_id = enqueue_read_job("tenant-a", "user-17", 42, cache)
> assert pending_job_id != completed_job_id
>
> # 服务端一致性夹具：tenant-b 的成员有读权限，但本租户没有 report 42。
> missing_target_job = db.execute(
>     "INSERT INTO jobs (tenant_id, requester, action, report_id) "
>     "VALUES (?, ?, ?, ?)",
>     ("tenant-b", "user-29", "report:read", 42),
> )
> db.commit()
> try:
>     run_job(missing_target_job.lastrowid, cache)
> except PermissionError:
>     pass
> else:
>     raise AssertionError("worker accepted a target missing from its tenant")
>
> # 尚未开始的任务在成员撤销后不得命中旧缓存。
> db.execute("DELETE FROM memberships WHERE tenant_id=? AND subject=?",
>            ("tenant-a", "user-17"))
> db.commit()
> assert read_api("tenant-a", "user-17", 42, cache) == (404, None)
> try:
>     run_job(pending_job_id, cache)
> except PermissionError:
>     pass
> else:
>     raise AssertionError("worker started a pending job after revocation")
> print("tenant-a user-17 report 42 -> 200 Service health before revocation, 404 after")
> print("tenant-b user-29 report 73 -> 200 Usage summary; report 42 -> 404")
> print("reader report:export, missing tenant target and revoked pending job denied")
> ~~~

**接下来：** 本章负责服务端把主体、动作和租户内资源联系起来；浏览器跨源读取、Cookie 自动发送和脚本执行见[浏览器安全控制分别保护什么信任边界？](#6.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AE%89%E5%85%A8%E6%8E%A7%E5%88%B6%E5%88%86%E5%88%AB%E4%BF%9D%E6%8A%A4%E4%BB%80%E4%B9%88%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C%EF%BC%9F)。网络入口容量与攻击流量准入见[Web 服务如何限制拒绝服务的影响？](#29.%20Web%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%8B%92%E7%BB%9D%E6%9C%8D%E5%8A%A1%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F)。

> [!info]- 来源
> - 默认拒绝、最小权限、每次请求校验权限和对象级授权：[OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)，Recommendations（Deny by Default、Validate the Permissions on Every Request、Prefer Attribute and Relationship Based Access Control over RBAC）与 Ensure Lookup IDs Are Not Accessible Even When Guessed or Cannot Be Tampered With，核对于 2026-11-12。
> - 多租户运行时隔离与租户上下文：[AWS Well-Architected SaaS Lens, Preventing cross-tenant access](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/preventing-cross-tenant-access.html)，核对于 2026-11-12。该文是云厂商架构指导，不是通用标准。
> - SQL 参数绑定与动态标识符允许列表：[OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)，Primary Defenses，核对于 2026-11-12；Python 3.11 `sqlite3` 的 `?` 参数绑定：[Python 3.11 sqlite3 documentation](https://docs.python.org/3.11/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries)，核对于 2026-11-12。
> - SQLite 支持由多个列组成的主键：[SQLite CREATE TABLE](https://www.sqlite.org/lang_createtable.html#the_primary_key)，§3.5，核对于 2026-11-12。
> - `404` 可以因隐藏禁止资源的存在而返回，且可启发式缓存：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§15.5.4–§15.5.5，2022-06；`private` 和 `no-store` 响应指令的缓存范围与隐私限制：[IETF RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html)，§5.2.2.5、§5.2.2.7、§6、§7.3，2022-06；均核对于 2026-11-12。
> - “排队后撤权就拒绝执行”是本合成案例选择的任务策略；队列协议不替应用决定任务以受理时权限还是执行时权限为准。任务记录与成员关系检查由文中 SQLite 示例具体展示。
## 6. 浏览器安全控制分别保护什么信任边界？

**案例背景。** 认证层已确认请求主体是 `user-17`；他是 `tenant-a` 的 `reader`，可读取租户甲的报表 42，报表内容为合成数据 `Service health`。页面由 `https://console.example.test` 提供，API 位于 `https://api.example.test`。API 设置 host-only 会话 Cookie `__Host-api-session`；本文讨论的登录态和权限均是案例输入，不代表浏览器控制本身会授予访问权。另有不可信的旧子域 `https://legacy.example.test`，用于检查“同站”是否足以代表可信。本例中用户直接打开这个旧子域页面，它是浏览器的顶层页面。

这些地址共用 `example.test`，只用于讲解。下面依次跟着一次连接、一段不可信标题、一项书签变更和一次跨源读取，看这些控制分别在何处生效：

| 边界 | 控制与成立条件 | 失败时会怎样 | 它不负责什么 |
| --- | --- | --- | --- |
| 网络链路 | HTTPS 的证书身份验证与 TLS 加密传输 | 验证失败时连接应终止或显示证书错误；若退回明文，链路保护消失 | 识别应用用户或决定用户能否读报表 |
| 页面解释数据 | 用适合目标上下文的安全 DOM 接口或编码；富文本另行消毒 | 不可信标记被 HTML 解析后，可能生成元素、事件处理器或可执行脚本 | 限制已经运行的同源脚本 |
| Cookie 自动发送 | CSRF token 或经审查的来源验证在服务端、状态变更前执行 | Cookie 仍可能随请求到达；防护失败会让伪造操作进入业务逻辑 | 认证本身、对象授权或脚本注入 |
| 浏览器跨源读取 | 预检时允许请求方法与请求头；实际响应的来源和凭据字段匹配请求 | 预检失败时浏览器不发后续的非简单请求；实际响应检查失败时脚本读不到响应 | 拦住所有请求、保护非浏览器客户端或授权报表 |
| 页面嵌入 | 报表响应的 CSP `frame-ancestors` 允许每个祖先来源 | 浏览器拒绝在不允许的祖先页面中呈现该页面 | API、附件和后台任务的服务端权限 |

### 网络连接如何保护数据并认证服务端？

本例使用带服务器证书的 HTTPS；Transport Layer Security (传输层安全协议，TLS) 在 HTTP 之下保护连接。浏览器验证链路上的证书身份与目标主机匹配，并成功完成 TLS 握手后，TLS 保护该连接上后续应用数据的机密性和完整性；证书身份匹配说明客户端连到预期服务端。错误证书、主机名不匹配或握手失败时，浏览器不能把该连接当作正常受保护的会话。证书撤销状态依赖客户端与部署所用的机制及其新鲜度，不应假设浏览器会在每个请求上即时查询撤销状态。

TLS 只保护浏览器到服务端的传输。它不知道请求当前代表 `user-17`，也不判断 `report 42` 属于哪个租户。即使 HTTPS 完全正常，API 仍须验证会话，并按当前主体和租户逐项授权。

### 不可信报表标题怎样安全显示？

Cross-Site Scripting (跨站脚本攻击，XSS) 发生在不可信数据变成可执行内容时。Document Object Model (文档对象模型，DOM) 是浏览器页面中的节点树。假设报表 42 的标题是 ` <img src=x onerror=alert(1)> `。`textContent` 会把它作为普通字符放进一般的标题元素；`innerHTML` 则把字符串交给 HTML 片段解析器。若图像加载失败且内联事件处理器没有被有效策略拦下，解析出的 `onerror` 可以运行。

![同一报表标题经 textContent 成为字符，经 innerHTML 则会被解析为可触发事件的图像元素](../../engineering-foundations/security/resources/web-browser-security-boundaries-xss.svg)

所以普通文本应使用框架默认安全的文本插值或一般元素的 `textContent`。需要把值放入 HTML 属性时，固定元素和属性名，并使用该属性上下文对应的编码；HTML 属性编码不会验证 URL 的语义，例如是否允许 `javascript:`。不要把不可信值拼进脚本、事件处理器、CSS 规则、标签名或属性名。只有产品确实支持用户撰写富文本时，才用维护中的 HTML 消毒器过滤允许的元素和属性；清理后再改写内容可能重新引入风险。框架的 raw HTML 入口仍需这些检查；不要把不可信字符串交给 `document.write`、`eval` 或 `new Function`，文本插值的安全性不会传递给这些解析或执行入口。

Content Security Policy (内容安全策略，CSP) 的脚本指令可以限制内联脚本或脚本来源，降低某些注入的可利用性；这属于纵深防御，不能让 `innerHTML` 变成安全文本接口。如果在 `console.example.test` 展示的标题已执行恶意脚本，它通常能以控制台页面的权限调用该源可用的接口；若 API 也允许该 origin 通过 CORS 读取，脚本还可能带着浏览器凭据读取 API 响应。`HttpOnly` 只阻止脚本直接读取 Cookie 值，不阻止它调用 `fetch` 让浏览器代为发送 Cookie。因此仍需修复注入点并在 API 检查每个资源。

### Cookie 自动发送时，怎样防止伪造变更？

Cross-Site Request Forgery (跨站请求伪造，CSRF) 利用浏览器自动携带的登录凭据，让另一个页面发起用户没有意图执行的变更。

Origin (源) 由协议、主机和端口组成；site (站点) 采用 schemeful site 判定，端口不参与比较，同一可注册域下的 HTTPS 子域属于同站。于是 `https://legacy.example.test` 与 `https://api.example.test` 是不同 origin，却是同 site。子域可由不同团队、租户或旧系统控制，因此“同站”不能当作同源或可信身份的替代物。

会话 Cookie 示例为：

~~~http
Set-Cookie: __Host-api-session=<opaque-session-id>; Path=/; Secure; HttpOnly; SameSite=Lax
~~~

`__Host-` 要求 `Secure`、`Path=/` 且不带 `Domain`，所以旧子域不能把这个 Cookie 的作用域扩大到 API 主机。但用户登录 API 后，浏览器会在目标主机、路径、Secure 要求及其他 Cookie 发送条件都匹配时，自动把它附加到发往 `api.example.test` 的请求。控制旧子域的脚本不必读取该 Cookie，就可能借用户现有会话发起请求。Cookie 怎样建立会话见[Cookie 会话与 OIDC 令牌怎样建立身份？](#4.%20Cookie%20%E4%BC%9A%E8%AF%9D%E4%B8%8E%20OIDC%20%E4%BB%A4%E7%89%8C%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E8%BA%AB%E4%BB%BD%EF%BC%9F)。

为了具体展示状态变化，本节的合成 API 另允许 `reader` 维护自己的报表书签；这不授予 `report:refresh` 或 `report:export`。书签初始为未置顶 (`pinned=false`)，这个示例端点接受 `application/x-www-form-urlencoded` 表单编码，并将 `pinned=true` 解释为置顶。旧子域提交下面的普通表单：

~~~html
<form action="https://api.example.test/api/tenants/tenant-a/reports/42/bookmark" method="post">
  <input name="pinned" value="true">
</form>
<script>document.forms[0].submit();</script>
~~~

两个页面都是 HTTPS 且同站，所以即使 Cookie 设置为 `SameSite=Lax`，发往 API 的同站表单 POST 仍可附带会话 Cookie。这个表单请求使用浏览器可直接提交的格式，不需要 CORS 预检。攻击页面不需要读回响应，副作用就可能发生。

下面用服务端精确检查 `Origin` 的变体画出结果；CSRF token 是正文随后说明的另一种防伪机制。两条分支比较同一个未置顶书签在两种实现下的结果。

![同站旧子域的表单 POST 带 Cookie 到达 API；认证和动作授权之后，来源校验拦下变更，漏检则将书签置顶](../../engineering-foundations/security/resources/web-browser-security-boundaries-csrf.svg)

API 仍要先从有效 Cookie 会话得到 `user-17`，再检查该主体是否能执行这项书签操作，然后验证与当前会话绑定的 CSRF token，或执行经审查的等价来源校验。应用先选定并贯彻自己的校验策略：要求 token 的接口拒绝缺少或无效 token；图中的来源校验变体只接受精确的控制台 origin，并拒绝缺失、`null` 或不匹配的来源值。两者都应在变更前拒绝，书签保持 `pinned=false`；这个校验只说明请求通过了该防伪机制，不证明用户表达了操作意图。若用 token 作为主要校验，传统表单必须提交攻击者无法跨源取得的有效 token。

显式设置为 `SameSite=Lax` 通常会限制真正跨站的不安全方法请求，但允许符合规则的顶层安全方法导航携带 Cookie；因此 GET 等安全方法不能改状态。它也不拦截上面的同站子域请求。若合法流程确实需要在 Lax 排除的跨站上下文中发送 Cookie，才考虑 `SameSite=None; Secure`；浏览器的第三方 Cookie 政策仍可能限制它，而且应用仍须单独防 CSRF。若同源 XSS 已执行，恶意脚本可能读取页面里的 token 或调用正常请求接口，不能把 CSRF token 当作 XSS 修复。

### 同源策略如何控制跨源响应读取？

same-origin policy (同源策略，SOP) 默认限制页面脚本读取另一个 origin 的页面或响应。API 可用 Cross-Origin Resource Sharing (跨源资源共享，CORS) 明确开放 Fetch 响应；这是对浏览器默认读取限制的受控放行。

控制台脚本访问独立 API 时，浏览器依据目标 URL、Cookie 属性和 Fetch 凭据模式决定 Cookie 是否符合发送条件。跨 origin 的 Fetch 默认不带目标源 Cookie；本例显式使用 `credentials: "include"`。Cookie 值仍由浏览器管理，脚本不能手动设置 `Cookie` 请求头，也不能读取 `Set-Cookie` 响应头。

```javascript
const response = await fetch('https://api.example.test/api/tenants/tenant-a/reports/42', {
  credentials: 'include',
  headers: { 'X-Report-View': 'compact' },
});
```

`X-Report-View` 不是 CORS safelisted request header。假设没有可用的预检缓存，浏览器先发不带用户 Cookie 的预检，请 API 声明此来源、方法、请求头和凭据模式是否可被共享：

```http
OPTIONS /api/tenants/tenant-a/reports/42 HTTP/1.1
Host: api.example.test
Origin: https://console.example.test
Access-Control-Request-Method: GET
Access-Control-Request-Headers: x-report-view
```

API 同意本例控制台读取时，可对预检返回：

```http
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://console.example.test
Access-Control-Allow-Methods: GET
Access-Control-Allow-Headers: X-Report-View
Access-Control-Allow-Credentials: true
Vary: Origin
```

![带自定义头的 Fetch 在无预检缓存时先发不带 Cookie 的 OPTIONS；预检通过才允许实际 GET，否则 Fetch 拒绝](../../engineering-foundations/security/resources/web-browser-security-boundaries-cors.svg)

预检通过后，浏览器才发送实际 GET。由于 Cookie 由 API 主机设置且本例两个 HTTPS 子域同站，若其余 Cookie 条件符合，实际请求可以带上它：

```http
GET /api/tenants/tenant-a/reports/42 HTTP/1.1
Host: api.example.test
Origin: https://console.example.test
Cookie: __Host-api-session=<opaque-session-id>
X-Report-View: compact
```

服务器此时仍须认证 Cookie、确认 `user-17` 当前属于 `tenant-a` 并有 `report:read`，再按租户与 ID 读取 42。仅在允许分享该结果时，实际响应本身才返回匹配的 CORS 字段：

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: private, no-store
Access-Control-Allow-Origin: https://console.example.test
Access-Control-Allow-Credentials: true
Vary: Origin

{"id":42,"title":"Service health","status":"ready"}
```

![实际 GET 已到 API 并经过身份和资源授权；响应的 CORS 字段再决定脚本能否读到状态和正文](../../engineering-foundations/security/resources/web-browser-security-boundaries-cors-response.svg)

对于 `credentials: "include"` 的请求，响应必须使用精确允许的 origin 和小写字面值 `true`，不能用 `Access-Control-Allow-Origin: *`。即便服务器返回了 `200`，若实际响应缺少匹配的允许来源或 `Access-Control-Allow-Credentials`，Fetch 会以 `TypeError` 拒绝，脚本拿不到这个响应的状态和正文；请求本身可能已经抵达并完成读取。隐藏式 `404` 若也要由控制台识别，同样需要可读的 CORS 响应字段：此时 Fetch 正常返回 `Response`，`response.status === 404` 且 `response.ok === false`，不是 CORS 导致的网络错误。相反，若预检响应不允许请求头或来源，浏览器不会发送这个带自定义头的后续 GET，Fetch 也以 `TypeError` 拒绝。没有预检的简单表单请求则可能先到服务器，所以两条失败路径都不能代替 API 的身份和授权检查。

CORS 是浏览器将跨源响应分享给脚本的协议，不是通用网络防火墙，不限制 `curl` 等客户端，也不替服务端授权。动态选择 `Access-Control-Allow-Origin` 时，`Vary: Origin` 让 HTTP 缓存区分不同来源的表示；它不区分同一个来源下的不同用户。对本例的私人报表，`Cache-Control: private, no-store` 表示合规 HTTP 缓存不得保存响应；这是缓存存储指令，不是服务端授权或绝对隐私保证。若产品需要可缓存表示，则要按 HTTP 缓存规则设计，并确保用户范围不会被别人的请求复用。`Vary: Origin` 本身不保护私有数据。若部署允许把 API 反向代理到页面同源的 `/api/`，可以省去这次跨源读取协商；会话也须能在控制台主机建立，因为 API 主机原有的 host-only Cookie 不会发给控制台主机。身份认证与资源授权仍照常执行。

> [!info] Fetch 对 Cookie 字段的边界
> 浏览器按目标 URL 和 Cookie 政策管理 `Cookie` 请求字段；网页脚本不能用 Fetch/XHR 手动设置它。`Set-Cookie` 是禁止暴露给脚本的响应字段，增加 `Access-Control-Expose-Headers` 也不能让网页读取该字段，无论 Cookie 是否设置了 `HttpOnly`。

### 什么时候限制页面被嵌入？

点击劫持会把真实页面放进攻击者控制的框架，再诱导用户点错位置。报表页面可以通过 HTTP 响应头限制哪些祖先来源可嵌入它：

~~~http
Content-Security-Policy: frame-ancestors 'self'
~~~

策略只允许同源祖先；任意一层祖先来源不匹配时，浏览器拒绝在该框架中呈现报表。必须用响应头发送 `frame-ancestors`；放进 `meta` 元素不会生效。旧客户端兼容需要可另评估 `X-Frame-Options`，并按目标浏览器验证策略。嵌入控制保护报表界面不被伪装成按钮，但不会阻止攻击者直接请求 API，也不会替 API 检查报表 42 的权限。

WebSocket 握手不使用 CORS 的响应字段来授权。浏览器会在握手中发送 `Origin`；服务端应按允许来源校验它，并验证连接身份。非浏览器客户端可以伪造或省略 `Origin`，所以它不能代替认证。连接建立也不等于对所有动作有权；每条读取或变更消息仍按资源和动作授权。双向消息与断线恢复见[何时选择轮询、SSE、流式 Fetch 或 WebSocket？](#19.%20%E4%BD%95%E6%97%B6%E9%80%89%E6%8B%A9%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)。

**接下来：** TLS 保护网络链路；安全呈现控制数据如何进入页面解释器；CSRF 防护验证自动附带 Cookie 的变更请求；CORS 决定脚本能否读取跨源响应；CSP 的 `frame-ancestors` 限制页面嵌入方。它们都不改变身份层已经确认的主体，也不取代[对报表 42 的服务端逐次授权](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

> [!info]- 来源
> - TLS 1.3 的握手认证与数据机密性、完整性：[IETF RFC 9846](https://datatracker.ietf.org/doc/html/rfc9846)，2026-07，§§2、4.5、5.2；服务器身份与目标主机匹配：[RFC 9525](https://www.rfc-editor.org/rfc/rfc9525.html)，2023-11，§§1.1、6；证书撤销没有完整且高效的通用检查方案：[RFC 9325](https://www.rfc-editor.org/rfc/rfc9325.html)，2022-11，§7.5。均核对于 2026-11-12。RFC 9846 已取代 RFC 8446。
> - Chromium 的 CRLSet 更新与浏览器端撤销数据示例：[Chromium CRLSet](https://www.chromium.org/Home/chromium-security/crlsets/)，核对于 2026-11-12。客户端采用的状态机制及新鲜度因实现而异。
> - origin 的协议、主机、端口及 same-site 的 schemeful site 判定：[WHATWG HTML Standard](https://html.spec.whatwg.org/multipage/browsers.html#origins)，Living Standard，2026-11-12，§7.1.1。
> - Cookie 作用域、`__Host-` 前缀和 `SameSite` 请求条件：[HTTPWG Cookies Internet-Draft](https://httpwg.org/http-extensions/draft-ietf-httpbis-rfc6265bis.html)，2026-11-12 draft，§§4.1.3.2、5.6.7；它仍是工作草案。Cookie 被 Fetch 如何处理另见 [WHATWG Fetch Standard](https://fetch.spec.whatwg.org/#cookies)，Living Standard，2026-10-19。
> - DOM 安全呈现、上下文编码、危险上下文、富文本消毒以及 CSP 的 XSS 纵深防御：[OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)，Safe Sinks、Output Encoding、Dangerous Contexts、HTML Sanitization、Other Controls，核对于 2026-11-12。
> - Cookie 认证状态变更的 CSRF token、Origin/Referer 校验和 SameSite 的限制：[OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)，Synchronizer Token、Defense in Depth、SameSite 与 Origin Validation，核对于 2026-11-12；SameSite 规则同时见上一条 Cookie 草案 §5.6.7。
> - 预检、CORS 凭据和 CORS 检查：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/#cors-protocol)，Living Standard，2026-10-19，§§3.3.1–3.3.5、4.8–4.10；`Cookie` / `Set-Cookie` 字段限制见 §§2.2.2、3.1。
> - HTTP 缓存的 `private`、`no-store` 与共享缓存约束：[IETF RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html)，2022-06，§§3–4、5.2.2.5、5.2.2.7。
> - `frame-ancestors` 的祖先匹配与禁止通过 `meta` 声明：[W3C Content Security Policy Level 3](https://www.w3.org/TR/CSP3/#directive-frame-ancestors)，Working Draft，2026-10-27，§6.4.2。
> - WebSocket 握手 `Origin` 字段、非浏览器客户端可自行提供来源值：[IETF RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)，§§1.6、4.1、10.1–10.2，2011-12；来源允许列表、连接认证和消息级授权：[OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html)，Authentication and Authorization，核对于 2026-11-12。
## 7. SQL 空值、连接与分组会怎样改变报表 42 的结果？

**案例：** 报表 42 按客户汇总一小组已付款和待付款订单。为便于手算，输入已经限定为账户 `acct-17` 的四客户、四订单切片。`customers` / `orders` 表省略账户和报表列；本页解释 SQL 查询语义，不展示租户过滤或授权。

语义以 PostgreSQL 18 官方文档核对，四客户 SQL 例另用本机 SQLite 3.51.0 复现；SQLite 对 `IS DISTINCT FROM` 的支持从 3.39.0 开始。

Ava 有两笔订单，Ben 的地区和一笔订单金额未知，Cy 有一笔已付款订单，Dia 没有订单。追踪查询时，可以把它的**逻辑结果阶段**看成 `FROM / JOIN` 形成行、`WHERE` 筛行、`GROUP BY` 形成组、聚合计算、`HAVING` 筛组。它帮助解释 SQL 结果；PostgreSQL 计划器可以用不同的物理执行计划算出同一结果。

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

SQL 使用 three-valued logic（三值逻辑）：普通比较可能是 TRUE、FALSE 或 UNKNOWN。`NULL = NULL` 与 `NULL <> 'North'` 都是 UNKNOWN。`WHERE` 只留下 TRUE，因此 `region = NULL` 搜不到 Ben；空值判断要写 `IS NULL`。 在本页的 PostgreSQL 和 SQLite 文本列中，空字符串 `''` 是已知的空文本，`'' IS NULL` 为 FALSE；它与未知值 NULL 不同。

本例中，`region <> 'North'` 单独用于 `WHERE` 时只选中 South；要连未知地区也纳入“不是 North 或未知”，再把 `IS NULL` 用 OR 合并：

| region | `<> 'North'` | `IS NULL` | `OR` | WHERE 保留？ |
| --- | --- | --- | --- | --- |
| North | FALSE | FALSE | FALSE | 否 |
| South | TRUE | FALSE | TRUE | 是 |
| NULL（Ben） | UNKNOWN | TRUE | TRUE | 是 |

~~~sql
SELECT name FROM customers WHERE region = NULL;
-- 空结果：比较为 UNKNOWN，WHERE 丢弃

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
-- Cy
~~~

坏例 `region = NULL` 按 PostgreSQL 默认 `transform_null_equals = off` 解释。若打开这个兼容开关，PostgreSQL 只会把裸 `NULL` 的等号形式 `expression = NULL` 或 `NULL = expression` 改写为 `expression IS NULL`；显式写 `IS NULL` 才不会依赖该开关。SQLite 例子不受它影响。

`IS DISTINCT FROM` 把 NULL 当作一个可比较状态：Ben 的 NULL 与 `'North'` 不同，条件为 TRUE。PostgreSQL 18 和 SQLite 3.39.0 及更新版本都支持它；更早的 SQLite 可用 `region <> 'North' OR region IS NULL` 表达“不是 North 或地区未知”。若业务问题实际是“地区已知且不是 North”，则只保留 Cy；先选定是否包含未知值，再写条件。

> [!info] 先判断“未知”是否等于“零”
> Ben 的缺失金额可能表示尚未计价、上游未回填或数据质量错误；自动当成 0 会抹去区别。只有报表定义明确把“没有金额输入”解释成零贡献时，才用 `COALESCE`。

### 左外连接的筛选条件放在哪里？

`LEFT JOIN`（左外连接）先用 `ON` 判断哪些左右行相配；客户没有任何匹配订单时，仍保留客户行，并把订单列补成 NULL。若问题是“列出每位客户和其已付款订单，同时保留没有已付款订单的客户”，应把付款条件放进 `ON`：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id AND o.status = 'paid'
ORDER BY c.customer_id;
~~~

如果先按客户号连接所有订单，再在 `WHERE` 筛 `o.status = 'paid'`，筛选是在空扩展行产生之后执行：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
ORDER BY c.customer_id;
~~~

| 条件位置 | 结果行 | 行数与原因 |
| --- | --- | --- |
| `o.status = 'paid'` 在 `ON` | Ava–101、Ben–103、Cy–104、Dia–NULL | 4 行。Ava 的 pending–102 不匹配；Dia 没有付款订单，仍得到右侧为 NULL 的保留行。 |
| `o.status = 'paid'` 在 `WHERE` | Ava–101、Ben–103、Cy–104 | 3 行。Dia 的 NULL 与 `'paid'` 比较为 UNKNOWN，筛选时被丢弃。 |

把条件从 `ON` 移到 `WHERE` 改变了行集，并把这条查询变成“只保留存在已付款订单的客户和订单”。结果不是客户去重列表：Ava 出现几次取决于符合条件的订单数。

报表 42 要汇总 paid 与 pending 两种订单，因此分组查询必须重新连接**全部**订单，不沿用上面的付款过滤。这个完整连接的中间结果是 5 行：

~~~sql
SELECT c.customer_id, c.name, o.order_id, o.amount_cents, o.status
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
ORDER BY c.customer_id, o.order_id;
~~~

| customer_id | customer | order_id | amount_cents | status |
| ---: | --- | ---: | ---: | --- |
| 1 | Ava | 101 | 1200 | paid |
| 1 | Ava | 102 | 800 | pending |
| 2 | Ben | 103 | NULL | paid |
| 3 | Cy | 104 | 500 | paid |
| 4 | Dia | NULL | NULL | NULL |

Ava 出现两行，是因为她有两笔不同订单；她的每笔订单金额各进入一次组内求和。Dia 的一行是外连接补出的记录，不是真实订单。后续要数订单就数非空主键 `o.order_id`；不能把左连接后的 `COUNT(*)` 当作客户数或真实订单数。

### 计数与求和各自统计什么？

在原始 `orders` 表中，`COUNT(*)` 统计四行，`COUNT(amount_cents)` 只统计三个非空金额；已知金额小计是 `1200 + 800 + 500 = 2500`。Ben 的一笔订单金额为 NULL，所以它不会被金额计数或加进总和。

~~~sql
SELECT COUNT(*) AS order_rows,
       COUNT(amount_cents) AS priced_orders,
       SUM(amount_cents) AS total_cents
FROM orders;
~~~

| order_rows | priced_orders | total_cents |
| ---: | ---: | ---: |
| 4 | 3 | 2500 |

左连接后按客户分组，依次看连接行数、真实订单数、金额非空的订单数和总金额：

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
~~~

| 客户 | 连接行 | 订单数 | 有金额订单 | 合计（分） |
| --- | ---: | ---: | ---: | ---: |
| Ava | 2 | 2 | 2 | 2000 |
| Ben | 1 | 1 | 0 | NULL |
| Cy | 1 | 1 | 1 | 500 |
| Dia | 1 | 0 | 0 | NULL |

`COUNT(*)` 数的是分组中的连接行，所以 Dia 的空扩展行也计为 1；`COUNT(o.order_id)` 才排除它并数到 0 笔订单。Ben 有一笔真实订单，但没有非空金额。`SUM` 只加非空输入；一个组没有任何非空金额时，结果是 NULL，而不是 0。若报表合同明确要把“无有效金额”显示为零，可用 `COALESCE(SUM(o.amount_cents), 0)`；否则保留 NULL 能与零金额区分。

还要区分“组里没有非空金额”和“没有组”：对 `orders` 过滤 `customer_id = 4` 后没有输入行；无 `GROUP BY` 的全局聚合仍返回一行，按客户分组则没有组可输出。

| WHERE 后的输入 | 分组与输出 | 计数（`COUNT(*)` / `COUNT(amount_cents)`） | `SUM(amount_cents)` |
| --- | --- | ---: | ---: |
| 没有订单行 | 无 `GROUP BY`，有一行整体汇总 | 0 / 0 | NULL |
| 没有订单行 | 按 `customer_id` 分组，无组、无结果行 | — | — |
| 一行真实订单，金额为 NULL | 按 `customer_id` 分组，有一组 | 1 / 0 | NULL |
| 一行真实订单，金额为 0 | 按 `customer_id` 分组，有一组 | 1 / 1 | 0 |

报表查询里 Dia 会保留，是因为 `LEFT JOIN` 先为她造出一行空扩展记录；因此 Dia 有组，`COUNT(*) = 1`，而非“订单表没有该组”的零行状态。

这不是所有聚合函数都会丢弃 NULL：例如 PostgreSQL 的 `array_agg` 会把 NULL 收入数组。本例只有客户到订单这一层，一笔订单只进入所属客户组一次；若再连接一张按订单有多行的标签表，同一订单金额就会随标签行重复。

单独看这个重复风险：暂时只取 Ava 的两笔订单，并给它们补三个合成标签关联；这是 fan-out 的小例，不是报表 42 的新增业务表：

~~~sql
WITH ava_orders(order_id, amount_cents) AS (
    VALUES (101, 1200), (102, 800)
), order_tags(order_id, tag) AS (
    VALUES (101, 'priority'), (101, 'gift'), (102, 'gift')
)
SELECT COUNT(o.order_id) AS joined_order_rows,
       COUNT(DISTINCT o.order_id) AS orders,
       SUM(o.amount_cents) AS naive_total_cents
FROM ava_orders AS o
JOIN order_tags AS t USING (order_id);
-- 3 | 2 | 3200
~~~

订单 101 的 1,200 分随两个标签出现两次，102 的 800 分出现一次，所以连接后 SUM 为 3,200，实际订单总额仍是 2,000。`COUNT(DISTINCT order_id)` 可在此查询中数回两笔订单，但 `SUM(DISTINCT amount_cents)` 不是通用修复：不同订单可能恰好有相同金额。要按客户安全地合并多个子表，先分别把每个子表汇总到 `customer_id` 粒度、保证每位客户至多一行，再连接这些汇总结果。

### 分组前后两种筛选各在何时执行？

`WHERE` 过滤连接产生的行，`GROUP BY` 把剩余行按客户合并，聚合函数计算组值，`HAVING` 再过滤组。下面只保留金额总和至少 500 分的客户：

~~~sql
SELECT c.name,
       COUNT(o.order_id) AS orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING SUM(o.amount_cents) >= 500
ORDER BY c.customer_id;
~~~

| 客户 | orders | total_cents | 保留原因 |
| --- | ---: | ---: | --- |
| Ava | 2 | 2000 | 求和至少 500。 |
| Cy | 1 | 500 | 边界值 500 满足 `>= 500`。 |

Ben 和 Dia 的 `SUM` 都是 NULL；NULL 与 500 比较为 UNKNOWN，因此两组都不满足 HAVING。要得出正确报表，先确认统计粒度、金额缺失的业务含义和哪些订单状态应参与，再把条件放在正确的 `ON`、`WHERE` 或 `HAVING` 阶段。

**接下来：** 数据库怎样用外键、唯一约束和索引保护报表记录与读取？见[如何用约束保护业务规则并为读取建立索引？](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F)。并发写入、提交和恢复又有哪些边界？见[事务隔离与预写日志能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - NULL 比较、`IS NULL` 与 `IS DISTINCT FROM`：[PostgreSQL 18, Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html)，§9.2；SQLite 3.39.0 加入兼容谓词：[SQLite Release 3.39.0](https://www.sqlite.org/releaselog/3_39_0.html)，核对于 2026-11-12。
> - PostgreSQL 的 `transform_null_equals` 默认关闭，只改写与裸 `NULL` 的 `=` 比较（`expression = NULL` 或 `NULL = expression`）：[Version and Platform Compatibility](https://www.postgresql.org/docs/18/runtime-config-compatible.html#GUC-TRANSFORM-NULL-EQUALS)，§19.13.2，核对于 2026-11-12。
> - LEFT JOIN 的匹配、NULL 扩展与 `ON` / `WHERE` 的差异：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.1–7.2.2；SQLite [SELECT](https://www.sqlite.org/lang_select.html)，§2，核对于 2026-11-12。
> - `FROM`、WHERE、GROUP BY、HAVING 的逻辑表转换：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.2–7.2.3；物理计划可因查询而异：[Planner/Optimizer](https://www.postgresql.org/docs/18/planner-optimizer.html)，§51.5，核对于 2026-11-12。
> - `COUNT(*)`、`COUNT(expr)`、SUM 的非空输入与空结果：[PostgreSQL 18, Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html)，§9.21；SQLite [Built-in Aggregate Functions](https://www.sqlite.org/lang_aggfunc.html)，核对于 2026-11-12。
## 8. 如何用约束保护业务规则并为读取建立索引？

**案例：** 报表服务接收账户 `acct-17`、主体 `user-17` 的幂等请求 `report-demo-208`，持久化任务 `job-demo-731`，之后按账户读取最近任务。数据库要保证库存不可为负、外键指向真实父行、同一作用域的报表键最多对应一行；读取任务列表时，索引则提供一个可能更省成本的路径。

本页的业务 schema 与索引说明以 **PostgreSQL 18** 为准；前一篇库存事务明确使用 PostgreSQL 18 Read Committed。这里的 `report-demo-208` 是报表操作键，`reserve-demo-208` 是另一篇库存案例的操作键，两者只是合成标识，不代表同一次业务操作。约束是所有写入方共享的数据规则；索引是需额外维护的查询结构，是否采用由计划器按成本决定。

### 先把不变量放在数据库边界

下面是一个**独立教学 schema**：它包含库存案例中的 `inventory` 与 `reservations`，并额外加入 `accounts` 父表及 `reservations.account_id` 外键，说明账户、SKU 和报表任务如何关联。不要在已按库存篇创建过同名表的数据库里原样重跑这些 `CREATE TABLE`。本例的 `principal_id` 是存储的作用域值，没有主体表外键；身份认证和访问授权不由这个字段或外键自动完成。

~~~sql
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY
);

CREATE TABLE inventory (
    sku TEXT PRIMARY KEY,
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
    job_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')
    ),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT report_jobs_idempotency_scope_key
        UNIQUE (account_id, principal_id, idempotency_key)
);

INSERT INTO accounts (account_id) VALUES ('acct-17');
INSERT INTO inventory (sku, available) VALUES ('SKU-7', 1);
~~~

![关系图仅列出键和约束相关字段：账户与库存为父表，箭头指向预留或报表任务的外键列；reservations 的 principal_id 属于复合主键，report_jobs 的 principal_id 属于作用域唯一键，两者都没有主体外键](../../engineering-foundations/databases/resources/database-constraints-and-indexes-schema.svg)

约束分别保护不同的不变量：

| 要保护的事实 | 示例约束 | 它能保证什么 |
| --- | --- | --- |
| 每个账户、SKU、任务 ID 只对应一行 | `PRIMARY KEY` | 主键是唯一且非空的行标识；即使显式省略 `NOT NULL`，PostgreSQL 主键列也不接受 NULL。 |
| 库存有已知、非负的数值 | `available NOT NULL CHECK (available >= 0)` | 两条规则须并用：CHECK 结果为 TRUE 或 NULL 都算通过，单独 CHECK 不能拒绝 NULL。 |
| 子记录引用已有账户或 SKU | `REFERENCES` | 本例引用父表主键所标识的已有行。默认删除动作是 `NO ACTION`；级联删除须显式声明。 |
| 每个作用域操作键最多保存一条记录 | 复合主键或 `UNIQUE` | `reservations` 用复合主键；`report_jobs` 用任务 ID 主键和操作作用域唯一约束。 |
| 状态值来自允许集合 | `CHECK (status IN (...))` | 只限制当前值，不验证 `queued → running → succeeded` 之类的转移顺序。 |

PostgreSQL 的 `UNIQUE` 默认把含 NULL 的键视作彼此不同；需要把 NULL 也视为相同键时可用 `NULLS NOT DISTINCT`。此 schema 中唯一键每列都声明为 `NOT NULL`，因此操作键比较没有这个歧义。主键和唯一约束会自动建立唯一 B-tree 索引，不要再为相同键重复建一个索引。外键会使用父表主键/唯一键的索引查找父行；PostgreSQL 不会自动为子表的外键列建索引。这里的 `reservations` 主键和 `report_jobs` 作用域唯一索引都以 `account_id` 开头，已有索引可用于账户前缀查找和父账户变更时的子行检查。`reservations.sku` 不在主键索引中；若按 SKU 查预留或删除/更新库存 SKU 时需检查大量子行，可按负载评估单独的 `reservations(sku)` 索引。

CHECK 表达式检查的是当前行，不能可靠表达跨行或跨表不变量；应优先使用 UNIQUE、外键等约束，或把需要协调的写入放进合适的事务协议。`created_at TIMESTAMPTZ` 表示一个时间点：带时区的输入会换算后按 UTC 存储，原时区标签不保留，输出按会话时区显示；混合格式的本地时间文本不能直接当作可靠时间顺序。

在本例 DDL 中，唯一和外键约束未声明 `DEFERRABLE`，因此使用 PostgreSQL 默认的立即检查方式；CHECK 与 NOT NULL 在行插入或更新时立即检查。显式事务里若立即约束报错，当前事务进入失败状态，应用需回滚，或回滚到先前建立的 savepoint，才能继续执行。不能把这句话泛化到所有数据库：例如 SQLite 默认的 ABORT 冲突策略撤销失败语句的更改，但保留同一事务中之前语句的更改。

幂等键的唯一约束只裁决“最多一行”，本身不规定重放返回什么。报表 API 的应用契约是：成功持久化的任务才绑定键；已接受请求以相同键、相同参数重放时，返回已存任务 `job-demo-731` 及其当前状态查询入口；同键不同 `period` 或 `format` 则返回参数冲突。若并发请求先查无记录，那个语句快照只说明当时没有可见的已提交行，不能证明另一个事务尚未提交的任务不存在；最终由写入约束裁决。

例如，任务首次写入时，下面的 `INSERT` 是一条语句，其 `$1` 到 `$5` 由该语句单独绑定：

~~~sql
BEGIN ISOLATION LEVEL READ COMMITTED;
INSERT INTO report_jobs
    (job_id, account_id, principal_id, idempotency_key,
     request_fingerprint, status, created_at)
VALUES ($1, $2, $3, $4, $5, 'queued', now());
COMMIT;
~~~

本例首次 `INSERT` 的绑定为 `$1 = job-demo-731`、`$2 = acct-17`、`$3 = user-17`、`$4 = report-demo-208`、`$5 = fingerprint-A`。以下并发重放分支假设 B 为本次尝试生成新的候选任务 ID `job-demo-732`；它与 A 的其他作用域参数、指纹相同：

~~~sql
BEGIN ISOLATION LEVEL READ COMMITTED;
INSERT INTO report_jobs
    (job_id, account_id, principal_id, idempotency_key,
     request_fingerprint, status, created_at)
VALUES ($1, $2, $3, $4, $5, 'queued', now());
-- 这里是 B 并发 INSERT；A 的同键 INSERT 尚未提交。
~~~

B 这条 `INSERT` 的独立绑定是 `$1 = job-demo-732`、`$2 = acct-17`、`$3 = user-17`、`$4 = report-demo-208`、`$5 = fingerprint-A`。A 和 B 的 INSERT 是两条语句，各自从 `$1` 开始绑定；B 使用新的候选任务 ID，让此例只考察作用域键唯一约束。

| A 的事务结果 | B 等待中的 INSERT | B 接下来做什么 |
| --- | --- | --- |
| A 提交 `job-demo-731` | B 收到 `report_jobs_idempotency_scope_key` 冲突 | 回滚 B 的失败事务，再开新事务按作用域键回查。 |
| A 回滚 | 唯一键冲突消失，B 的 INSERT 可成功 | 提交 B 的事务，键绑定到 `job-demo-732`。 |

只有明确识别为 `report_jobs_idempotency_scope_key` 的冲突才是同键重放的查询线索。`job_id` 主键冲突也会产生 SQLSTATE `23505`，但它是任务 ID 冲突，不能仅凭同一错误码当作同键重放；应用应检查 PostgreSQL 错误诊断中的约束名。即使作用域键冲突，也要回查指纹才能区分重放与换参数。

若 B 因作用域唯一键冲突，先回滚失败事务，再在新事务回查。查询是另一条语句，重新从 `$1` 开始绑定账户、主体和操作键；SQL 位置参数不会跨语句共享一组编号。

~~~sql
ROLLBACK;

BEGIN ISOLATION LEVEL READ COMMITTED;
SELECT job_id, request_fingerprint, status, created_at
FROM report_jobs
WHERE account_id = $1
  AND principal_id = $2
  AND idempotency_key = $3;
COMMIT;
~~~

这条 recovery `SELECT` 的绑定独立为 `$1 = acct-17`、`$2 = user-17`、`$3 = report-demo-208`。本例重放结论假定重放窗口内绑定行仍被保留、作用域键未变。A 已提交时读到的是现有 `job-demo-731`，不是第二条已提交记录；同指纹复用该任务，异指纹返回参数冲突。若 A 回滚，B 的 INSERT 可继续而无需读到 A 的记录。具体 HTTP 重放与响应丢失契约见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)；库存的键绑定和失败不占键见[两个请求争夺最后一件库存时，怎样保证只预留一次？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。

### 复合索引怎样配合任务列表？

调用方已获得查看账户 `acct-17` 全部任务的授权，现在读取该账户最近 20 个任务，同一创建时间用任务 ID 决定稳定顺序：

~~~sql
CREATE INDEX report_jobs_by_account_recent
    ON report_jobs (account_id, created_at DESC, job_id DESC);

SELECT job_id, status, created_at
FROM report_jobs
WHERE account_id = $1
ORDER BY created_at DESC, job_id DESC
LIMIT 20;
~~~

这条查询自己的 `$1` 绑定为 `acct-17`。B-tree 按复合键的字典序排列：前导列 `account_id` 的等值条件通常最有效，能直接定位这个账户的键区间；`created_at DESC, job_id DESC` 随后给出该区间内要求的次序和稳定并列顺序。

| 索引键 | 查询中的作用 | 本例边界 |
| --- | --- | --- |
| `account_id` | `WHERE account_id = $1` 限定账户区间 | PostgreSQL 18 的多列 B-tree 也能利用非前导列条件或 skip scan；只是前导列等值条件通常更直接、更有效。 |
| `created_at DESC` | 在账户范围内按最近时间先读 | 匹配的 B-tree 可以避免另做排序，但计划器仍会比较它与顺序扫描加排序的成本。 |
| `job_id DESC` | 为相同时间的任务提供确定顺序 | 查询排序须与索引能够提供的列序和方向匹配；B-tree 也可反向扫描，不要求索引声明与查询方向逐字相同。 |
| `status` | 只在 SELECT 输出 | 本索引没有 `status`，需要从表行取值；它不是覆盖该查询的索引。 |

若计划器选择匹配的索引，`LIMIT 20` 可在收集到 20 条可见结果后停止继续取行；MVCC 可见性等条件可能使它检查多于 20 个索引项。它不保证只读前 20 个物理项，也不保证计划器必选索引。若查询需读取整表很大比例，顺序读表再排序可能更便宜。

索引列序应从过滤和排序需求推导，字段越多不等于越快。每个索引占磁盘和缓存，并增加写入和后续清理的维护成本；给表加索引后还需用目标数据库的真实数据、统计信息与 `EXPLAIN` 检查查询计划。`EXPLAIN ANALYZE` 会实际执行语句，评估有写入副作用的语句时要考虑它真的会改数据。

### 计划器为什么有时不用已建索引？

计划器比较不同访问路径的估算成本，不会因为索引存在就必定选它。前面的 PostgreSQL 列表索引已建好后，本机 PostgreSQL 14.24 两行小表的计划器估算后选择了顺序扫描加排序；数据、统计信息、目标版本都会影响计划。接着保留一个独立 SQLite 教学库：它的 `orders` 与下一篇 NULL / join 章节的同名表结构不同，需分别建表。这里合成 1,000 个订单，`customer_id = 17` 对应 10 行（`order_id` 为 17、117、……、917），再观察索引前后的查询计划。

> [!example]- 两行表上已有索引但仍选择顺序扫描（本地 PostgreSQL 14.24）
> 下面的两条任务插入到前面刚创建的 `report_jobs` 教学表；复现时表中只有这两行，查询用字面量绑定账户值：
>
> ~~~sql
> INSERT INTO report_jobs VALUES
>     ('job-demo-731', 'acct-17', 'user-17', 'report-demo-208',
>      'fingerprint-A', 'queued', '2026-11-10 12:00:00+00'),
>     ('job-demo-730', 'acct-17', 'user-17', 'report-demo-207',
>      'fingerprint-B', 'running', '2026-11-11 12:00:00+00');
> ANALYZE report_jobs;
>
> EXPLAIN (COSTS OFF)
> SELECT job_id, status, created_at
> FROM report_jobs
> WHERE account_id = 'acct-17'
> ORDER BY created_at DESC, job_id DESC
> LIMIT 20;
> ~~~
>
> 本机实际计划：
>
> ~~~text
> Limit
>   ->  Sort
>         Sort Key: created_at DESC, job_id DESC
>         ->  Seq Scan on report_jobs
>               Filter: (account_id = 'acct-17'::text)
> ~~~
>
> 对这两行表，PostgreSQL 14.24 的计划器估算后仍选了 `Seq Scan → Sort`，虽然匹配过滤和排序的索引已经存在。这是该版本、数据集和统计信息下的一次实际计划，不表示测得顺序扫描耗时更低，也不代表 PostgreSQL 18 或更大数据集会作出相同选择。

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
> -- SQLite 3.51.0：SCAN orders；USE TEMP B-TREE FOR ORDER BY
>
> CREATE INDEX orders_by_customer_and_time
>     ON orders(customer_id, placed_at);
>
> EXPLAIN QUERY PLAN
> SELECT order_id, amount_cents, placed_at
> FROM orders
> WHERE customer_id = 17
> ORDER BY placed_at DESC;
> -- SQLite 3.51.0：SEARCH orders USING INDEX orders_by_customer_and_time (customer_id=?)
> ~~~

本地 SQLite 3.51.0 实际输出显示：无索引时全表 `SCAN` 并用临时 B-tree 排序；创建 `(customer_id, placed_at)` 后改为按 `customer_id` 的索引 `SEARCH`，在等值筛出的客户区间内按索引反向读取以满足 `placed_at DESC`。这验证了该引擎、该数据集上的路径和排序变化，不是 PostgreSQL 的计划，也没有测量查询耗时或证明端到端延迟必然下降。查询取出 `amount_cents`，但索引不含该列，所以也不是覆盖索引。SQLite 的 `EXPLAIN QUERY PLAN` 输出是面向调试的描述，版本升级时格式可能变化。

**接下来：** 事务如何将扣库存与操作记录一起提交，见[事务隔离与预写日志能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。NULL、外连接与聚合会如何改变报表行数，见[SQL 空值、连接与分组会怎样改变报表 42 的结果？](#7.%20SQL%20%E7%A9%BA%E5%80%BC%E3%80%81%E8%BF%9E%E6%8E%A5%E4%B8%8E%E5%88%86%E7%BB%84%E4%BC%9A%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E6%8A%A5%E8%A1%A8%2042%20%E7%9A%84%E7%BB%93%E6%9E%9C%EF%BC%9F)。

> [!info]- 来源
> - 主键、唯一、外键、删除动作和 CHECK/NULL 语义：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)，§5.5；`TIMESTAMPTZ` 的输入、存储与显示：[Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html)，§8.5，核对于 2026-11-11。
> - 可延迟约束类型与立即检查边界：[PostgreSQL 18, SET CONSTRAINTS](https://www.postgresql.org/docs/18/sql-set-constraints.html)，核对于 2026-11-11。
> - 显式事务的原子性与失败后 `ROLLBACK` / savepoint 边界：[PostgreSQL 18, Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html)，§3.4；[ROLLBACK](https://www.postgresql.org/docs/18/sql-rollback.html)，核对于 2026-11-11。
> - 唯一索引检查会等待未提交竞争者并按其提交/回滚结果重检：[PostgreSQL 18, Index Uniqueness Checks](https://www.postgresql.org/docs/18/index-unique-checks.html)，§63.5；唯一违规可读取约束名等错误诊断字段，PK 与 UNIQUE 冲突都属 `23505`：[Error Codes](https://www.postgresql.org/docs/18/errcodes-appendix.html)，Appendix A，核对于 2026-11-11。
> - 报表任务 API 的同键重放、指纹与查询入口契约：[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)，库存键策略另见[库存事务页](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。
> - 多列 B-tree 的前导列、后续列与 skip scan：[PostgreSQL 18, Multicolumn Indexes](https://www.postgresql.org/docs/18/indexes-multicolumn.html)，§11.3；索引排序和 `ORDER BY` / `LIMIT`：[Indexes and ORDER BY](https://www.postgresql.org/docs/18/indexes-ordering.html)，§11.4，核对于 2026-11-11。
> - 索引维护成本与计划器取舍：[PostgreSQL 18, Indexes](https://www.postgresql.org/docs/18/indexes.html)，§11.1；索引更新和统计信息：[Indexes Introduction](https://www.postgresql.org/docs/18/indexes-intro.html)，§11.1；估算计划和实际执行的区别：[EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)，核对于 2026-11-11。
> - SQLite 默认 ABORT 的语句级回滚范围：[SQLite, The ON CONFLICT Clause](https://www.sqlite.org/lang_conflict.html)；`SCAN`、`SEARCH` 和计划输出格式边界：[EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)；多列索引同时筛选和排序：[Query Planning](https://www.sqlite.org/queryplanner.html)，§§2.2、3.1，核对于 2026-11-11。
## 9. 事务隔离与预写日志能保证什么？

**案例背景。** 库存服务同时收到两份来自账户 `acct-17`、主体 `user-17` 的请求，预留同一件 `SKU-7`。库存初值 `available = 1`，此前没有该操作键的预留记录。本例使用 PostgreSQL 18 的 Read Committed（读已提交）隔离级别，要求一次库存扣减与该操作记录一起提交。

两份请求代表同一逻辑操作，都携带稳定键 `reserve-demo-208` 和指纹 `fingerprint-A`。指纹是参与业务决定的参数（账户、主体、SKU 与操作内容）的稳定摘要，用来判断重复键是否仍代表原请求。成功事务保存 `SKU-7 / reserved` 结果，以便重复请求读取并返回；本例只保存成功结果。

`inventory.sku` 唯一标识库存行，`available` 是非负整数。`reservations` 的 `(account_id, principal_id, idempotency_key)` 复合唯一约束保证同一主体下的操作键只保存一份成功记录。连接超时只说明调用方没收到结论，不代表数据库已经回滚。

![两份同键请求争用最后库存的 Read Committed 时序](../../engineering-foundations/databases/resources/d4-transaction-reserve-race.svg)

时序中的 A 先锁定并扣减库存，再写 `SKU-7 / reserved` 结果并提交；B 等待同一行锁。A 提交后，PostgreSQL Read Committed 会按最新库存重检 B 的更新条件，B 得到零行，回滚尝试后用新事务查询同键结果。若 A 回滚，B 可在锁释放后继续并成为成功者。最终库存为 0、只存在一条成功预留记录；两份同键同指纹请求返回同一成功状态。若两份请求使用不同操作键，且 B 的键原先无记录，B 的查询不会找到 A 的结果，应返回库存不足。

### 事务把哪些写入放在同一边界？

transaction（事务）把多条数据库语句放进同一次提交或回滚。ACID 是描述该边界的常用词，但每项都受数据库实现、配置与底层存储能力约束：

- **atomicity（原子性）**：同一事务中的写入一起提交，或由回滚一起撤销。
- **consistency（一致性）**：数据库约束和应用规则定义合法状态；事务不会自行发明业务不变量。
- **isolation（隔离性）**：并发事务按数据库实现的隔离级别观察或等待其他写入。
- **durability（持久性）**：成功提交能够抵抗配置和存储承诺范围内的故障；异步提交或不可靠存储会改变这个范围。

先读 `available = 1` 再无条件写成 0 不安全。例如两份不同操作各自先读到 1，再无条件把库存设为 0 并分别插入不同操作键，最终库存仍显示 0，却有两条成功预留。条件扣减保护库存不变量；复合唯一键则保护同一逻辑操作不会保存两份结果。下面使用 PostgreSQL 参数绑定；`$1 = SKU-7`、`$2 = acct-17`、`$3 = user-17`、`$4 = reserve-demo-208`、`$5 = fingerprint-A`，字段沿用[库存基础页](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)的 schema：

~~~sql
BEGIN;

UPDATE inventory
SET available = available - 1
WHERE sku = $1 AND available > 0
RETURNING available;
-- 应用取回结果：一行时继续 INSERT；零行时立即 ROLLBACK，不能执行 INSERT。

INSERT INTO reservations
    (account_id, principal_id, idempotency_key,
     request_fingerprint, sku, status)
VALUES ($2, $3, $4, $5, $1, 'reserved');

COMMIT;
~~~

若 INSERT 或其他写入因约束或数据库错误失败，PostgreSQL 事务进入失败状态；应用显式 `ROLLBACK`，不能继续尝试 `COMMIT`，并按错误类别返回或报告失败。`40001` 是整笔事务从开头重试的序列化失败；COMMIT 时连接响应丢失则是提交结果未知，不能当作普通失败处理。

如果本次条件更新返回零行，或插入因复合操作键冲突而失败，应用回滚这个事务，然后在新事务按 `(account_id, principal_id, idempotency_key)` 查询。查到相同指纹就返回已保存的当前结果——本例是 SKU-7 的 `reserved` 记录；指纹不同则冲突。在普通条件更新失败的路径中，若本次返回零行，且新事务回查也没有该键的已提交记录，就返回本次未预留、库存不足；这同样适用于重试此前没有保存结果的失败请求。失败结果没有持久写入，所以库存之后变化时，失败请求是否复用同一键由上层协议定义。

若 COMMIT 响应丢失，查到同键同指纹记录可确认已提交；查不到只说明这次查询没有看到提交记录，原事务仍可能在执行或提交中，不能当作失败后换新键再做一次业务操作。保留原键与同一指纹，沿相同条件更新和唯一约束路径安全重试，或稍后再次查询。复合键只在数据库中裁决并发写入，不会自动生成重放响应。完整请求重放与故障分支见[两个请求争夺最后一件库存时，怎样保证只预留一次？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。

### 隔离级别限制哪些并发现象？

dirty read（脏读）是读到其他事务尚未提交的写入；non-repeatable read（不可重复读）是同一事务重读一行时看到后来提交的新值；phantom read（幻读）是相同条件查询再次执行时，结果行集合因其他提交而变化；serialization anomaly（序列化异常）是一组成功事务的结果无法解释为某种串行执行顺序。SQL 标准以现象规定隔离级别最低限度要防止什么；数据库对同一名称可以提供更强保证，也可能采用不同的并发控制实现。

| PostgreSQL 18 级别 | 脏读 | 不可重复读 | 幻读 | 序列化异常 |
| --- | --- | --- | --- | --- |
| Read Uncommitted（读未提交） | 不发生；等同 Read Committed | 可能 | 可能 | 可能 |
| Read Committed（读已提交，默认） | 不发生 | 可能 | 可能 | 可能 |
| Repeatable Read（可重复读） | 不发生 | 不发生 | 不发生 | 仍可能出现写偏差 |
| Serializable（可串行化） | 不发生 | 不发生 | 不发生 | 不发生 |

在 PostgreSQL Read Committed 下，每条语句取得新快照。两个请求同时以 `WHERE available > 0` 更新同一 SKU 时，后执行者会等待；前者提交后，数据库用新行版本重检条件，库存已是 0，就更新零行。若前者回滚，等待者可继续更新旧值。这让单条条件更新直接表达“库存不能低于零”。在 Repeatable Read 下，事务若试图修改它的快照之后已被另一事务提交修改的同一行，会以 SQLSTATE `40001` 失败；应用要从最初读取开始重试整笔事务。PostgreSQL 的 Repeatable Read 快照始于事务中第一条非事务控制语句；隔离级别名称不是实现说明，例如下一页的 InnoDB Repeatable Read 以首次一致性读快照与索引锁协作。

> [!info] MVCC 不等于“无锁读取”
> multi-version concurrency control（多版本并发控制，MVCC）让快照读取按可见性规则选择版本；在 PostgreSQL 中，更新行会产生新 tuple 版本，旧快照仍可读到对它可见的已提交版本。这能减少部分读写等待，但不消除写写冲突：像本例 B 更新同一库存行仍会等待，Repeatable Read 冲突也可能失败；`FOR UPDATE` 等显式锁和其他资源等待同样仍会发生。各引擎保留、清理旧版本的实现不同；PostgreSQL 的 VACUUM 清理不再对活动快照可见的旧 tuple，长时间持有旧快照会延迟清理。

### 为什么稳定快照仍可能破坏共享规则？

write skew（写偏差）说明稳定快照不一定维护跨行规则。排班表有医生 A、B 两行，规则要求至少一人值班。事务 T1 读到两人都在岗后关闭 A 的排班；事务 T2 读到相同快照后关闭 B。两者修改不同的行，因此 PostgreSQL Repeatable Read 下都可能提交，最终没人值班。

修法取决于规则形状。可把规则改成单行值班人数，用条件更新维护计数，并在同一事务更新计数和医生行；也可在 Read Committed 下让所有写方先锁同一排班控制行，再用下一条 SELECT 检查状态。若 T1 关闭 A，T2 等控制行锁释放后，下一条语句取得新快照并看到只剩 B 在岗，于是拒绝关闭 B。Repeatable Read 的快照从事务中第一条非事务控制语句开始，等待不会刷新它，不能照搬这个两语句方案。另一选项是让所有维护这条规则的并发事务都运行 Serializable；若发生 `40001`，失败方从事务开头重试，看到只剩一人后放弃关闭。只重试最后一条 UPDATE 会沿用旧决策。

事务中不要执行无法撤销的远端支付或直接发布消息。可以在同一数据库事务写 outbox（发件箱）记录，提交后再异步投递；业务更新和待发送记录由数据库原子提交，但消息投递仍可能重复，消费者要能去重或幂等处理。开发时也应避免在事务中等待长时间网络调用。

### 预写日志如何把提交与数据页写回分开？

write-ahead log（预写日志，WAL）先记录数据页更改，再允许对应数据页写回持久存储。以 PostgreSQL 本地同步提交为例，默认 `synchronous_commit = on` 且 `fsync = on` 时，服务器在成功确认前会持久化提交所需的 WAL；被修改的数据页可以在提交前或提交后写回，只要写页前相应 WAL 已持久。并发小事务还可能共用一次 WAL 刷盘。这样不必在每次提交时同步刷新所有受影响的数据页。

下图把成功事务的提交路径与数据页写回分开。条件为 `synchronous_commit = on`、`fsync = on`，且存储正确兑现 flush（持久化刷新）。

![同步提交先持久化所需 WAL，数据页可独立写回](../../engineering-foundations/databases/resources/d4-postgresql-wal-commit.svg)

下面的崩溃分支沿用开场状态：SKU-7 初始为 1、没有 `reserve-demo-208`，A 与 B 是此库存上的全部写入尝试，期间没有其他库存写者。这个前提使“无提交记录”能归因到两份请求都未成功；若另有写者，库存值不能只归因于 A/B。

![PostgreSQL WAL 提交点与崩溃恢复分支](../../engineering-foundations/databases/resources/d4-postgresql-wal-crash.svg)

如果至少一份尝试的提交记录已持久而数据页尚未写回，恢复会重放所需 WAL，使库存扣减与一条预留记录可见。若 A、B 两份尝试都没有持久提交记录，启动恢复仍可能重放数据页修改记录；重放本身不等于提交，未提交的库存新版本对查询不可见，未提交的预留行也不可见，因此查询仍读到旧库存 1 且没有预留。PostgreSQL 的这一例子是本地单节点崩溃恢复，不是跨故障域复制保证。把 `synchronous_commit` 设为 `off` 会缩短等待，却允许刚确认的事务在数据库崩溃时丢失（不应因此损坏其他已提交数据）；下游若按成功响应执行外部动作，就不能忽略这段风险。任何持久性保证仍依赖文件系统、设备与控制器正确兑现 flush。

WAL 也不是时间点恢复的全部材料。要恢复到过去时点，还需要适用的基础备份，以及从该备份起点到目标时刻连续、完整的 WAL 归档；若有一段缺失，就不能从这份备份跨过缺口恢复，之后另有适用基础备份时仍可有新的恢复范围。SQLite 有自己的回滚日志与 WAL 模式及配置，不能把 PostgreSQL 的文件布局和恢复步骤直接套用。

> [!example] 一次提交后立即崩溃时检查什么
> 在“只有 A/B 两份竞争尝试、期间没有其他库存写入”的前提下，若其中一份成功事务已按同步策略持久提交，即使数据页尚未写回，崩溃恢复也能重做库存扣减与预留记录；恢复后读到 `available = 0` 和一条 `reserved` 操作记录。若两份尝试都没有持久提交记录，恢复后的查询仍看到旧库存 `available = 1` 且没有该预留。若 API 在提交确认前失联，查到同键记录可确认成功；暂时查不到不证明原事务已经结束，应保留原键处理。HTTP 响应不是数据库提交记录。

### 哪些课程细节继续留在归档？

课程中的 ARIES 恢复推演仍保留在[WAL 与 ARIES 的逐步恢复例题](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md)：analysis（分析）阶段用 dirty page table（脏页表）记录恢复时涉及的脏页；每页的 recLSN 表示该页自上次干净后可能需要 REDO（重做）的最早日志位置，所有页中最小 recLSN 是 REDO 起点，不是分析阶段要扫描的最早日志范围。ARIES 的 repeat-history 后接 loser undo 是通用课程算法；这里的 PostgreSQL WAL 说明不表示 PostgreSQL 或 InnoDB 按原版 ARIES 执行恢复。

CAP 讨论分布式系统的故障边界：网络分区时，系统无法同时保证 linearizability（线性一致性）与 availability（可用性，即每个非故障节点收到的请求最终都得到响应）。two-phase commit（两阶段提交，2PC）协调多个参与者的提交决定；进入 prepared 并投赞成票的参与者仍持有锁，在获知全局提交或回滚决定前可能等待。这些机制都不能代替单库的库存约束、隔离或日志恢复。

**接下来：** 这里的并发例是 PostgreSQL Read Committed。要看同名隔离级别在另一引擎中如何由 read view、索引记录锁、redo 和 undo 落地，见[InnoDB 怎样用索引记录、旧版本与日志处理库存事务？](#10.%20InnoDB%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%B4%A2%E5%BC%95%E8%AE%B0%E5%BD%95%E3%80%81%E6%97%A7%E7%89%88%E6%9C%AC%E4%B8%8E%E6%97%A5%E5%BF%97%E5%A4%84%E7%90%86%E5%BA%93%E5%AD%98%E4%BA%8B%E5%8A%A1%EF%BC%9F)。SQL 约束与索引决定哪些业务状态可写、哪些访问路径可用，见[如何用约束保护业务规则并为读取建立索引？](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F)；ORM 的 Session、事务与连接持有时间见[如何限定 ORM Session 并诊断连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。

> [!info]- 来源
>
> - 隔离现象定义、PostgreSQL 18 的各级别保证、Read Committed 等待后重检、Repeatable Read 冲突后整笔重试、Serializable 检测：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2，核对于 2026-11-12；`UPDATE ... RETURNING` 只返回实际更新的行：[PostgreSQL 18, UPDATE](https://www.postgresql.org/docs/18/sql-update.html)；`COMMIT` 使事务改动对其他会话可见并按数据库持久策略保证崩溃后保留：[PostgreSQL 18, COMMIT](https://www.postgresql.org/docs/18/sql-commit.html)，核对于 2026-11-12。
>
> - “Repeatable Read”名称不规定同一引擎策略：[MySQL 8.4, Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)，§17.7.2.1；普通快照读与锁定读分别观察 read view 和最新状态，对照 [MySQL 9.7 的同一章节](https://dev.mysql.com/doc/refman/9.7/en/innodb-transaction-isolation-levels.html)，核对于 2026-11-12。
>
> - 快照可见性、VACUUM 与旧版本清理：[PostgreSQL 18, Introduction to MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html)，§13.1；旧版本清理：[Routine Vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html)，§24.1.2，核对于 2026-11-12。
>
> - WAL 先持久于相关数据页、崩溃重放与基础备份加连续日志的时间点恢复：[PostgreSQL 18, WAL Introduction](https://www.postgresql.org/docs/18/wal-intro.html)，§28.3；同步与异步提交的确认差异：[Asynchronous Commit](https://www.postgresql.org/docs/18/wal-async-commit.html)，§28.4；检查点刷页：[WAL Configuration](https://www.postgresql.org/docs/18/wal-configuration.html)，§28.5；PITR：[Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/18/continuous-archiving.html)，§25.3，核对于 2026-11-12。
>
> - SQLite 的独立事务机制：[SQLite Transactions](https://www.sqlite.org/lang_transaction.html) 与 [Write-Ahead Logging](https://www.sqlite.org/wal.html)，核对于 2026-11-12。
>
> - 课程 ARIES 推导与原始机制：[Mohan et al., ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging)；关联课程页[WAL 与 ARIES 的逐步恢复例题](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md)。CAP 原始证明：[Gilbert and Lynch, Brewer’s conjecture and the feasibility of consistent, available, partition-tolerant web services](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf)；prepared 事务会继续持锁，需外部协调器最终发出 COMMIT PREPARED 或 ROLLBACK PREPARED：[PostgreSQL 18, PREPARE TRANSACTION](https://www.postgresql.org/docs/18/sql-prepare-transaction.html)，§Description and Caution，核对于 2026-11-12。
## 10. InnoDB 怎样用索引记录、旧版本与日志处理库存事务？

**案例背景。** 全局 `SKU-7` 库存只剩一件，`available = 1`，此前没有 `reserve-demo-208` 结果。账户 `acct-17`、主体 `user-17` 是预留请求的作用域，不是库存分区；A、B 是同一逻辑请求的两次尝试，操作键为 `reserve-demo-208`，指纹为 `fingerprint-A`。指纹应是规范化业务参数的稳定摘要；这里用 `fingerprint-A` 作符号标签，省略实际摘要编码。会话 A 开启可重复读（`REPEATABLE READ`）事务并先用普通读建立快照，看到 1；会话 B 用条件更新扣成 0，在同一事务保存该操作键和指纹后提交。A 之后的普通读仍可能看到旧值 1，但锁定读和更新会针对当前记录。要判断“能读旧值”是否意味着“还能安全扣减”，必须分清 InnoDB 的索引路径、一致性读、当前锁定读以及崩溃恢复决策。

本文以 MySQL 8.4 长期支持（LTS）版本、InnoDB 为准：普通事务默认隔离级别为可重复读（`REPEATABLE READ`），示例仍显式设定；`sku_id = 7` 表示 `SKU-7`。单条独立 SQL 使用自动提交（`autocommit=1`），需要跨语句加锁的片段会显式开启事务。事务隔离与预写日志（WAL）的通用语义见[事务隔离与预写日志能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)；这里的快照、索引锁范围和 `undo log`（回滚日志）/`redo log`（重做日志）是 InnoDB 具体行为。

### 查询先走哪棵 InnoDB 索引？

本例用主键点查 SKU-7，并另外建仓库库存二级索引。InnoDB 的主键组织为 clustered index（聚簇索引），叶记录保存整行；每个 secondary index（二级索引）叶项保存二级键列与该行主键。若二级索引查询还需要 `note` 这样的非索引列，InnoDB 会用叶项中的主键再回聚簇索引取行。投影列都在二级索引记录里时，查询在字段层面可被覆盖；但 multi-version concurrency control（多版本并发控制，MVCC）的可见性检查仍可能要查聚簇记录。

> [!example]- 示例表结构和初始数据
>
> ~~~sql
> CREATE TABLE inventory (
>     sku_id INT NOT NULL PRIMARY KEY,
>     warehouse_id VARCHAR(16) NOT NULL,
>     available INT NOT NULL CHECK (available >= 0),
>     note VARCHAR(64) NOT NULL
> ) ENGINE = InnoDB;
>
> CREATE INDEX inventory_by_warehouse_stock
>     ON inventory (warehouse_id, available);
>
> CREATE TABLE reservations (
>     account_id VARCHAR(32) NOT NULL,
>     principal_id VARCHAR(32) NOT NULL,
>     idempotency_key VARCHAR(64) NOT NULL,
>     request_fingerprint CHAR(64) NOT NULL,
>     sku_id INT NOT NULL,
>     status VARCHAR(16) NOT NULL,
>     PRIMARY KEY (account_id, principal_id, idempotency_key),
>     FOREIGN KEY (sku_id) REFERENCES inventory(sku_id)
> ) ENGINE = InnoDB;
>
> INSERT INTO inventory VALUES
>     (5,  'W-2', 2, 'point-query neighbor'),
>     (7,  'W-1', 1, 'last unit'),
>     (9,  'W-2', 2, 'point-query neighbor'),
>     (10, 'W-1', 5, 'range example'),
>     (11, 'W-1', 4, 'range example'),
>     (13, 'W-2', 2, 'range example'),
>     (20, 'W-2', 1, 'range example');
> ~~~

![InnoDB 主键与二级索引的候选访问路径](../../engineering-foundations/databases/resources/d4-innodb-index-path.svg)

`WHERE sku_id = 7` 是完整唯一主键点查，找到聚簇索引里的完整行。若用 `WHERE warehouse_id = 'W-1' AND available >= 1` 筛选仓库库存，优化器可能选择 `(warehouse_id, available)` 二级索引；若只取 `sku_id, available`，这些投影列都在二级项里，字段层面可覆盖查询。但若二级项已被标为删除，或二级索引页包含快照之后的更新，InnoDB 仍可能回聚簇记录核对 MVCC 可见性，再由 undo 重建旧版。例如 B 把 SKU-7 的 `available` 从 1 改成 0 后，二级项 `(W-1,1,7)` 会被标记删除；A 的旧视图即使只取 `sku_id, available`，也可能按主键查回旧值。若还取 `note`，则无论如何都要按 `sku_id` 查聚簇索引。索引是否实际使用取决于谓词、统计信息、数据分布和投影列，生产排查应看 `EXPLAIN`，不能从 WHERE 子句直接猜计划。

### 普通读为什么能看见已过时库存？

InnoDB 的 consistent read（一致性读）使用 read view（读视图）确定查询时点。在 `REPEATABLE READ` 下，同一事务的普通非锁定 `SELECT` 使用第一次一致性读建立的快照。若此后另一个事务更新了行，undo log（回滚日志）保留重建旧版所需的信息，普通读可以据此仍返回旧值；它也会看见本事务此前语句写入的变更。普通 `SELECT` 不锁住被读行，其他事务仍可更新。这是 MVCC 允许读者沿快照读取、写者修改当前版本的一种实现；读写等待可因此减少，但写写冲突、显式锁和所有等待并没有消失。

锁定读和 DML（data manipulation language，数据操作语言）语句不必服从这个普通读快照：`SELECT ... FOR UPDATE` 是 current read（当前读），读取最新可用记录并取得排他锁；`UPDATE` 同样要按当前可修改版本协调锁。下面按固定的双会话顺序推演，库存初始为 1：

~~~sql
-- 会话 A：先建立一致性读视图
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT available FROM inventory WHERE sku_id = 7;
-- 结果 1；这是之后普通 SELECT 的快照时点。

-- 会话 B：使用当前库存完成同一逻辑操作
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
UPDATE inventory
SET available = available - 1
WHERE sku_id = 7 AND available > 0;
-- 应用检查受影响行数：若为 0，立即 ROLLBACK 并结束尝试；不执行 INSERT。
-- 只有影响恰好 1 行，应用才继续 INSERT。
INSERT INTO reservations
    (account_id, principal_id, idempotency_key,
     request_fingerprint, sku_id, status)
VALUES
    ('acct-17', 'user-17', 'reserve-demo-208',
     'fingerprint-A', 7, 'reserved');
-- 只有 UPDATE 影响 1 行且 INSERT 成功，应用才走成功分支：
COMMIT; -- 成功分支才执行
-- 若 INSERT 因重复键或其他约束/写入错误失败，不能继续 COMMIT。
-- InnoDB 通常只回滚失败语句；
-- 应用必须显式 ROLLBACK 整笔事务，撤销前面的库存扣减。
-- 重复操作键错误：整笔回滚后用新事务按作用域键回查，再比较指纹。
~~~

会话 B 提交后，会话 A 仍在原事务中继续：

~~~sql
-- 普通一致性读：沿旧读视图，仍是 1。
SELECT available FROM inventory WHERE sku_id = 7;

-- 当前锁定读：最新值是 0，同时锁定该索引记录。
SELECT available FROM inventory WHERE sku_id = 7 FOR UPDATE;

UPDATE inventory
SET available = available - 1
WHERE sku_id = 7 AND available > 0;
-- 影响 0 行；不能按快照中的 1 再扣一次，也不插入预留记录。
ROLLBACK;

-- 回滚后以新事务确认同键请求的已提交结果。
START TRANSACTION;
SELECT request_fingerprint, sku_id, status
FROM reservations
WHERE account_id = 'acct-17'
  AND principal_id = 'user-17'
  AND idempotency_key = 'reserve-demo-208';
COMMIT;
-- 同键同指纹：返回已保存的业务结果；同键异指纹：报告操作键冲突。
-- 查询仍无记录时，竞争事务可能尚未结束；不把空结果当作另一事务已失败。
~~~

若 `INSERT` 因复合主键重复而失败，MySQL/InnoDB 通常只回滚这条语句，之前成功的库存 `UPDATE` 仍在原事务里。因此应用必须先 `ROLLBACK` 整个尝试，之后才能在新事务查键和指纹；同键同指纹返回已有业务结果，同键异指纹返回操作键冲突。若其他约束或写入错误导致失败，也整笔回滚并按具体错误返回，不能沿失败路径照常 `COMMIT`。竞争事务仍在执行时，新事务暂时查空也不是“对方已经失败”的证据，应保留原键并重试/重查。

![旧快照读、当前锁定读和条件更新的结果](../../engineering-foundations/databases/resources/d4-innodb-snapshot-current-read.svg)

这里的旧值是“普通读仍可见的版本”，不是可用来再次扣减的当前库存。读视图按事务可见性判断聚簇记录的版本；只要 A 的快照仍可能需要旧值，update undo 就不能清理。在本例 B 已提交、A 条件更新影响零行的顺序下，若 A 与 B 是不同操作键，A 在回滚后查不到自己的键，应报告本次库存不足；同键同指纹才返回 B 保存的结果，同键异指纹则返回冲突。若回查为空，也可能是同键竞争事务尚未结束，不能仅凭一次空结果断言对方失败。若 B 仍未提交而 A 先执行 `FOR UPDATE`，A 会等待 B 提交或回滚：在没有其他写入的本例中，B 提交则看到 0，B 回滚则看到 1。通常不应在 `REPEATABLE READ` 同一事务中随意混合普通快照读与锁定读；此处是为了展示两条读取路径为何得出不同值。完整的原请求重试与幂等键约定见[库存扣减与同键重试如何保证只生效一次？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。

### 唯一命中与范围扫描为什么锁不同？

InnoDB 的行锁实际落在索引记录上。若完整唯一索引等值条件只命中一条已存在记录，通常只锁该索引记录，不锁它前面的间隙。若排他搜索经二级索引完成，InnoDB 还会锁对应的聚簇索引记录。复合唯一索引如果只给部分键列，便不是完整唯一命中，可能需要扫描并锁定一段索引范围。

~~~sql
-- 独立示例一：完整主键点查，只锁 sku_id=7 记录。
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT available FROM inventory WHERE sku_id = 7 FOR UPDATE;
ROLLBACK;

-- 独立示例二：完整主键上的范围扫描。
-- 会话 A 保持事务时，会话 B 的 INSERT 15 要等 A 结束。
-- 会话 A
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT sku_id FROM inventory FORCE INDEX (PRIMARY)
WHERE sku_id BETWEEN 10 AND 20
FOR UPDATE;
-- 结果 10、11、13、20；A 暂不结束事务。

-- 会话 B，autocommit=1 的单条 INSERT
INSERT INTO inventory VALUES (15, 'W-1', 2, 'insert in protected gap');
-- 等待 20 记录之前的间隙被释放。

-- 会话 A
COMMIT;
-- A 释放范围锁后，B 才能继续并提交。
~~~

![唯一记录锁与范围 next-key 锁覆盖的索引位置](../../engineering-foundations/databases/resources/d4-innodb-lock-interval.svg)

在这个 `REPEATABLE READ` 主键范围中，记录 20 的 next-key lock（临键锁）由记录锁加其前方 gap lock（间隙锁）组成，保护 `(13, 20]`；要插入的 15 落在该区间，所以 B 等 A 提交或回滚后才继续。间隙锁只抑制冲突插入，不表示这条语句锁住整张表。读已提交（`READ COMMITTED`）下的搜索和扫描通常不使用间隙锁，但外键检查与重复键检查仍可能用；具体范围取决于真正扫描的索引、谓词和计划。遇到等待时先用 `EXPLAIN` 确认访问路径，再看 InnoDB 锁信息。

### 崩溃时 redo 和 undo 各做什么？

redo log（重做日志）为页修改提供恢复记录，能把尚未写回表空间的变更前滚；它也可能记录后来被判为未提交的事务修改。undo log（回滚日志）一方面用于一致性读重建旧版本，另一方面用于撤销未完成事务。因此“redo 重放过页面变化”不等于“业务事务已经提交”。

本例假设 binary log（二进制日志，binlog）已启用，`innodb_flush_log_at_trx_commit = 1`、`sync_binlog = 1`，且文件系统、控制器与设备真实兑现 flush。MySQL 8.4 对启用 binlog 的 InnoDB 表使用隐式 XA two-phase commit（两阶段提交）来协调两个日志：事务执行完更新与预留插入后，InnoDB 的 `PREPARE` 将准备记录写入 redo 日志缓冲区，但调用本身不表示已持久化；组提交刷新阶段先持久化 prepare 及此前的 redo，再把完整事务和 transaction identifier（事务标识符，XID）写入并同步到 binlog；之后 InnoDB 才完成提交。XA 是服务器协调器内部使用的协议，不是应用发出 `XA` SQL。客户端可能在提交已形成后断线，所以是否收到 `COMMIT` 响应不能代替恢复时的日志决策。

![更新、prepare缓冲、redo持久化、binlog同步与InnoDB提交的五步顺序](../../engineering-foundations/databases/resources/d4-mysql-binlog-crash-recovery.svg)

图中的五步只追踪本例单笔事务在各阶段的先后。同组多笔事务可以共用日志刷盘。

从独立初态 `SKU-7.available = 1` 且无 `reserve-demo-208` 开始；假定本例只有 B 这一笔事务修改该库存，没有其他库存写入。组提交中的 redo 刷盘在 binlog 刷新之前，因此恢复时可以用 redo 恢复页及可恢复的事务状态，再用完整、有效的 binlog XID 作事务决策；崩溃发生在步骤 4 中也要看最终是否留下可恢复 XID：没有完整有效 XID 时回滚，有则完成仍 prepared 的提交。分支如下：

![根据完整有效持久XID完成提交或回滚事务](../../engineering-foundations/databases/resources/d4-mysql-crash-decision.svg)

> [!info]- 恢复两条路径的完整条件
>
> | 崩溃时可恢复的提交证据 | 重启恢复路径 | 恢复后的业务状态 |
> | --- | --- | --- |
> | 完整、持久且可恢复的 binlog 事务和 XID 已存在；客户端可能没收到响应 | redo 恢复页面修改；若事务仍处于已准备（prepared）状态，MySQL 通知 InnoDB 完成提交；已完成的提交保持不变 | `available = 0`，操作键记录存在；重试查询可确认结果 |
> | 没有完整、持久且可恢复的 XID；包括步骤 4 期间崩溃而未留下有效 XID | redo 可先重放页面修改；未提交事务用 undo 回滚，若 prepared 事务不在有效 binlog XID 集合中也回滚 | 在没有其他库存写入的前提下，`available = 1`，无该预留记录 |

MySQL 可在 redo 应用后尽早接受新连接，未完成事务回滚可能在后台继续，期间新事务仍可能遇到这些行上的锁等待。若崩溃发生在 binlog XID 已同步、InnoDB 尚未完成提交的窗口，恢复会完成 prepared 事务；若 XID 没有持久化，则恢复会回滚它。两种分支都要求这里设定的日志刷盘条件可信；设备谎报 flush、整盘损坏或故障域丢失都需要备份/复制策略处理。

`innodb_flush_log_at_trx_commit = 1` 使 InnoDB 在事务提交时写并刷 redo；`sync_binlog = 1` 使 binlog 同步到磁盘。Point-in-time recovery（时间点恢复，PITR）仍需合适备份和其后的连续二进制日志；redo/undo 不代替备份。这个 XID 协调与 InnoDB 恢复步骤是 MySQL 的具体实现，不能因同样使用预写日志就称为 PostgreSQL 或课程 ARIES 的同一算法。

若想从通用事务边界、PostgreSQL 隔离异常与 WAL 的角度再看同一库存案例，见[事务隔离与预写日志能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
>
> - 以 MySQL 8.4 LTS 手册和 8.4.13 源码为本页实现基线；另与 MySQL 9.7 手册交叉核对，不把 9.7 称为最新发行版。Oracle 已于 2026-10-20 发布 MySQL 26.10.0：[MySQL 26.10.0 Release Notes](https://dev.mysql.com/doc/relnotes/mysql/26.10/en/news-26-10-0.html)。本页关键声明核对于 2026-11-12。
>
> - 聚簇索引保存完整行，二级索引叶项包含二级键和主键：[MySQL 8.4, Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html) §17.6.2.1；二级项被删除标记或索引页含较新更新时，MVCC 可见性检查可能回到聚簇记录，因此覆盖索引只说明投影字段齐全：[InnoDB Multi-Versioning](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html) §17.3。
>
> - DDL 中 `CHECK (available >= 0)` 的约束语义：[MySQL 8.4, CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html)，§15.1.20.6。
>
> - REPEATABLE READ 首次一致性读建立事务快照、READ COMMITTED 每条一致性读新快照、普通读与 DML/锁定读可能看到不同状态：[MySQL 8.4, Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html) §17.7.2.3 与 [Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html) §17.7.2.1；undo 支持旧版重建：[Undo Logs](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html) §17.6.6。
>
> - 完整唯一索引命中与范围扫描的记录锁、间隙锁、next-key 边界，以及 READ COMMITTED 例外：[MySQL 8.4, InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html) §17.7.1；语句锁范围、二级索引排他搜索时锁对应聚簇记录：[Locks Set by Different SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html) §17.7.3；`FOR UPDATE` 取最新可用记录并持锁到事务结束：[Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html) §17.7.2.4，核对于 2026-11-12。
>
> - 重复键错误通常只回滚失败语句；前面已成功的 UPDATE 仍留在事务中，应用须显式回滚整笔尝试：[InnoDB Error Handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html) §17.20.5，核对于 2026-11-12。
>
> - redo 前滚与不完整事务后台回滚：[MySQL 8.4, InnoDB Recovery](https://dev.mysql.com/doc/refman/8.4/en/innodb-recovery.html) §17.18.2；InnoDB redo 日志：[Redo Log](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html) §17.6.5；PITR 用完整备份后的二进制日志回放：[Point-in-Time Recovery Using Binary Log](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-binlog.html) §9.5.1。
>
> - binlog 与 InnoDB 隐式 XA 两阶段提交、恢复扫描完整 XID 并完成 prepared 事务：[MySQL 8.4, The Binary Log](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html) §7.4.4；8.4.13 源码说明 `prepare()` 将记录先写入日志缓冲，再由组提交刷新阶段先刷新引擎日志：[sql/binlog.cc](https://github.com/mysql/mysql-server/blob/mysql-8.4.13/sql/binlog.cc#L8087-L8116)、[组提交 flush 阶段](https://github.com/mysql/mysql-server/blob/mysql-8.4.13/sql/binlog.cc#L8518-L8525)、[InnoDB redo flush](https://github.com/mysql/mysql-server/blob/mysql-8.4.13/storage/innobase/handler/ha_innodb.cc#L5903-L5940)。`innodb_flush_log_at_trx_commit=1`、`sync_binlog=1` 与 flush 设备假设：[InnoDB System Variables](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html) `innodb_flush_log_at_trx_commit`。同组事务可共用 binlog 同步，见 [Binary Logging Options and Variables](https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html#sysvar_binlog_group_commit_sync_delay) 的 `binlog_group_commit_sync_delay` 和 `sync_binlog`。
>
> - MySQL 9.7 手册交叉核对 Repeatable Read 快照、索引锁策略与 binlog XID 恢复：[Transaction Isolation Levels](https://dev.mysql.com/doc/refman/9.7/en/innodb-transaction-isolation-levels.html) §17.7.2.1；[The Binary Log](https://dev.mysql.com/doc/refman/9.7/en/binary-log.html) §7.4.4，核对于 2026-11-12。此处将 9.7 仅作版本交叉核对；发行版本已到 MySQL 26.10.0。
>
> - PostgreSQL 同名级别使用不同并发行为的对照：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html) §13.2；具体比较见[事务隔离与预写日志能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。
## 11. 怎样限定对象关系映射会话并排查连接池耗尽？

**案例：** 请求读取账户 `acct-17` 的报表 42；worker 也可能为已接受的 `job-demo-731` 分页读取活动。本文用 SQLAlchemy 2.0 和 PostgreSQL 说明四种不同边界：`Session`（会话）跟踪本次对象工作，transaction（事务）界定一组 SQL 的提交或回滚，connection（连接）承载数据库通信，connection pool（连接池）限制并复用并发连接。池耗尽时，先查连接借出多久、为什么没归还，再判断查询或池容量；“数据库慢”不能直接说明是哪一段在慢。

~~~mermaid
flowchart TD
    Work[本例的一次报表查询 / worker 的一页<br/>创建局部 Session 并开始本段事务] --> Need[首次需要连接；本例由 SELECT 触发]
    Need --> Pool{在等待期限内取得连接？}
    Pool -->|是：取空闲、按需新建或等到归还| Q[执行 SQL，并在事务内取完结果]
    Pool -->|否：QueuePool 等待超时| Timeout[关闭 Session；本次访问失败<br/>业务 SQL 未发出；无连接可归还]
    Q -->|成功| C[提交事务]
    Q -->|异常| R[回滚事务]
    C --> Close[释放连接；关闭本段 Session<br/>池有空位则保留，否则关闭物理连接]
    R --> Close
    Close --> Result{事务成功？}
    Result -->|是| Success[交付结果；调用者决定下一页或结束]
    Result -->|否| Failure[传播错误；结束本次访问或 job]
~~~

### 会话、事务和连接各自保存什么状态？

`Session` 保存本次工作中加载或新增的 ORM（对象关系映射）对象、identity map（身份映射）和待写入的变更。身份映射确保同一会话中的主键身份对应同一个 Python 对象；它不会缓存任意查询结果，也不适合跨请求共享。一个 `Session` 是可变的事务状态，不可由并发线程共同使用；`AsyncSession` 也不可被多个并发 Task 共享。并发线程各用自己的局部 `Session`，异步 Task 各用自己的局部 `AsyncSession`，不要把线程池里的 Session 留给之后的请求。

事务是数据库原子操作的边界。`flush()`（刷新）把 Session 中待写入的变化发成 SQL，但仍处于当前事务；正常离开 `session.begin()` 时提交，异常离开时回滚。若数据库在 INSERT 时生成主键，flush 后通常能在对象上读到这个 ID；但在提交前回滚，新增行仍不会成为已提交数据。若 flush 异常从 `session.begin()` 向外传播，事务上下文在退出时回滚；若代码捕获异常后还要复用同一 Session，必须先显式回滚，或关闭并丢弃这个 Session。

`Engine` 长期保存数据库方言、连接建立方式和进程内连接池。Session 一般先保存逻辑事务状态，第一次真正需要数据库连接时，才向 Engine 借一条 DBAPI 连接；本例由执行 SELECT 触发，但调用 `Session.connection()` 也可以在业务 SQL 发出前借出。事务结束后连接归还池。一个 Session 可以先后运行多笔事务，但每笔事务都有自己的结束点；本例每段请求读取或 worker 页使用一个新的 Session，并在此后才交付响应或进入下一页。`Session.close()` 会结束未完成的事务并归还连接；关闭 Session 不等于关闭数据库服务器。

仓库中的 [ASP.NET Core 与 EF Core 示例](../../archive/back-end/ASP.NET-Core.md) 用 `DbContext` 展示相近的对象跟踪与请求作用域。换 ORM 后，仍要分别找出对象跟踪、事务提交和驱动连接归还的边界；某框架默认的 Web 作用域不是数据库本身的规则。

### 怎样让每个请求有界地访问数据库？

以下同步代码以 SQLAlchemy 2.0 和 PostgreSQL 为例，假设 `Report` 已映射，`account_events` 是数据库中的表，`Engine` 在每个服务进程内创建一次。HTTP 路由先按当前主体校验 `report:read`，再把可信账户范围放进查询条件。worker 则从权威数据库读取已接受 job 的账户、时间范围和固定页数预算，并按 job 规定复查 `report:export` 权限；不能把队列正文里的账户范围当作授权凭据。

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
    with Session(engine) as session, session.begin():
        report = session.scalar(
            select(Report).where(
                Report.account_id == account_id,
                Report.id == report_id,
            )
        )
        if report is None:
            return None
        # 在事务提交前复制出响应字段，避免返回依赖懒加载的 ORM 对象。
        return {
            "id": report.id,
            "status": report.status,
            "version": report.version,
        }

def load_account_page(account_id, start_at, end_at, after=None, limit=100):
    # 参数来自已授权并持久化的 job；本例使用 Q2 的左闭右开时间范围。
    cursor_filter = ""
    params = {
        "account_id": account_id,
        "start_at": start_at,
        "end_at": end_at,
        "limit": limit,
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

第一条路径先验证主体，再同时按可信 `account_id` 和 `report_id` 取资源；只用报表 ID 会漏掉账户边界。事务上下文在正常返回时提交、异常时回滚，外层 Session 上下文随后关闭。SQLAlchemy 默认在提交时令已加载的 ORM 属性过期；提交后在 Session 仍打开时读取 `report.status`，可能重新发起数据库访问；提交并关闭后再访问，则可能因对象已脱离 Session 而触发 `DetachedInstanceError`。所以响应字段须在事务提交前复制出来。读取通常不需要为“成功”额外写入；这里显式结束事务，是为了把连接归还点放在返回给客户端之前。

第二条路径按 Q2 的 `[2026-04-01T00:00:00Z, 2026-07-01T00:00:00Z)` 取一页。排序键 `(occurred_at, event_id)` 由时间戳和唯一事件 ID 组成；本例要求这两列非空，事件写入后不再修改这两个值。若多行同一时间，ID 再给出稳定次序。SQL 返回列顺序是 `event_id, occurred_at`，构造游标时需按排序键重排字段，不能直接把整行当作游标。范围、游标与页大小均绑定为参数；动态拼接的片段只有固定 SQL 条件，不含调用者提供的 SQL。

为看清游标，先把合成教学数据的页大小从 worker 固定预算 100 缩小为 2；SQL 与排序不变。若第一页返回 `(100, 10:00)`、`(101, 10:00)`，游标是 `(10:00, 101)`，下一页只返回 `(102, 10:01)`；这一页仅有 1 行，小于页大小 2，于是读取完成。若游标错用 `(10:00, 100)`，下一页会重复返回 `101`，这说明同时间戳时唯一的第二排序键不可省略。

实际 worker 使用从已接受 job 读取的可信账户、Q2 起止时间和页数预算；本例 job 预算为 12 页，服务端硬上限也是 12。它按 `after=None → 每页读取 → 用最后一行排序键推进` 顺序开启新事务，每页开始新的 Session。下面的调用器只展示分页和结束条件；`load_authorized_export_job` 会从数据库取 job 并复查 `report:export` 权限，写 CSV 的细节省略。

~~~python
PAGE_SIZE = 100
MAX_PAGE_BUDGET = 12

def iter_job_pages(job_id):
    job = load_authorized_export_job(job_id)
    if not 1 <= job.max_pages <= MAX_PAGE_BUDGET:
        raise InvalidJobBudget(job_id)
    after = None
    for page_number in range(1, job.max_pages + 1):
        rows = load_account_page(
            job.account_id, job.q2_start, job.q2_end,
            after=after, limit=PAGE_SIZE,
        )  # 函数返回时，本页 Session 和事务已经结束
        if len(rows) < PAGE_SIZE:
            yield rows
            return  # 本页不足 100 行：已扫完当前查询视图
        if page_number == job.max_pages:
            raise RangeExceeded(job_id)  # 不把可能不完整的 CSV 标成成功
        yield rows
        last = rows[-1]
        after = (last.occurred_at, last.event_id)
~~~

满 100 行就继续；不足 100 行表示这一查询视图中没有更多行。达到 12 页预算后若第 12 页仍有 100 行，本例按范围超限失败。这个规则也会让**恰好 1,200 行**失败，因为固定预算内无法确认是否还有第 1,201 行；本例宁可保守失败，也不把可能截断的结果标成完整。异常发生时，调用方丢弃尚未发布的部分输出，并把本次尝试记录为范围超限；只有迭代正常完成且报告产物已写好，才标记 job 成功。若要接受恰好 1,200 行并区分超额，应由 job 契约决定是否另行探测下一行。

每页各自使用短事务，因此页与页可能看到不同时间点的数据；一个新事件若在前一页之后插入到已经越过的游标之前，后续页不会回头拾取它。稳定排序键只保证给定视图内游标可前进，不等于固定结果集。若产品要求同一数据库快照，需把 `Session` 和事务一起移到页循环外，并让每页查询复用这个 Session；所有页处于同一笔有界的 PostgreSQL `REPEATABLE READ` 事务中，或读取版本化快照。此时连接从第一次借出后一直占到整段循环的事务结束，包括页间处理时间。连接池约束读取并发，数据库主键、索引和事务语义仍由数据库决定，见[库存约束怎样保护一次预留？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。

使用 ORM 可清楚表达实体关系和变更跟踪；批量操作或数据库特有查询也可以使用参数化 SQL。应检查 ORM 实际发出的 SQL：数据库针对实际语句选择查询计划，唯一约束和隔离语义仍由数据库决定。

### 长时间持有连接怎样变成池耗尽？

典型占用路径是：首次需要连接时向池申请；池里若没有空闲连接但仍低于并发上限，可以按需新建；若池已到上限且没有空位，调用方等待 `pool_timeout`。等待超时发生在借出之前，业务 SQL 尚未发出，也没有借到的连接可归还。成功借出后，查询、写入和事务内等待都占着这个连接，直到提交/回滚并归还。若事务完成前等待远端 HTTP、发送长响应、排队或做无关 CPU 工作，这段等待也占槽。

> [!example] 一槽连接如何让后续请求在 SQL 之前超时
> 合成配置：`pool_size=1`、`max_overflow=0`、`pool_timeout=2` 秒。A 在 `t=0` 借到唯一连接，查完报表后还在事务内等待远端服务 3 秒。B 在 `t=0.1` 到达并请求连接；它的 SQL 只需 10 毫秒，但连接一直被 A 占着，B 约在 `t=2.1` 池等待超时，尚未执行自己的 SQL。A 到 `t=3` 归还连接已经救不了 B。把远端等待移出事务，或在发起远端调用前结束数据库工作，才会提前释放槽位。

要让一次故障能分流，为每次申请记录 request/job attempt ID、进程标识、Engine/pool 标识和申请时刻；成功 checkout/checkin 事件另带连接标识、事件时刻和 checkout 时的持有者 attempt ID。应用计时从调用可能借出连接的操作之前开始。SQLAlchemy 的 `PoolEvents.checkout` 只在连接成功取出后触发，超时者 B 不会有 checkout，不能拿 B 的 attempt ID 直接找 A。先在 B 所在的同一进程、同一 pool 中，找出 **B 等待期间仍处于 checked-out 且尚未 checkin 的连接**，包括 B 开始等待之前就已 checkout 的连接；再按该连接持有者 A 的 request/job attempt ID 查应用 trace。要关联 PostgreSQL activity 时，再记录或匹配 backend PID。物理建连失败、池等待超时和 SQL 执行超时分别计数。`PoolEvents.connect` 标记某条物理连接成功创建，能帮助判断 checkout 是否伴随新建，但单个事件不能量出建连耗时；若需建连用时，在驱动执行物理 connect 调用前后分别计时。

| 观察结果 | 可以得出的判断 | 下一步 |
|---|---|---|
| 申请连接到 timeout 很久，已 checkout 数量达到配置上限，且该尝试没有 SQL 事件 | 请求排在池里，并未发送 SQL | 在同一进程/池中找 B 等待期间仍被占用、尚未 checkin 的连接；包括 B 申请前已 checkout 的连接。再查持有者的 request/job attempt trace，必要时匹配 PostgreSQL backend PID。 |
| checkout 到 checkin 很久；PostgreSQL `pg_stat_activity` 显示 `idle in transaction`、`wait_event_type = 'Client'`，且 `xact_start` 很早 | 应用事务仍开着，但数据库在等客户端继续发命令；可能在事务中等待远端或响应流 | 对照同一 trace 中的远端等待区间，收窄事务并提前归还连接。 |
| SQL 已开始且执行期间 `wait_event_type = 'Lock'` | SQL 正等数据库锁 | 先找阻塞事务和锁资源，不要先扩大应用池。 |
| checkout 等待高，但多数连接 checkout-to-checkin 较短，且并发借出已到配置上限 | 单次占用短但同时到达的请求超过当前池并发 | 限制 API/worker 并发或在数据库总连接预算内调整池，纳入所有副本和其他使用者。 |

查询慢、N+1 查询、锁等待、事务里调用远端服务以及遗漏结束事务，都会改变上述某段时长。池等待之外也要单独记录物理建连失败和 SQL 超时。重试会再增加借出请求；在池已经饱和时，不设截止时间地重试会加重排队，应按请求或 job 的总预算拒绝、延后或失败。应用池超时不等于可以把数据库错误改写成空结果。

连接数也要按进程和部署副本求和。每个服务进程通常拥有自己的 `Engine` 和池；`QueuePool` 按需建连，不会在 Engine 创建时预先打开所有槽位。`pool_size` 是可保留的空闲连接数，`max_overflow` 是超过基数后允许同时借出的额外连接数。它限制借出峰值，不给每条物理连接永久标记“基数”或“overflow”身份：归还时若空闲队列有位，**先归还的那条连接会被保留**，不论它先前是否属于 overflow；队列已满才关闭这次归还的连接。下一次借用的是池当前保留的连接。

假设有 4 个副本、每个副本 3 个服务进程，每进程设置 `pool_size=8` 和 `max_overflow=2`，若所有池同时达到上限，配置的同时借出上限是 `4 × 3 × (8 + 2) = 120`。这是每个进程一池、各池都连接到同一受限数据库时的配置峰值，不是当前已经打开的物理连接数。API、worker、迁移任务和其他服务都要放进同一数据库连接预算，并留出管理和故障恢复余量。不要跨 `fork` 共享父进程已打开的连接；一种做法是在每个子进程内初始化 Engine，另一种是在子进程初始化阶段对继承的 Engine 调用 `engine.dispose(close=False)`，让子进程建立自己的连接池。

**接下来：** 数据访问章节规定回源时何时借用和归还连接；缓存会改变哪些展示读取到达数据库以及返回的版本新旧，见[怎样缓存数据库读取并说明陈旧窗口？](#12.%20%E6%80%8E%E6%A0%B7%E7%BC%93%E5%AD%98%E6%95%B0%E6%8D%AE%E5%BA%93%E8%AF%BB%E5%8F%96%E5%B9%B6%E8%AF%B4%E6%98%8E%E9%99%88%E6%97%A7%E7%AA%97%E5%8F%A3%EF%BC%9F)。若请求超时或需要控制重试总量，见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - SQLAlchemy 2.0 中 Session 的身份映射、工作单元、flush/commit/rollback、close 归还连接，以及 Session/AsyncSession 的并发使用规则：[Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)，对应 `What does the Session do?`、`Flushing`、`Closing`、`Is the Session thread-safe?`，核对于 2026-11-12。`Session` 不做通用查询缓存，见同页 `Is the Session a cache?`。默认提交后过期对象属性与事务边界见 [Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#managing-transactions)；`Session.connection()` 的连接获取时点见 [Session API](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.connection)。
> - `QueuePool` 配置项、按需创建连接、`pool_size + max_overflow` 并发上限以及 fork 时不共享池连接：[SQLAlchemy 2.0, Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)，`Connection Pool Configuration`、`QueuePool` 与 `Using Connection Pools with Multiprocessing or os.fork()`，核对于 2026-11-12。overflow 归还后由空闲队列容量决定保留或关闭，核对 [SQLAlchemy 2.0.44 QueuePool 实现](https://github.com/sqlalchemy/sqlalchemy/blob/rel_2_0_44/lib/sqlalchemy/pool/impl.py#L129-L166)。代码为同步 `create_engine()` 路径；异步 Engine 使用兼容 asyncio 的池实现。
> - 池事件定义：连接成功借出见 [PoolEvents.checkout](https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.PoolEvents.checkout)，归还见 [PoolEvents.checkin](https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.PoolEvents.checkin)，物理连接创建见 [PoolEvents.connect](https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.PoolEvents.connect)；池到达配置上限后的 timeout 见 [SQLAlchemy 2.0 Error Messages](https://docs.sqlalchemy.org/en/20/errors.html#queuepool-limit-of-size-x-overflow-y-reached-connection-timed-out-timeout-z)，两页核对于 2026-11-12。
> - `LIMIT` 查询应有唯一稳定排序：[PostgreSQL 18, LIMIT and OFFSET](https://www.postgresql.org/docs/18/queries-limit.html)，§7.6；`(occurred_at, event_id)` 行值比较按从左到右顺序比较：[PostgreSQL 18, Row Constructor Comparison](https://www.postgresql.org/docs/18/functions-comparisons.html#ROW-WISE-COMPARISON)，§9.25.5；核对于 2026-11-12。
> - PostgreSQL 的 Read Committed 在每条命令开始时取快照，Repeatable Read 在事务内保持同一快照：[PostgreSQL 18, SET TRANSACTION](https://www.postgresql.org/docs/18/sql-set-transaction.html)，`ISOLATION LEVEL`，核对于 2026-11-12。
> - PostgreSQL `pg_stat_activity` 的 `state`、`xact_start`、`wait_event_type` 字段，以及 `idle in transaction`、`Lock` 等等待状态：[PostgreSQL 18, The Cumulative Statistics System](https://www.postgresql.org/docs/18/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW)，§27.2.3，核对于 2026-11-12。
> - 账户范围、job 的时间界限和页数是本例的业务约束。`require_account_permission` 是示意授权边界，不是 SQLAlchemy API。
## 12. 怎样缓存数据库读取并说明陈旧窗口？

**案例：** 报表 42 的已授权展示内容常被重复读取，适合放进 Redis 来减少主数据库查询；数据库仍是版本的权威来源。展示缓存里可能是版本 9，也可能在更新后变为版本 10。相反，后台任务 `job-demo-731` 的 `queued/running/succeeded` 状态和结果引用必须从权威数据库读取，不能用一个可能陈旧的缓存值回答。每次请求都要重新验证当前主体对账户和报表的访问权；缓存键不是授权凭据。

`cache-aside`（旁路缓存）由应用先查缓存，未命中时读取数据库，再把结果写回缓存。它减少重复读取，但带来两个需要由业务承受或显式解决的条件：命中值可能落后于数据库，Redis 故障时的大量未命中也会变成数据库压力。下文设 time to live（TTL，存活时间）为 30 秒；TTL 和报表值都是教学设定，不是线上推荐或测量结果。

### 一次读取和写入会经过哪些状态？

读取路径从授权开始：验证当前主体能否读取 `acct-17` 的报表 42，再取出获准的账户范围。这个案例缓存按语言生成、可由多个获准主体共享的报表表示，键为 `report:v1:acct-17:42:zh-CN`；权限筛选仍发生在每次请求中，缓存值不含主体专属字段。若命中后有字段需要按当前权限隐藏，命中路径和数据库回源路径都在返回前应用同一权限投影。若产品缓存的是已经按主体过滤的最终响应，键必须包含主体和权限版本等所有影响表示的范围，权限变化时也要让旧表示失效。缓存键不能代替当前访问检查。参见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

- **命中：** Redis `GET` 取回共享报表表示，应用再按本次通过的权限检查生成响应；本次不读报表数据库。
- **未命中：** 应用按可信账户范围从数据库读取报表 42。若读到版本 9，缓存共享表示 `'{"version":9,"status":"ready"}'`，通过 `SET report:v1:acct-17:42:zh-CN ... EX 30` 设置 30 秒期限，再按当前权限生成响应。数据库错误、缓存错误不能被伪装成 `not-found`；缓存写入失败也不应丢弃已经读到的数据库结果。
- **确定不存在：** 只有数据库明确确认不存在时，才可短时缓存 `not-found`。创建资源时删除所有受支持语言的负缓存键；创建前已开始的未命中读取仍可能迟到回填负结果，也受后文 D+T 条件约束。
- **写入：** 在数据库事务中把报表从版本 9 更新到版本 10 并提交，再让失效流程删除该账户/报表的所有受影响表示键，而不是只删当前请求的 `zh-CN` 键。若语言集合有界，可以逐一生成键；transactional outbox（事务型发件箱）可把报表 ID 和变更类型连同事务提交，再由中继删除所有语言表示和负缓存。存在主体专属表示时还须覆盖其权限版本。先删后提交会让并发读者在数据库仍为 9 时回填版本 9；先提交再删避免这一顺序，但不能阻止已在途的旧读取稍后回填。

`GET`、`SET ... EX`、`DEL` 和 `TTL` 是这条路径所需的基本 Redis 命令。`TTL` 只报告键剩余寿命，不会告诉应用数据距数据库提交已经多旧。数据库提交和 Redis 删除属于两个系统，不能由一个普通数据库事务原子完成：如果提交后进程崩溃或 `DEL` 失败，原有缓存可能继续存在到过期。这个发件箱模式可在数据库提交时一同记录失效意图，再由 relay（中继器）重试 `DEL`；它使失效最终可重试，但在 relay 成功前仍允许旧值，且不能阻止失效后仍在途的旧读取再次回填。高成本报表后台任务的耐久状态和结果引用仍直接查询数据库，见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 为什么存活时间不等于一致性保证？

`SET` 默认会替换这个键原有的 TTL；Redis 6.0 起可用 `KEEPTTL` 保留旧过期时间。本例的回填使用 `EX 30` 设置新的存活时间，计时从这次 `SET` 开始，而不是从数据库提交开始。因此 TTL 限制的是当前缓存条目从这次写入起保留多久，不能单独证明缓存值距数据库最新提交不超过 30 秒。

图中时间是相对秒数，事件间距不按比例绘制。`t=0`，读者 R 缓存未命中，从数据库读到版本 9，但尚未完成回填。`t=1`，写者 W 提交版本 10，再删除缓存键；键此时为空，却无法收回 R 已经读在内存中的版本 9。`t=3`，R 将旧版本 9 写入空键并设置 `EX 30`。若没有其他回填，Redis 键在 `t=3` 起可命中版本 9，约在 `t=33` 到期，过期后不再命中；相对 `t=1` 的数据库提交，陈旧命中可持续到近 32 秒。`32 = (3 + 30) - 1` 是指定时间和参数的手算结果，不是 Redis 运行测量。

![报表 42 的在途读取在写入失效后回填旧版本并重启 TTL 的时间线](../../engineering-foundations/backend/resources/caching-and-redis-stale-refill-timeline.svg)

要把这条时序推广成上界，需同时给出两个上限。令 **D** 为提交后仍允许旧表示被 Redis 成功写入的最长时间；D 必须覆盖所有可能读到旧值的来源（例如旧事务快照或滞后副本）、应用排队与重试，以及 Redis 接受回填前的延迟。只设置请求截止时间不够：截止时间之后仍能到达 Redis 的旧写入必须被丢弃或由栅栏拒绝。令 **T** 为所有可能含旧值的表示键的期限上限：每次成功写入都必须设置不超过 T 的 TTL，提交时已经存在的旧条目剩余 TTL 也必须不超过 T。命中不能续期或滑动延长 TTL，也不能用 `KEEPTTL` 保留一个超过 T 的旧期限。于是任何提交后的旧回填都不晚于提交后 D 写入，任何提交时已有的旧条目也至多再存活 T；在同一正常推进的计时基准上，按过期检查的时间粒度衡量，最后一次旧值命中不晚于 `D + T`。这不是不计时钟误差和执行延迟的墙钟承诺。若不能为 D 证明有限上限，TTL 本身不提供有限的全程陈旧上界。本例只有一个语言表示，D = 2 秒（提交 t=1 到成功回填 t=3），T = 30 秒，所以陈旧命中可逼近提交后 32 秒。多种表示时，D 与 T 要覆盖所有变体及其回填路径。

版本号比较也不能单独保证严格新鲜。报表已提交 v10、但失效尚未执行时，缓存中仍有 v9，版本比较并不妨碍读者直接命中 v9；DEL 后键为空，没有 v10 可供比较；若版本标记也放在可淘汰缓存中，它可能一起消失。只阻止低版本覆盖，只证明缓存内部不会被某次旧写降级，不证明缓存代表数据库当前版本。读己之写可携带刚提交的最低版本，并绕过缓存或只接受不低于该版本的值。要求每个请求都读到权威当前版本时，应在可见该提交的新鲜权威读路径查询，或在读取时取得与数据库提交一致的最新版本门槛，只接受不低于该门槛的缓存值。这种持久失效栅栏须覆盖空键、淘汰和所有表示变体。门槛只是持久化但异步更新，仍会留下提交到门槛更新之间的旧命中窗口；本章不声称单靠 Redis TTL/版本比较实现了这类协议。不能接受陈旧状态的后台任务、授权决定和余额仍应读权威源。

失效与监控也要区分不同时间。缓存写入时刻只能量出条目驻留时长，不能代表报表数据距数据库提交多久。可在样本中比较缓存表示的版本或 `updated_at` 与权威数据库当前值，并记录发现差异及其持续时间；若只记录 fill time，不应把它标成数据年龄或陈旧窗口。

对允许短暂陈旧的展示页，可使用可靠的写后失效和有界 TTL，并监控所有表示变体的失效结果。若 `DEL` 失败，原有键可继续到成功删除、淘汰或到期；若旧读取在删除后回填，仍须由 D 的约束和 TTL 覆盖。把更短 TTL 当作唯一补救不会修复回填顺序。

### 缓存击穿和 Redis 故障怎样限制？

一个热门键过期时，100 个并发请求可能同时 `GET` 未命中并各自读数据库，把一次正常读取放大成 100 次。TTL 加少量随机抖动能把许多不同键的到期时间错开；它不会拆散同一个热门键在同一刻过期的请求。

同一进程内的同键请求可用 single-flight（单飞请求合并），让一个调用者负责加载，其他调用者短暂等待；它不协调其他进程。跨进程可用有界 lease（租约）尽力合并：第一次 `GET` 未命中后，调用者用 `SET lock-key unique-token NX PX lease-ms` 领锁。`unique-token` 每次领取都新生成；`NX` 只在锁键不存在时写入，`PX` 后的期限单位是毫秒。成功领锁后必须再 `GET` 一次缓存：第一次未命中后，另一位持有者可能已回填并释放锁；若复查命中，就用当前权限生成响应并安全释放自己的锁，不再读数据库；只有复查仍未命中才回源并回填。未领到锁的调用者在请求截止时间内重查缓存，拿不到值就按回源预算等待、失败或回退。释放必须原子地比较 token 并只删除匹配锁：Redis 8.4 起可用 `DELEX lock-key IFEQ unique-token`；较早版本可用 Lua 脚本完成同一比较与删除。不能先 `GET` 比对、再单独 `DEL`，否则租约到期后旧持有者可能删掉新锁。若旧加载超过租约，第二个加载者仍可能开始，因此锁只减少重复工作，不是数据正确性的证明。

Redis 内存策略也会影响命中：达到内存上限时，所选 eviction（淘汰）策略可能在 TTL 到期前移除缓存键，这只会变成未命中，应按普通缓存未命中回源。若配置 `noeviction`，新缓存写入可能报错；主数据库已经读出的结果仍可返回，同时记录缓存写入失败。观测命中/未命中、Redis 命令失败、淘汰计数、回源量及连接池等待时间，才能分辨缓存缺失和数据库变慢。

Redis 不可达时，`GET` 报错不是普通缓存未命中。应用可以在请求截止时间、回源并发上限和数据库连接预算内读取主库；超出预算就返回暂时不可用。只有确实另存本地快照、端点允许陈旧响应且能核对快照年龄时，才考虑在 Redis 故障下返回该快照。不要把 Redis 错误或数据库错误吞成空值。缓存故障带来的回源峰值由[怎样限定 ORM Session 并排查连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)一同计入；该页展示回源 SQL 怎样申请并占用连接。

**接下来：** 高成本报表的持久后台任务状态、授权和结果引用见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。本章只缓存可容忍陈旧的展示读取；如何保证一次写入和数据库事务的原子性，见[库存约束怎样保护一次预留？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。

> [!info]- 来源
> - Cache-aside 的 miss 回源、读取后回填、写后失效、TTL 与热门键并发回源：[Redis, Cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/)，`Why the problem is hard` 与 `How Redis supports the solution`，核对于 2026-11-12。官方流程给出通用模式；本文的在途旧值竞态及 D+T 算例是按明确事件顺序推导的应用条件，不是官方承诺。
> - `SET key value EX seconds` 以秒设期，`PX` 以毫秒设期；成功的 `SET` 默认丢弃旧 TTL，除非显式用 `KEEPTTL`（Redis 6.0 起提供）；`NX` 仅在键不存在时写入：[Redis, SET](https://redis.io/docs/latest/commands/set/)，`EX`、`PX`、`NX` 和 `KEEPTTL`，核对于 2026-11-12。移除键及返回剩余 TTL 分别见 [DEL](https://redis.io/docs/latest/commands/del/) 和 [TTL](https://redis.io/docs/latest/commands/ttl/)；剩余寿命不是数据距权威提交的年龄。
> - 内存上限和淘汰策略、`noeviction` 下的写入拒绝、可按 `INFO` 查看淘汰和命令拒绝：[Redis, Key eviction](https://redis.io/docs/latest/develop/reference/eviction/)，`Using maxmemory`、`Eviction policies` 与 `Using the INFO command`，核对于 2026-11-12。
> - 单实例 `SET ... NX PX` 锁、随机且唯一的 token、期限单位和比较 token 后安全释放：[Redis, Distributed Locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)，`Correct Implementation with a Single Instance`，并参照 [SET](https://redis.io/docs/latest/commands/set/)，核对于 2026-11-12。官方页说明 Redis 8.4 新增 `DELEX ... IFEQ`，更早版本可用 Lua 脚本原子比较并删除。本文增加“领锁后复查缓存”以避免前一持有者已经回填后的重复回源；这是应用流程，不是锁命令语义。单实例短租约只用于尽力合并缓存加载，不用于数据库正确性。
> - 旧事务快照在 PostgreSQL 18 Repeatable Read 下可继续看见事务开始前的版本：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2，尤其 Repeatable Read 的事务快照说明，核对于 2026-11-12。复制数据未同步时，回源也可能填入旧值：[Microsoft, Caching Guidance](https://learn.microsoft.com/en-us/azure/architecture/best-practices/caching#caching-and-eventual-consistency)，`Caching and eventual consistency`，核对于 2026-11-12。两者说明 D 要覆盖数据来源的陈旧期；具体 D 仍由部署的事务、复制和队列边界决定。
> - 过期边界与计时：[Redis 8.4.0 `keyIsExpired`](https://github.com/redis/redis/blob/8.4.0/src/db.c#L2475-L2483) 使用命令时间快照，并在 `now > when` 时判定过期；因此到期毫秒的等号处仍可能读到值，本文时序用“约 t=33 到期”，不写成严格半开区间。D+T 推导以同一正常推进的计时基准和普通过期读取为条件。
> - 在途旧填充可覆盖新缓存；仅靠缓存内版本记录还会在新版本键被淘汰后丢失较新版本知识：[Meta, Cache made consistent](https://engineering.fb.com/2022/06/08/core-infra/cache-made-consistent/)，开头的失效竞态和 version field 反例，2022-06-08。该案例支持“版本比较不等于最新读取”的边界，不提供本例的强一致协议。
> - `maxmemory` 淘汰策略及写入拒绝：[Redis, Key eviction](https://redis.io/docs/latest/develop/reference/eviction/)，`Using maxmemory`、`Eviction policies` 与 `Using the INFO command`，核对于 2026-11-12。缓存失效通知与数据库更新的双写缺口、outbox 把两者写入同一事务并处理重复通知：[AWS, Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)，`Intent`、`Motivation` 与 `Issues and considerations`，核对于 2026-11-12。outbox 使失效意图可重试，仍不阻止失效后的在途旧读晚到回填。
> - 报表缓存键、逐次主体授权、表示维度齐全的缓存键、负缓存策略、读己之写和 job 状态必须查权威数据库是本章应用边界，见内部安全与报表设计链接；不是 Redis 命令承诺。没有连接 Redis 服务执行命令或故障测试。
## 13. 单库接近容量上限时，怎样分片并在搬迁中保持唯一写入者？

**案例：** 一个合成报表服务按账户保存报表、作业状态和幂等结果。报表 `report-42` 属于 `acct-17`。单库的安全容量或维护窗口不再满足需求，团队准备把账户分到多个数据库；搬迁期间，任何时刻都不能让旧库 B 与新库 D 同时接受 `acct-17` 的业务写入。

本章沿一次完整决策展开：先把必须一起提交的数据放在同一逻辑分片，按访问负载判断瓶颈是一组键还是单个热键，再把 `acct-17` 从 B 搬到 D。迁移以一致快照起点 S 回填，以捕获并有序应用 S 之后的变更追平；旧写入口在一条共享所有权记录上冻结，目标校验到屏障位置 L 后，路由目录以条件更新切换代次，再开放 D。路由缓存只是位置提示，授权、唯一写入者和数据完整性各自仍有明确责任。

下图只约定一个已知账户键的写请求如何进入分片。若请求只带 `report-42`，服务先解析它属于哪个账户；这一步不向全部分片广播。解析路由也不能代替逐次授权。

![报表写请求由账户键定位，并由分片内所有权状态决定接受、刷新或重试](../../engineering-foundations/databases/resources/i7-sharding-request-route.svg)

### 先决定哪些操作必须待在同一个分片

shard key（分片键）要同时适配主要查询和事务边界。本例选择 `account_id`：按账户列出报表、查询幂等结果、改变作业状态时都能用它直接定位；`report-42`、相关作业和账户范围内的操作记录因此位于同一个分片。账户内的一组更新仍可由一笔本地数据库事务提交。

这个选择也限定唯一性的范围。如果作业编号只要求在账户内唯一，应让唯一约束包含账户键，例如 `UNIQUE (account_id, job_id)`；若编号要求跨所有账户全局唯一，则需要可验证的全局命名空间、独立分配器或调用方提供的全局唯一键。每个数据库各有一条 `UNIQUE (job_id)` 只能保证**单库内**唯一，不能把不同分片上的冲突裁决掉。

`logical shard（逻辑分片）`是按分片键划出的数据范围及其当前写所有者；`physical node（物理节点）`是实际承载数据库实例的机器或服务端点。一个物理节点可以承载多个逻辑分片；逻辑分片也可以由一个主实例及多个副本组成。重映射逻辑分片与更换主实例是不同操作，后者本身并不改变哪个账户归哪个逻辑分片。

分片与 `replication（复制）`也解决不同问题：分片把不同键的主数据分开，扩展可承载的数据量和不同键的写入总量；复制让同一数据有冗余副本，可用于故障切换或读取扩展。采用单写者的复制拓扑时，增加只读副本不会把同一热账户的写入摊到更多主实例。多主或共识型系统可以采用不同的写入与冲突协议，不能据此省略本章例子所需的所有权契约。

请求若只携带 `report_id`，服务必须先由资源目录找出所属账户，或让稳定 ID 中带有可验证的路由信息。任意跨账户搜索会成为 `scatter-gather（散播后汇总）`：请求扇出到多个分片，再合并结果，尾延迟和失败面都会随参与分片增加。跨分片写入也不能假定单个 SQL `COMMIT` 能原子覆盖多个独立数据库；要么选用有明确故障恢复语义的协调事务，要么重构业务边界并接受可恢复的分步流程。事务、隔离和协调提交的边界见[事务隔离与 WAL 能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

路由只确定数据位置，不代表用户拥有该数据。服务仍须从认证主体和资源关系验证其对 `acct-17/report-42` 的权限；路由目录不可作为授权名单，也不可因缓存命中而跳过授权。

### 固定取模为何在加节点时大幅搬家？

先用可手算的合成映射比较扩容成本。假设 `h(acct-n) = n`，分片从 0 编号；这是为了算术透明而选的输入，不是生产哈希函数。三个分片时余数 `0/1/2` 分别映射到 A/B/C；新增 D 后，分片数变四，余数 `0/1/2/3` 映射到 A/B/C/D。

| 账户 | `h(key)` | `% 3` 目标 | `% 4` 目标 |
| --- | ---: | --- | --- |
| `acct-17` | 17 | `17 % 3 = 2 → C` | `17 % 4 = 1 → B` |
| `acct-20` | 20 | `20 % 3 = 2 → C` | `20 % 4 = 0 → A` |
| `acct-21` | 21 | `21 % 3 = 0 → A` | `21 % 4 = 1 → B` |
| `acct-35` | 35 | `35 % 3 = 2 → C` | `35 % 4 = 3 → D` |
| `acct-49` | 49 | `49 % 3 = 1 → B` | `49 % 4 = 1 → B` |
| `acct-52` | 52 | `52 % 3 = 1 → B` | `52 % 4 = 0 → A` |
| `acct-65` | 65 | `65 % 3 = 2 → C` | `65 % 4 = 1 → B` |
| `acct-70` | 70 | `70 % 3 = 1 → B` | `70 % 4 = 2 → C` |
| `acct-82` | 82 | `82 % 3 = 1 → B` | `82 % 4 = 2 → C` |

这九个键中有八个改变目标；`acct-49` 的余数保持为 1，所以仍到 B。固定取模的好处是映射容易计算，适合分片数长期稳定或可以整体重建数据的系统；代价是分片数变化时大批键可能重新映射。实际要迁移多少数据还取决于真实键的分布，不能只看键的数量。

`consistent hashing（一致性哈希）`把节点与键映射到循环哈希空间，键归给顺时针遇到的第一个节点。下面继续用 0–99 的玩具环，token 位置和键的哈希值都是教学输入。约定区间为 `(前一 token, 当前 token]`，所以新节点 D=20 会接管 `(0,20]`：

| 账户哈希点 | 原环 `A=0, B=33, C=66` | 加入 `D=20` 后 |
| ---: | --- | --- |
| 17 | B | D |
| 20 | B | D |
| 21 | B | B |
| 35 | C | C |
| 49 | C | C |
| 52 | C | C |
| 65 | C | C |
| 70 | A | A |
| 82 | A | A |

因此 `acct-17` 从 B 移到 D，九个样例中只有它与 `acct-20` 搬家；同一小样本里，固定取模搬 8/9，一致性哈希搬 2/9。这个比例只说明映射规则的差异，不是负载均衡实测。节点只有少数 token 时，各区间仍可能很不均匀；`virtual node（虚拟节点）`让一个物理节点在环上有多个 token，通常能缩小区间大小偏差，但不能保证真实数据和请求负载均匀。环给出候选位置，不会自动切换账户的权威目录；本章继续追踪 `acct-17`，只有回填、追平、校验和单写切换完成后才逐账户改路由。

哈希分片适合按离散键点查和均匀分摊许多键，但打散按键范围的局部性。`range partitioning（范围分区）`保留范围扫描、局部排序或按范围归档的便利，却可能让新时间戳或递增编号集中写到当前边界分区。迁移选择不能只问哪种函数“更均匀”：先看请求是否都带分片键、账户事务范围、排序/范围扫描需求和实际热点分布，再选能保留主要访问路径的映射。

### 怎样判断要重平衡还是拆开热键？

扩容前先区分三种量：所有分片的总数据、每个分片当前负载、每个分片里最重的单个键。平均负载会掩盖偏斜，数据行数也不等于资源消耗；报表生成写入、状态轮询和索引维护的代价可能不同。以下只用写工作量做一笔可复算的合成算例，假设每个请求消耗相同；这里 `1 work` 是一个等成本的标准化写请求，不是产品或硬件单位。物理节点经压测后暂以 `1,200 work/s` 作为安全目标。这不是数据库产品的固定容量，也不是测量结果。

| 物理节点 | 当前写工作量 | 其中 `acct-17` | 移出 `acct-17` 并加 D 后 |
| --- | ---: | ---: | ---: |
| A | 700 work/s | — | 700 work/s |
| B | 1,600 work/s | 1,000 work/s | 600 work/s |
| C | 700 work/s | — | 700 work/s |
| D（新） | — | — | 1,000 work/s |
| 合计 | 3,000 work/s | — | 3,000 work/s |

把 `acct-17` 从 B 搬走后，总工作量仍是 3,000 work/s；峰值从 1,600 降为 1,000，四台节点都低于本例假设的 1,200 安全目标。扩容在这里解决的是账户键分布偏斜，并没有减少请求成本或系统总工作量。若新 D 的目标也只有 900 work/s，整账户搬迁仍然不满足目标，必须换目标容量或进一步改变账户边界。

| 观测到的形态 | 更可能的瓶颈 | 下一步判断 |
| --- | --- | --- |
| 多个分片都接近 CPU、I/O、连接或存储安全上限 | 总容量或单请求成本 | 先降低请求/索引成本；再增加可用节点或分片，并按主要资源复核容量。复制只读副本只帮助符合读取契约的流量。 |
| 只有一两个分片超限，且过热分散在很多键 | 分配不均或当前分区边界不合适 | 移动部分逻辑分片/范围，或调整映射；搬迁前核对新节点在同一资源口径下有足够余量。 |
| 一个账户、一个设备或一个时间键独占大部分工作量 | 单热键；虚拟节点或加节点仍把整个键送往一个所有者 | 先决定能否在实体内部再按报表/事件键切分；若不能，就限速、缓存、排队或给该键独立容量，并接受跨子键事务和聚合的额外成本。 |
| 存储占满但请求量不高，体积集中于少数账户/范围 | 数据放置或保留策略 | 以字节数、索引体积、增长率估算搬迁与目标余量；必要时归档或调整分区，不用 QPS 代替容量依据。 |

生产判断要按时间窗记录每个物理节点与逻辑分片的 CPU、I/O、连接数、事务延迟、读写量和数据体积，并观察 p95/p99 与限流/锁等待；再用目标工作负载和安全余量压测，而不是把某次峰值直接设为容量常数。若单个账户超过单节点目标，给它一个独立分片只能隔离邻居，仍不能拆掉“一个账户只有一个写所有者”的上限。要拆账户内键，就要重新决定账户汇总、幂等唯一性、外键与跨键事务由谁协调。

### 复制数据时怎样保持一个写所有者？

迁移协议需要把**数据副本什么时候完整**与**谁获准写入**分开管理。目录对 `acct-17` 记录权威 `owner（写所有者）`、单调递增的 `epoch（路由代次）` 和切换状态；每个分片还有可事务锁定的本地所有权记录。请求携带目标分片与代次，旧缓存不能自行授权。每次业务写都在目标分片的同一数据库事务内锁定并核对本地所有权记录，再写报表、作业或幂等数据；检查和业务效果分成两个事务会留出冻结与写入竞态。

本章把本地所有权行约定为 `(account_id, owner, epoch, candidate_id, state)`。`open` 可接受业务写，`closed` 是已准备但尚未开放的候选，`frozen` 是本代的终态。曾经创建过的行或等价代次下限不能删除；任何可被提升为写主的副本都必须保留它，或在提升后、对外开放前重新从权威端核对，否则旧副本可能复活旧代次。

| 本地状态转换 | 必须满足的条件 |
| --- | --- |
| 首次初始化 → `open` | 仅该账户在此分片从未有过所有权行，且权威目录已唯一指定初始 owner 时，才建立初始所有者；本地第一行本身不给写权，后续迁移不能伪装成首次初始化。 |
| 较低代次 `frozen` → 更高代次 `closed` | 新代次高于持久下限；真正第一次建行则须由当前权威代次授权。完全相同的 prepare 重试只可读回仍为 `closed` 的同一候选。 |
| `closed` → `open` | 仅在目录 CAS 已成功并持久记录确切 `decision_id` 后；命令须匹配账户、owner、epoch、不可变 `candidate_id` 和该决策。只看到 owner/epoch 相等不构成授权。 |
| `closed` 或 `open` → `frozen` | 同一行上的条件更新。若原为 `open`，它会等已持业务共享锁的事务提交或回滚后再冻结。 |

同代次 `frozen` 不能改回 `closed` 或 `open`。未发布的 `closed` 候选也不能被新 prepare 随意覆盖：先从权威目录确认它已在 CAS 竞争中不可逆地落败，再将该行冻结，随后才可准备更高代次。目录离开任何已发布的 owner/epoch 前，必须先让该 owner 本地冻结且冻结持久。这样，迟到开门与取消开门的冻结会在同一行竞争：冻结先赢，旧开门条件失败；开门先赢，冻结等待业务事务排空后成为该代终态。

#### 快照 S、持续变更与目标回填

先建立一个在逻辑上无缝相接的复制起点。`consistent snapshot（一致快照）`在坐标 S 表示：它包含源端截至 S 的一致业务数据版本；从同一 S 开始保留所有之后提交的源端变更流。目标 D 是候选副本，在验收完成前不接受应用的业务写入。

![快照 S 提供回填基线，捕获的后续变更在基线完成后按顺序重放到候选 D](../../engineering-foundations/databases/resources/i7-snapshot-cdc.svg)

实施时要满足三件事：

1. **没有复制缺口。** 先确定快照 S 与 `change data capture（变更数据捕获，CDC）`起点属于同一复制契约，再开始回填。若源端在快照期间继续服务，S 之后的变更必须被可靠保留到目标追上；复制槽、日志保留空间或 CDC 缓冲一旦丢失了必要区间，就不能把“后来重新连上”当作无缺口，要重建快照或重新建立起点。还要监控消费者积压与源端可保留空间；复制槽会阻止尚需的日志被清理，长时间不推进会占用磁盘。
2. **不让旧快照覆盖较新变更。** 本例先完成 `acct-17` 在快照 S 中的基线回填，再从 S 按源端事务顺序应用捕获变更。若为了缩短追赶而并行回填和重放，必须以行版本/日志位置等机制证明旧快照行不会晚于新变更写入目标；仅仅让两个任务同时跑不构成顺序保证。
3. **复制完整业务效果。** CDC 要包含对该账户的插入、更新和删除，保留稳定主键与事务顺序；变更记录必须带足以定位账户的键列。以 PostgreSQL 18 为例，`logical decoding（逻辑解码）`的 UPDATE/DELETE 能否提供旧行列取决于表的 `replica identity（复制标识）`设置。重复投递要按源位置或等效变更标识安全去重。迁移控制用的 owner/epoch 行不当成普通业务表复制到目标；D 的候选所有权状态由切换控制单独准备。

目标追平位置可能包括整个数据库里别的账户的日志事件，但本次迁移只应用 `acct-17` 的业务数据。应用程序的事务也必须以账户边界为单位；如果一笔源事务原子地改变多个账户，本协议把它拆开后就不再保持那笔跨账户事务的原子性。此时要重新设计事务边界或使用能保留该原子性的分布式协调方案。

PostgreSQL 18 的逻辑解码提供一种具体参照：复制槽可导出与变更流衔接的一致快照；`log sequence number（日志序列号，LSN）`描述 `write-ahead log（预写日志，WAL）`位置。槽会保留后续所需日志，消费者也必须防止崩溃重启导致的重复变更造成副作用。它说明怎样实现快照与日志衔接，不意味着本章的账户目录、租户过滤和代次栅栏是 PostgreSQL 自动提供的迁移功能。

#### 用同一所有权锁排空并冻结源端

在 epoch 7 稳定期，B 是 `acct-17` 唯一开放的写所有者。每笔业务事务先在本地 `account_ownership` 行上取得一个**与其他业务写兼容、但与冻结更新冲突**的锁，检查 `owner=B AND epoch=7 AND state='open'`，再在**同一事务**更改业务数据。PostgreSQL 18 可用 `SELECT ... FOR SHARE` 表示这一关系，冻结事务对该行的 `UPDATE` 会等待已持锁的业务事务结束；在 `Read Committed（读已提交）`下，等待并发更新后锁定语句会返回更新后的行版本，因此应用必须在拿到锁后检查状态。不同数据库要核对各自的锁模式。若每笔业务写都对所有者行取互斥锁，账户内写会被串行化；本例不要求这种吞吐成本。

以 PostgreSQL 18 为例，下面是事务内的应用伪码，不是可直接执行的 SQL 脚本。查询和更新必须用同一连接与事务；应用必须真的检查结果，SQL 注释本身不会阻止后续语句：

```text
BEGIN ISOLATION LEVEL READ COMMITTED
row = SELECT owner_shard, epoch, state
      FROM account_ownership
      WHERE account_id = $1
      FOR SHARE
if row_count != 1 or row != (B, 7, open):
    ROLLBACK
    reject or refresh the authoritative route
else:
    UPDATE reports
       SET status = $2
     WHERE account_id = $1 AND report_id = $3
    if this transaction creates a new business effect:
        INSERT local_business_commits(account_id, owner, epoch, operation_key)
        VALUES ($1, 'B', 7, $4)
    COMMIT
```

`local_business_commits` 是本教学协议的本地提交账本：对每个新业务效果，在包含该效果的同一事务写入 `(account_id, local owner, epoch, operation_key)`。重复请求若只读到既有幂等结果，不算新的本地业务提交；B 的账本不随 `acct-17` 的业务快照复制到 D。D/8 的账本只记录 D/8 本地产生的效果，须在回退判断期内保留，并在 D 的权威写主完成故障恢复后可查。若无法确认写主保留全部可能已提交的业务效果（包括数据库已提交、客户端却未收到回执的事务），结果就是未知，不按零提交回退。

冻结事务更新同一行。它会等已有兼容锁释放；应用必须确认条件更新恰好命中一行，才把 B/7 记作 frozen。下面仍是应用步骤伪码；`UPDATE ... RETURNING` 结果要由调用方检查：

```text
BEGIN
changed = UPDATE account_ownership
          SET state = 'frozen'
          WHERE account_id = $1
            AND owner_shard = 'B'
            AND epoch = 7
            AND state = 'open'
          RETURNING account_id
if changed != exactly one account_id:
    ROLLBACK
    reread authoritative state; do not claim B/7 was frozen
else:
    COMMIT
```

同一行上的兼容/冲突锁把“核对所有权”和“写业务数据”连成屏障；仅在应用内先检查再另开事务写数据并不安全。

迁移器先让 B 的入口停止接收**新**业务事务，避免继续扩大队列；但已准入、仍在执行或尚未取得 ownership 行锁的事务不因入口关闭自动消失。冻结更新拿到冲突锁之前，已经持兼容锁的业务事务必须结束；冻结提交之后，排在它后面的请求读取新状态并回滚。不能仅因请求更早到达 API 就算成已获数据库写权。

![写入口停止准入后，源端业务事务与冻结事务在同一 ownership 行上排序](../../engineering-foundations/databases/resources/i7-freeze-barrier.svg)

冻结事务在同一提交中写入一个消费端不会过滤的事务性逻辑消息，例如 PostgreSQL 18 的 `pg_logical_emit_message(true, 'migration_barrier', 'acct-17/B/7')`；使用 `pgoutput` 时还须启用 `messages` 选项。该消息所在源事务的提交位置定义为 L，不能把函数返回的消息记录位置误当成提交位置。由于它与冻结状态同事务提交，日志流中的屏障晚于所有已获准并提交的 B/7 业务写。目标只报告连续应用位置到 L，才说明已越过这个屏障；只读某个服务器当前 LSN 不自动等于 CDC 消费承诺。即使目标过滤掉其他账户的行变更，也要推进它已连续消费的源端位置。单看低复制延迟、估算复制百分比或源端行数都不够。对每个账户，D 从 S 之后的**剩余未应用前缀**继续追到 L，不会把已经应用的增量再盲目全量重放。

这里 `L` 是目标待满足的源端日志位置，不是墙上时钟，也不单独证明目标完整。贯穿本例：快照 S 中 `report-42` 仍为 `queued`；之后请求 `op-9` 在 B/7 的一个业务事务里将它改为 `ready`，并把该操作的幂等结果写入同一账户记录。若这笔事务先取得 ownership 共享锁并提交，冻结更新必须等它结束，屏障 L 就在它之后。D 的消费者要在同一目标事务中应用 `report-42=ready`、复制该幂等结果，并推进本地连续应用检查点；只有目标事务提交后，检查点才代表这些效果持久可见。新的 D/8 开放后，`op-9` 超时重试应读到已复制的幂等结果，不重新生成一份业务效果。若冻结先取得锁，`op-9` 事务看到 frozen 并回滚，源端不产生 ready 更新或幂等结果。

目标已应用连续位置到达 L 之后，还要核对业务不变量：迁移范围的主键覆盖无洞，报表 `report-42` 及其作业和幂等记录在目标可查，账户内唯一约束成立；根据大小与风险核对行数、按稳定主键范围计算的摘要/校验和及关键聚合。只比较总行数可能把“一行缺失、另一行重复”抵消掉。若任何一项不符，B 继续冻结或在安全条件下恢复为唯一写者；不得开放 D 让它边写边追赶。

#### 用条件切换目录，再开放目标

先把候选 `candidate_id=C8` 准备为 `D/8/closed`，使其不接受应用业务写。D 连续应用到 L 并通过初步核对后，关闭 C8 的新回填/CDC 写入口并排空已经开始的复制事务；目标写资格门禁须拒绝任何随后到达或重放的 C8 复制事务。确认 C8 不能再改变候选数据后，重新做最终完整性校验。之后目录用 CAS 比较完整当前值 `B/7`，原子写入 `D/8 + C8 + decision_id=K8`。未命中时不发开门命令，重新读取权威目录；确认候选已不可逆地落败后，才把 D/8 同一行冻结并准备更高代次。CAS 成功或应答丢失后从权威目录确认 K8 已生效，才授权本地更新：`D/8/closed/C8 → D/8/open/C8`，并记录 K8。更新必须匹配同一账户、owner、epoch、candidate 与 K8；看见 `owner=D, epoch=8` 本身不够。旧 B/7 在此前已冻结，所以目录切换后允许短暂没有写者；未得到精确开门决策时保持 closed，不让两个数据库都开放。

![切换目录和目标开门分开提交；安全回退取决于目标是否已有业务提交](../../engineering-foundations/databases/resources/i7-owner-cutover-rollback.svg)

旧路由继续送到 B/7 时，B 本地状态已是冻结，因此拒绝该写。只有请求入口能核对权威目录时，才把 owner/epoch 已改变报告为 `stale-route（路由过期）`并令客户端刷新；若 B 只知道本地冻结而无法查目录，应返回可重试的暂时不可用，客户端再从权威目录取路线。请求目标与 epoch 匹配但本地仍为 closed 时也是暂时暂停，不是 stale-route。超时后的非幂等请求不能仅因刷新了路由就换目标重放，仍需沿用稳定操作键查询或安全重试；每次重试照常校验权限。

目录切换后，按新 owner 查找的读取会去 D；本节的写入栅栏不会拦截还拿着旧缓存 B/7 的读，也不保证它们的新鲜度。副本读的延迟、旧路由读的处理方式以及 read-your-writes（读己之写）承诺，要由独立读取契约说明；一条陈旧读结果不能用来证明旧分片没有提交。

**出现异常时的恢复条件取决于谁已经提交过业务写：**

- 快照、日志捕获或回填在 B/7 冻结前失败：B/7 仍是唯一开放者，可以停止并重建候选 D。只有证明 CDC 区间没有丢失时才能从原位置续跑；否则重新建立一致快照与日志起点。
- B/7 已冻结，但权威目录仍是 `B/7`：D/8 与 B/8 都只能是 `closed` 候选；各自的目录 CAS 都要求当前仍为 B/7。若 `B/7 → B/8` 先成功，只能以该成功决策打开 B/8，D/8 的迟到开门没有成功凭据；若 `B/7 → D/8` 先成功，只能打开 D/8，B/8 不能再赢。输掉的 closed 候选须先从权威目录确认已经不可逆地落败，再在自身分片把同一行冻结，才能准备更高代次。目录切换后，目标开门仍需带与不可变 candidate 完全匹配的成功决策。
- 目录已经是 `D/8`，无论本地 D/8 仍为 `closed` 还是已 `open`，取消或恢复都先在同一行执行 `closed|open → frozen`。若为 open，冻结更新会等已经持业务共享锁的事务完成；若 D/8 的迟到开门先赢，冻结随后排空它。冻结提交后从 D 的权威写主取得新鲜快照，检查本地 epoch-8 提交账本；此账本须由每笔 D/8 新业务效果在同一事务写入、持久保留，并与从 B 复制来的幂等结果区分。账本缺失或无法确认时视作“未知”，不得按零处理。
- 冻结后的 D/8 账本确认为零：B 侧已有候选若仍是 `closed`，先确认其目录 CAS 已落败并冻结；随后在 B 准备 `B/9/closed`，目录 CAS `D/8 → B/9` 成功后，才用该确切决策开放 B/9。D/8 的同代冻结是终态，旧开门不能复活它。冻结后的账本有任一业务提交或结果未知：不能直接回到陈旧 B；保持 D 权威并前向修复，或先把 D 的新提交反向追平到 B、核验后再切。若只是需要在 D 恢复服务，也按更高代次经目录决定后开启 `D/9`，不重新打开冻结的 D/8。

epoch 只递增、不复用，使携带旧代次的调用始终落后于新所有者。此方案选择“基线复制、变更追平、短暂单写屏障、条件切换”，没有让应用同时向 B 与 D 双写；真正的互斥来自所有写入口都遵守分片内的 ownership 检查，而不是路由缓存更新得足够快。

Vitess 24.0 的稳定文档将重分片工作流拆为创建、监控、VDiff 数据核对、`SwitchTraffic` 切流和完成清理；文档也说明可以反向切流。这里引用它作为产品化迁移步骤的实例，不把本章的 B/7、D/8 ownership 行、CAS 条件和零提交回退规则说成 Vitess 提供的同名 API。不同产品可能接管复制、路由、写缓冲或验证的不同部分，采用产品流程时仍应确认其版本和每个步骤实际保证的状态。

若要复习本地事务如何保护唯一约束，可读[两个请求争夺最后一件库存时，怎样保证只预留一次？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)；快照、WAL 与恢复的通用边界见[事务隔离与 WAL 能保证什么？](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源与核实范围
> - 一致性哈希的环分配和虚拟节点用于改善节点间负载偏斜：[DeCandia 等，Dynamo: Amazon’s Highly Available Key-value Store，SOSP 2007](https://cdn.amazon.science/ac/1d/eb50c4064c538c8ac440ce6a1d91/dynamo-amazons-highly-available-key-value-store.pdf)，§4.2，pp. 199–200。本文 0–99 玩具环采用区间 `(前一 token, 当前 token]`，这是本例为了手算明确选择的边界约定；Dynamo 原文以“下一个节点位置大于键位置”定义顺时针归属，正落在 token 的键边界可能不同。九个键点也都是合成输入。
> - 分片行与物理数据库服务器、分片与复制是不同维度：[Vitess 24.0 Sharding](https://vitess.io/docs/24.0/reference/features/sharding/)，核对于 2026-11-13。版本页当日列 v24.0 为 Stable，v25.0 为 Development：[Vitess Releases](https://vitess.io/docs/releases/)。
> - 快照与逻辑复制流的衔接、复制槽在崩溃后可能重发、消费者去重、事务性屏障消息的配置及复制进度：PostgreSQL 18 [Logical Decoding Concepts](https://www.postgresql.org/docs/18/logicaldecoding-explanation.html) §47.2、[System Administration Functions](https://www.postgresql.org/docs/18/functions-admin.html#FUNCTIONS-REPLICATION) §9.28.6 的 `pg_logical_emit_message`、[Logical Streaming Replication Protocol](https://www.postgresql.org/docs/18/protocol-logical-replication.html) §54.5 的 `messages` 选项、[Replication Progress Tracking](https://www.postgresql.org/docs/18/replication-origins.html) §48。UPDATE/DELETE 旧行列的 `replica identity` 限定见 [Logical Decoding](https://www.postgresql.org/docs/18/logicaldecoding.html) §47 开篇；LSN 与 WAL 位置见 [WAL Internals](https://www.postgresql.org/docs/18/wal-internals.html) §28.6。核对于 2026-11-13。18 是当前稳定主版本，2026-11-12 发布 18.7；19 仍为 RC，机制引用固定到 18 文档：[18.7 发布通知](https://www.postgresql.org/about/news/postgresql-187-1712-1616-1520-1425-and-19-rc-2-released-3442/)、[Versioning Policy](https://www.postgresql.org/support/versioning/)。
> - PostgreSQL 行级锁阻塞冲突更新/锁定直到持锁事务结束，以及 Read Committed 锁定更新行后重检条件：[PostgreSQL 18 Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html) §13.3.2、[Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html) §13.2.1。ownership 行与业务修改放同一事务，以及目录 CAS 是本章定义的教学协议，不是 PostgreSQL 自动保证的租户迁移服务。
> - Vitess VReplication 重分片流程、VDiff、切流与反向切流：[Vitess 24.0 Reshard](https://vitess.io/docs/24.0/reference/vreplication/reshard/)，核对于 2026-11-13。迁移状态表和数值工作量示例由本文合成，不是 Vitess 实测或性能承诺。
> - 高访问集中于少数分区键会形成热点、热点容量不能仅由总吞吐推断：[Amazon DynamoDB, Designing partition keys to distribute your workload](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-uniform-load.html)，核对于 2026-11-13。该产品文档仅佐证分区键偏斜的通用现象，不把 DynamoDB 的具体容量限制套用到关系数据库。
## 14. 请求超时后如何确认结果并安全重试？

**案例：** 账户 `acct-17` 的主体 `user-17` 用操作键 `reserve-demo-208` 预留 SKU-7 的最后一件库存。数据库已经提交，HTTP 响应却丢失了。调用方看到超时，不知道请求没到服务器、事务回滚，还是扣减已经完成。要恢复结果，服务需要识别“这是刚才那次预留的重试”，而不是再扣一次库存。

本例沿用[库存事务页](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)的契约：成功提交才绑定操作键；库存失败回滚且不占键；同键同参数重放返回同一笔预留的**当前状态**。下面先跟完一次响应丢失的恢复，再解释如何设计键、控制重试成本和处理取消。

~~~mermaid
sequenceDiagram
    participant C as 客户端
    participant A as API
    participant D as 数据库
    C->>A: POST 预留，键 reserve-demo-208
    A->>D: 扣库存 + 写预留记录
    D-->>A: 同一事务提交
    A--xC: 响应在途中丢失
    Note over C,D: 此时库存为 0；客户端尚不知道已成功
    C->>A: 重放原 POST，沿用键与参数
    A->>D: 授权后按作用域键读记录
    D-->>A: 已存在的预留及其当前状态
    A-->>C: 返回同一笔预留，不再扣库存
~~~

### 超时和截止时间让调用方处于什么状态？

timeout（超时）限定一次等待或操作的时长；deadline（截止时间）是整条调用链最晚允许完成的时间点。每经过一层都重新开始完整 timeout，会让多个串行下游调用的总耗时远超最初预算。服务应传递剩余时间或截止时限，并为清理和响应留出时间。连接建立、TLS 和响应读取是否都包含在一次库的 timeout 内，要按客户端 API 检查。

当写入可能已经执行而响应丢失，调用方得到的是 unknown outcome（未知结果）：它无法从自己的连接状态区分“请求没到”与“效果已提交但响应丢失”。图中 `available` 已从 1 变成 0，预留记录为 `reserved`。客户端没有按键查询的 GET 接口，因此重放原 POST；服务重新授权并核对参数后，找到同一笔记录，不再扣库存。若期间这笔预留已被另一个合法操作取消，就返回当前的 `cancelled`，不会把它重新激活。这恢复的是同一业务操作，不要求逐字节重放首次 HTTP 响应。

查不到记录时，不能立即断言“原请求失败了”：原事务可能仍在执行，尚未提交。重放必须继续经过数据库的原子约束；普通的先查后写无法排除并发。只读状态查询也必须保持只读，不能因为查无记录就偷偷启动原操作。

HTTP 202 Accepted 是另一种显式状态：API 确认任务已受理，但没有表示已完成。账户报表契约没有按幂等键查询的 GET；若 202 响应丢失，客户端用相同 `report-demo-208` 和相同请求正文重放 POST，服务返回已存在的 `job-demo-731` 与状态 URL，再 GET 该已知 URL。连接断开不会自动取消已经持久接受的 job；需要取消时使用明确的取消请求。完整作业生命周期见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 怎样定义可安全重放的幂等键？

idempotency key（幂等键）是客户端为一次逻辑意图生成并在重试时保持不变的标识。服务必须定义它的唯一范围、保留时间、请求参数关系和结果重放规则。账户报表示例把键作用域定义为 (account_id, principal_id, key)；不能让另一个主体靠猜到键读取私有结果。服务还保存规范化请求指纹：同一个键、同一参数返回已存结果；同一键却换了 period 或 format，则返回明确冲突，不能默默把旧结果解释成新意图。

RFC 9110 对 HTTP 方法的幂等性定义为：重复一次或多次相同请求，其预期服务端效果等同于只执行一次；这不禁止每次请求分别记录日志。它是 HTTP 方法的语义。给某个 POST 另加稳定幂等键，则是应用层的去重和结果重放约定，两者不能互相代替。

去重记录和本地数据库效果必须处于同一事务；若扣库存提交后才单独写 reserve-demo-208 操作记录，中间崩溃会让重试无法识别原操作：本例最后一件已被扣完时会误报无库存；若其后补货，重试还可能再次扣减。

在库存例中，复合唯一键是 `(account_id, principal_id, idempotency_key)`。两次尝试都走到插入记录时，只能有一个提交；冲突方须回滚**整笔事务**，撤销自己的临时库存扣减，再用新事务读取已提交记录和比较参数。

库存更新没有返回行时，也要先回滚，再以新事务按操作键查记录。假如 A 刚扣完最后一件并提交，B 重放相同 POST，等到 A 释放行锁后发现库存为零，就会走这条分支：B 查回 A 的同键同参数记录，仍返回同一笔预留；只有回查未见已提交结果时，才报告本次库存失败。查不到不证明另一个原请求已经失败。

这个方案不是在请求一到达时就抢占键。一次真正无库存的失败不保存操作记录，相同 POST 日后可能在补货后成功。同键改参数、更新另一 SKU 的并发请求，也可能在另一请求尚未提交时先得到无库存失败。若产品要求“第一次尝试就固定键与结果，包括失败”，需要另行设计前置占键与处理中状态，不能从这个最小库存事务推导出来。具体时序见[同一请求并发到达时，库存与操作记录怎样保持一致？](#1.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。

服务还要明确保证的重放窗口，并在窗口内保留识别同一键所需的记录。窗口过后若删掉所有信息，服务无法仅凭键字符串判断它是旧操作还是新意图；对于本例这种不带可验证有效期的键，若要在删除结果后仍拒绝过期旧键，就得继续保留可识别该旧键的墓碑记录。窗口外的重试保证必须写清楚，调用方不能把旧操作当成新请求重做。

若操作会调用外部支付或发消息，单库事务无法覆盖远端系统。durable outbox（持久发件箱）只让本地结果与待发布指令一起提交，并使 relay 能在崩溃后重发；它不会替远端付款去重。避免重复付款仍需要收款方按相同业务键幂等处理；如果没有这样的保证，超时后不能盲目重发，应先向权威交易记录查证。对账可以发现重复，但自身不阻止重复扣款。超时也不自动撤销远端副作用。

### 重试时间和总工作量怎样受控？

先判断失败是否可能恢复、操作是否可安全重放，再决定是否重试。参数校验失败和同键异参数冲突应先修正意图；把它们原样反复提交不会恢复。对可恢复失败，使用有上限的 exponential backoff (指数退避) 并加入 full jitter（全抖动），分散再次到达的请求：

~~~text
cap(n) = min(max_delay, base_delay × 2^n)
wait(n) = 从 0 到 cap(n) 均匀随机选择
~~~

假定 base_delay 为 100 ms、max_delay 为 800 ms，第一次失败后的 `n=0`，前几次等待区间依次为 0–100 ms、0–200 ms、0–400 ms；客户端实际次数还须受剩余 deadline 限制。若最多 3 次尝试，初次请求失败后只在剩余预算装得下下一次调用和必要回包时重试。base、上限和次数是服务策略，不是通用常数。若服务要求等待一段时间，例如响应携带 `Retry-After`，也要结合接口契约与剩余预算处理，不能退避后立即绕过该等待。

避免多个调用层各自放大工作量：一条串行调用链上，5 层调用者都最多尝试 3 次，且每次都耗尽后再向上失败，则最深层最多收到 `3⁵ = 243` 次调用。这是最深层的次数，不是整条链所有调用的总和。通常由最了解端到端预算的一层承担重试，其余层明确失败边界。

> [!example] 响应截止时间下的重试复盘
> 客户端总截止时间为 2 秒，第一次（共最多 3 次尝试中的第 1 次）请求用了 1.2 秒后超时，剩余 0.8 秒。第一次失败后的退避是 `n=0`，所以等待上限为 100 毫秒；下一次调用至少需要 700 毫秒，并为处理/返回预留 50 毫秒，能容纳的等待最多只有 `800−700−50=50` 毫秒。若全抖动抽到 80 毫秒（合法，因为低于 100 毫秒），总计要 `80+700+50=830` 毫秒，超过剩余预算，应停止并把状态留作未知。最多 3 次尝试包括初次调用，因此总共最多只有两次退避，后续上限才是 200 毫秒。

![剩余预算为800毫秒，计划等待80毫秒、调用700毫秒、处理返回50毫秒，总计830毫秒，超过截止时间30毫秒](../../engineering-foundations/reliability/resources/api-retry-deadline-budget.svg)

图中的 700 毫秒是这个教学例子选定的最小调用预算；真实请求并没有可预知的固定耗时。应根据服务时延目标、观测数据和取消能力设预算，并把剩余 deadline 传给下游。客户端停止等待后，尚未查证的写入仍然是未知结果，不能自动改成“失败且未生效”。

### 取消如何作为协作式信号？

cancellation（取消）是通知仍在运行的工作“结果不再需要”。把信号传给下游，并在安全检查点停止多余计算、释放资源；不同运行时能否中止远端调用取决于 API。对已返回 202 且已持久接受的账户报表，浏览器断开只结束这次连接，不会取消后台 job；客户端必须向已知 job URL 显式请求取消。尚未接受的请求级工作则可在断开后结束。取消也不证明已经提交的数据库副作用回滚，提交状态仍要从权威业务记录确认。

**接下来：** 账户报表把幂等键、202、outbox 和后台尝试组合成一个可长期查询的流程，见[怎样设计可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。队列发布确认与消费者 acknowledgement 的 broker 语义归[发布者确认和消费者确认分别证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)，连接借用预算归[如何限定 ORM Session 并排查连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。

> [!info]- 来源
> - HTTP 幂等方法、202 受理与 Retry-After 语义：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§9.2.2、§15.3.3、§10.2.3，核对于 2026-11-11；库存键绑定和当前状态重放是本例声明的应用契约。
> - 副作用、超时、重试安全与请求令牌：[AWS Builders’ Library, Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)，核对于 2026-11-11。
> - timeout、backoff 与 jitter：[AWS Builder Center, Timeouts, retries, and backoff with jitter](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter)，原文 2019-12-05，核对于 2026-11-11。
> - Full jitter 的均匀等待区间：[AWS Architecture Blog, Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)，2015-03-04、2023 年补充 SDK 说明；本文只使用其算法定义，不将模拟负载的收益当成通用性能保证。
> - deadline 传播和协作式取消：[gRPC Deadlines](https://grpc.io/docs/guides/deadlines/)，核对于 2026-11-11；具体行为仍取决于各 API。
## 15. 怎样设计一个可持久查询的账户报表？

**案例：** 用户为账户 `acct-17` 请求报表 42：只读有限时间范围内的账户活动，并导出 Comma-Separated Values (CSV，逗号分隔值) 文件。一次查询有时超出 Hypertext Transfer Protocol (HTTP，超文本传输协议) 请求预算；浏览器断线后，用户仍要查询状态，并在成功后七天内下载私有结果。客户端以 `report-demo-208` 作为 idempotency key (幂等键)，服务用 `job-demo-731` 标识已持久接受的 job (任务)；报表 ID、任务 ID 和幂等键不能互相替代。案例假设请求约 8 KiB，最多顺序读取 12 页，结果平均 128 KiB。

平均每秒 5 个新 job、峰值每秒 20 个新 job 且持续十分钟、每个 attempt (尝试) 平均六秒、每个 job 最多三个 attempt (含首次)，都是合成输入，不是测量值。

先决定是否真的需要异步化。若有界读取可以稳定在调用方截止时间和尾延迟目标内完成，同步接口只须校验、读取并返回 CSV，省掉状态、排队和清理生命周期。只有当工作可能超过请求预算、断线后仍须继续，或必须与 application programming interface (API，应用程序接口) 的执行资源隔离时，才创建可恢复的持久 job (任务)。队列保留唤醒，不增加处理能力；可持久的 job 才让用户在连接之外查到服务已接受什么、正在发生什么以及最终结果。

### 如何接受请求并让用户查询结果？

客户端可以发出如下请求：

~~~http
POST /v1/accounts/acct-17/reports
Idempotency-Key: report-demo-208
Content-Type: application/json

{"reportId":42,"period":"2026-Q2","format":"csv"}
~~~

服务先认证当前 principal (调用主体)，再检查它是否能为 `acct-17` 导出报表；然后验证时间范围、格式、页面数等有界条件，并生成会影响执行的规范化参数。请求参数若已可判定超过 12 页，就在接受前拒绝；读取中到第 12 页仍未完成时，worker (工作进程) 停止并提交有界失败，不能再无限分页。页数限制不限制单次 I/O 可能无限等待，因此每页读取和对象上传还各自配置并强制执行有限截止时间；具体时长须与客户端、存储和租约策略一起设定。

请求路径中的账户号和随机 job ID 不是授权凭据。`report:read` 不自动包含 `report:export`。后台 worker 使用服务身份访问有限数据，并在开始读取前重新确认原请求主体仍有本报表导出权限；若授权此时已撤销，则不读数据，提交有界的 `authorization_revoked` 失败结果。状态、取消和下载端点也各自检查调用者对该 job 与结果的当前访问权。

若条件满足，响应可为：

~~~http
HTTP/1.1 202 Accepted
Location: /v1/jobs/job-demo-731
Content-Type: application/json

{"jobId":"job-demo-731","status":"queued","cancelRequested":false,"statusUrl":"/v1/jobs/job-demo-731"}
~~~

HTTP 的 `202 Accepted` 表示请求已接受处理，但处理尚未完成，也不承诺之后一定成功。这个服务把“已接受”定义得更强：只有 job、待发布 outbox (事务发件箱) 意图和一个等待槽已在同一数据库事务提交，才返回 202。若数据库提交结果对 API 仍未知，就不能猜测成功；客户端使用原幂等键重试，已有 job ID 时也可查状态，数据库唯一键会把它与已提交记录重新关联。这个应用契约让 `202` 成为可查询的承诺，而不是“内存里排了一个后台任务”。

此处的 `202` 和过载响应是本服务定义的接口合同，具体成功与错误表示仍要有一致的 HTTP API 契约，见[如何设计可预期的 HTTP API 契约？](#3.%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F)。如果客户端在请求仍可能提交时就超时，必须用同一幂等键和查询路径查证，不能创建一个新意图；其他超时、截止时间与重试边界见[请求超时后如何确认结果并安全重试？](#%E8%B6%85%E6%97%B6%E5%92%8C%E6%88%AA%E6%AD%A2%E6%97%B6%E9%97%B4%E8%AE%A9%E8%B0%83%E7%94%A8%E6%96%B9%E5%A4%84%E4%BA%8E%E4%BB%80%E4%B9%88%E7%8A%B6%E6%80%81%EF%BC%9F)。

幂等键在本例按 `(account_id, principal_id, key)` 唯一，并绑定规范化请求指纹，例如报表 ID、期间和格式。新请求在事务中尝试插入带唯一键的 job 身份；唯一约束裁决谁成为这项新意图的胜者。只有胜者才在**同一事务**内预留一个准入令牌与等待槽、补齐 job 参数并写入 outbox，再一起提交。若令牌或槽位不足，事务回滚，未提交的 job 行也消失，不留下已接受的半条记录。

相同键的并发败方等待唯一约束裁决后回滚，再用新事务读取胜者并比较指纹：同指纹返回同一个 job，不再扣令牌或占槽；异指纹返回冲突。

令牌与等待槽通过所有副本共享的配额行管理：扣减使用带余量条件的原子更新，或锁定该行后检查并扣减。两个不同幂等键也必须争用同一份余量，不能各自先读到最后一个空槽就都接受。这里的合成服务把令牌桶也放在同一数据库事务内；若改用外部限流器，必须另设可幂等确认或补偿的预留合同，不能假定数据库回滚会退回外部令牌。不能只先 `SELECT` 再 `INSERT`：并发请求可能都先查无记录。队列消息只携带稳定 job ID，不塞入原始正文或敏感筛选条件；worker 所需的规范化参数在 job 中单独持久保存，指纹只负责比较。

![新请求经过认证、授权和范围限制后，在 job、outbox 与等待槽同事务提交才返回 202](../../engineering-foundations/architecture/resources/system-design-admission.svg)

图一只画首次接受新 job 的成功路径。幂等重放不创建新 job：若并发唯一键争用使本事务失败，调用方先回滚，再读取胜者；同指纹返回同一个 job，异指纹返回冲突。等待槽达到共享上限 240 时事务回滚，在 202 前拒绝；数据库不可用或提交结果未知时，服务也不能声称接受成功。

状态查询返回 job 的持久状态与有界错误码。取消用 `DELETE /v1/jobs/job-demo-731` 表达“请求停止”，不代表计算已立即停止；运行中 job 可继续显示 `running` 并带 `cancelRequested=true`。只有 `succeeded` 且对象仍在保留期内，结果端点才允许下载。例：

~~~http
GET /v1/jobs/job-demo-731/result
~~~

每种终态都写 `terminal_at`；成功事务还以数据库时间写 `succeeded_at` 和 `result_expires_at = succeeded_at + 7 days`，与对象引用一起提交，结果从这次提交起对用户可见。job 与最小幂等映射从 `terminal_at` 起保留 14 天，以覆盖更长的重试窗口。

对象过期后 job 仍是 `succeeded`，端点返回 `result_expired`，同一幂等键仍指向原 job，不自动重建。删除 14 天后的幂等记录就不再提供窗口外重放保证；若业务要拒绝任意久以前的键，须保留能识别它的墓碑。

job 的 `status` 和 `attempt` 描述执行生命周期；若产品要说明报表读到的数据版本，应把版本作为结果元数据保存。若报表承诺一个精确的“截至时点”，请求还须持久化对应的数据水位或快照语义；有限时间过滤本身不保证多个分页读取来自同一快照。

### 任务、发件箱与队列怎样交接？

系统至少维护五个 job 状态；`cancel_requested` 是独立标志。`outbox.state` 是另一条生命周期，不可代替 job 状态。

| 持久状态 | 含义和下一步 |
| --- | --- |
| `queued` | 已接受但尚未领取的逻辑排队轮次，可能仍在 outbox 中待发布，也可能已进入 broker；持有一个共享等待槽；达到 `available_at` 后才能领取。 |
| `running` | worker 已成功条件领取，等待槽释放，当前 attempt 与有界 `lease_expires_at` 已写入。 |
| `succeeded` | 当前 attempt 的私有对象引用与成功状态已一起提交；同一事务还写入 `report.ready` outbox。 |
| `failed` | 不可重试错误、达到本 job 的最多三次 attempt (含首次)，或重试/恢复时没有等待槽；错误用可查询有限码表达，如 `authorization_revoked`、`attempts_exhausted`、`capacity_exhausted`。 |
| `cancelled` | 取消赢得状态竞争后的终态，不暴露结果对象引用。 |

job 行还需保存 job ID、账户与原请求主体、`report_id`、规范化参数、请求指纹与幂等键、创建时间、不可变的 `max_attempts=3` 策略、当前 attempt、租约、最早可领取时间 `available_at`、是否持有等待槽、`cancel_requested`、成功/终态时间、结果到期时间、私有结果引用和范围受限的错误码。初次任务的 `available_at` 取当前数据库时间，延迟重试则保存退避到期时间，relay 与 worker 使用同一数据库时间基准。

三次上限包括首次领取，最多允许两次重试；为已有 job 改部署配置时不能悄悄改变其上限。终态一旦提交就不再回到 `queued` 或 `running`；取消请求是字段，不是终态。outbox 有自己的 `pending` / `published` 状态。已确认发布的 outbox 行在满足审计和重放保留期后按策略清理；未决发布意图要保留，不能跟成功结果对象使用同一删除条件。每次新排队轮次产生独立唯一 outbox 意图，relay 的回写以该意图 ID 为条件，旧轮次的迟到确认不能把新轮次也误标为已发布。

从上节提交后的状态继续：job、等待槽与 `pending` outbox 已持久保存。未开始任务的上限 240 覆盖 outbox 和消息代理（broker）中相同逻辑 job 的等待轮次；它们迁移位置或重复投递都不会重复计数。提交后 API 才返回 202，独立 relay (转发进程) 扫描 outbox 并向选定 broker 发布稳定 job ID。

数据库与 broker 没有一个普通原子事务可同时覆盖双方。先提交 job 后直接发布，进程可能在两步间崩溃，留下无人唤醒的 job；先发消息再提交，数据库回滚后消息会引用不存在的 job。outbox 把业务提交和“将来必须发布”的意图放进同一数据库事务。relay 可能在 broker 接收后、回写发布状态前崩溃，于是再次发同一意图。因此消息可能重复；worker 依据数据库 job 状态和条件领取消重，而不是假设消息只投递一次。relay 只有按所选 broker 的契约核对发布结果、所需路由与持久性条件后，才把意图标为 `published`；publisher confirm (发布者确认) 本身未必证明目标路由正确。发布结果不证明 worker 已经处理；consumer acknowledgement (ACK，消费者确认) 也不证明报表成功。各 broker 的精确边界由其协议决定，见[发布确认、消费者确认与业务完成各证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

![已提交的 job 经 outbox 与 broker 唤醒，worker 先取物理执行槽，再条件领取当前排队轮次](../../engineering-foundations/architecture/resources/system-design-execution.svg)

图二的终点是一个已取得执行权的 attempt：job 已变成 `running`，等待槽已经归还，但物理执行槽仍由这个 attempt 占用。领取条件未命中时，worker 归还刚预占的物理槽，再读权威 job 决定保留或确认投递；不能继续读数据。取得执行权后，才进入下图的读取和结果发布。

![当前 attempt 复验权限、读取与上传后，只有更新一行且提交确认才走成功 ACK；零行或提交未知另行查证](../../engineering-foundations/architecture/resources/system-design-result-commit.svg)

图三展开有权且成功读完后的结果发布，以及成功条件未命中的分支。worker 只有在取得本进程的物理执行槽后才领取；成功路径先完成有界读取并上传 attempt 专属私有对象，再在一个数据库事务里以当前 job 状态、attempt 和未取消条件写入 `succeeded`、对象键与 `report.ready` outbox。**只有条件更新恰好一行且 `COMMIT` 确认后，才走成功 ACK。**

更新零行时下面的 common table expression (公共表表达式，CTE) 不产生 ready，但整个事务仍可成功提交；零行本身不是 ACK 许可。此时要从新连接读权威 job 与 outbox：已持久终态或已提交且可恢复的后继路径才允许确认旧投递；若仍没有持久终点，就保留投递。提交结果未知时，一次读到旧 `running` 状态也不能证明原事务回滚。对象引用结局未决时不要把 attempt 对象当孤儿删除。取消、永久失败、重试和租约接管各有自己的 ACK 条件，具体投递 tag 与确认行为取决于 broker。

> [!example]- 对照 SQL 看同一事务怎样限定 ready 意图
> 下面的极简事务只展示状态更新与 ready 意图的原子边界，省略完整表定义、成功/终态时间戳和三次上限字段：若条件更新未命中，CTE 不产生行，`report.ready` 也不插入；外层事务仍可成功提交，所以不能仅凭 `COMMIT` 成功就 ACK。对象上传在事务外，因此可留孤儿；消费者不能因上传成功就报告结果可用。
>
> ~~~sql
> BEGIN;
> WITH completed AS (
>   UPDATE report_jobs
>   SET status = 'succeeded', result_object_key = :attempt_object_key
>   WHERE job_id = :job_id
>     AND status = 'running'
>     AND attempt = :attempt
>     AND cancel_requested = FALSE
>   RETURNING job_id, attempt
> )
> INSERT INTO report_outbox(operation_key, job_id, attempt, payload)
> SELECT :ready_operation_key, job_id, attempt, :ready_payload
> FROM completed;
> COMMIT;
> ~~~

relay 重发时重用数据库中同一条持久 outbox 意图和稳定操作键，不为未知结果造新通知。`report.ready` 与结果引用同事务，避免“ready 已发，job 仍在 running 或后来由 B 接管”的假成功通知。

### 工作进程重试怎样避免旧结果覆盖新结果？

队列中的 job ID 只是唤醒线索，不携带 attempt。worker 持有物理执行槽后，任何唤醒——包括上一轮迟到的旧投递——都可以条件竞争**当前**的 `queued` 轮次。领取事务只允许一个 worker 把状态改为 `running`、增加 attempt、设有限租约并归还本轮等待槽一次；投递本身不能创建新轮次。旧 attempt 能否写入由数据库当前状态和 attempt 栅栏决定，而不是靠辨认唤醒消息的新旧。队列预取量和进程内缓冲要有界，避免任务虽未获执行槽却已离开 broker 堆在内存中。物理槽与等待槽不同：前者表示活进程正在占用 CPU、连接、游标或上传句柄；后者只表示一个未开始的逻辑 job 等待被领取。

领取、取消、完成和恢复都要竞争数据库中的当前 job 行，条件字段至少包括 job ID、状态、attempt 和取消标志。租约到期**只让独立恢复器取得竞争接管资格**，不会自动撤销旧 worker 的提交权。到期后恢复器与原 worker 可能同时继续；若 worker 的成功事务先提交，job 成功，恢复器随后看到终态便不重排；若恢复器先把 job 原子改回 `queued`，旧 worker 的成功条件就不匹配。fencing (写权栅栏) 发生在恢复事务提交处，不是时钟到达租约时刻。

> [!example] A 停顿后，B 怎样接手同一份报表？
> A 领取 `job-demo-731 / attempt=1` 后停顿。租约到期时，A 还可能先提交成功；只有恢复器先提交 `running → queued`，才阻止 A 的旧成功更新。B 随后领取 `attempt=2` 并提交结果，A 再恢复时，条件 `attempt=1 AND status=running` 已不匹配，更新零行。A 的私有对象不会替换 B 的结果；A 自己占用的物理槽则要等 A 停止并释放资源。

本例把总尝试上限定为三次，初次领取也计一次。worker 发现可重试的暂时错误并停止当前工作后，或恢复器在租约到期后取得接管资格时，都用同一决策顺序：先核对 job 和当前 attempt；取消请求优先落为 `cancelled`，永久错误或 `attempt >= max_attempts` 落为 `failed`，否则只有预留到等待槽才可重排。

重排事务把 `queued`、下一次 `available_at`、新的 `pending` outbox 和一个等待槽一起提交；relay 按持久的 `available_at` 安排到期唤醒，过早重复到达不能越过 worker 的条件领取，且只有已持久安排到期唤醒时才可确认早到投递。槽已满时持久失败为 `failed/capacity_exhausted`，不能靠 broker 无限重投。恢复器只有在自己的事务提交时才 fence 旧 attempt；单纯发现 lease 到期不改变旧 worker 的写权。例：attempt 1 暂时失败、停止业务操作后预留槽并写退避唤醒，attempt 2 可以成功；若 attempt 1、2、3 都失败或失联，第三次后的恢复写 `attempts_exhausted` 终态，不再预留第四次。

若 relay、broker、worker 或数据库长期不可用，任务无法继续推进；有限的 attempt 截止时间、lease 扫描以及这些组件最终恢复并取得进展，是该例的活性条件。已排队任务仍持有等待槽，240 槽满后 API 停止接受新 job。

| 并发结果 | job 与等待槽 | 外部对象及投递 |
| --- | --- | --- |
| worker 成功先提交 | `running → succeeded`；提交结果引用及 `report.ready` 意图；无需等待槽。 | 当前 attempt 对象成为唯一公开引用，成功提交后可 ACK；恢复器不得重排。 |
| 运行中取消先标记 | 状态可暂时仍为 `running`，`cancel_requested=true`。 | worker 到有界检查点后条件提交 `cancelled` 与清理决定；在终态提交前不 ACK。 |
| 恢复器见到取消 | 条件写 `cancelled` 与对象清理/保留决定。 | 不重新排队、不占等待槽；决定持久后旧 delivery 可 ACK。 |
| 恢复器先提交接管，未取消、`attempt < max_attempts` 且存在空槽 | `running → queued`，同事务重新预留一个共享等待槽并新增 `pending` outbox；随后新 worker 领取并增加 attempt。 | 旧 attempt 被数据库状态栅栏阻止写结果；其物理执行槽仍要等旧 attempt 实际停止并释放资源才归还。 |
| 可重试失败/恢复时达到 `max_attempts` | 写 `failed` 与 `error_code='attempts_exhausted'`，不占槽、不新增 outbox。 | 这是持久终态；终态与必要清理决定持久后可 ACK，不再安排下一轮。 |
| 可重试失败/恢复时 240 槽已满且尚有 attempt 额度 | 写 `failed` 与 `error_code='capacity_exhausted'`，不占槽、不新增 outbox。 | 这是持久终态，不是无限 nack/requeue；终态与必要清理决定持久后可 ACK。 |

若 job 仍为 `queued` 且持有等待槽，取消事务可条件地写入 `cancelled` 和对象处理决定并只释放该槽一次。领取与取消同时发生时由 job 行的条件更新决定唯一胜者：领取先提交时已经释放等待槽，API 不能再释放一次，只能给 `running` 写 `cancel_requested=true`；取消先提交时 worker 领取条件不匹配。运行中 worker 在有界检查点发现取消请求后，以 job、状态、attempt 与取消标志为条件提交 `cancelled`；如果它先失联，租约到期后的恢复器提交相同的取消终态，不会为了取消去抢等待槽。`cancel_requested` 还不是 ACK 许可，终态或可靠后继恢复路径仍须先持久化。

“请求取消”“发出停止信号”“租约到期”“数据库已栅栏旧 attempt”都不证明旧 attempt 已停止。该 attempt 实际停止并释放它占有的连接、游标和上传资源后，才归还物理执行槽；同一进程仍可运行其他 attempt。若取消请求和成功提交同时发生，条件事务的提交顺序选出唯一终态：取消先写入时，成功条件失败；成功先提交时，取消端返回现有成功状态，不改写终态。

每个 attempt 写到独立、只用于该次尝试的私有对象键，例如 `reports/job-demo-731/attempt-2.csv`。B 成功后，A 迟到的数据库更新因状态或 attempt 不匹配而影响零行；A 的对象不会被用户下载。若旧 attempt 仍可能在被栅栏后开始上传，则一次孤儿扫描不够：只有上传能力已撤销或存在明确的最大上传启动/持续时间，且安全宽限和存储传播时间已过，再次确认对象键未被任何已提交结果引用，才删除。当前 attempt 确认停止与异步孤儿回收是两个独立责任，不需要为了清理孤儿继续占 worker 槽。

对象写入若选 Amazon S3，`If-None-Match: *` 可阻止覆盖当前同名对象；这是避免覆写的存储条件，并不能代替数据库 attempt 栅栏。另一种存储应按其写入条件语义设计，案例本身不依赖 S3。

### 何时应排队，怎样设容量边界？

沿用同一工作负载，4 个 worker 副本、每副本 2 个进程、每进程 8 个并行 attempt 槽，共 64 个物理执行槽；每个 attempt 平均占用六秒。若峰值每秒 20 个新 job 都被长期接受，且每个 job 只需一个 attempt，平均就需要 `20 × 6 = 120` 个并发 attempt，超过 64 槽；实际重试还会增加总 attempt 槽秒，租约恢复重叠时旧 attempt 仍占物理槽。队列只能暂存超出服务能力的任务，不能消除持续过载。容量页继续计算在假设的 70% 平均利用率下把准入目标设为每秒 7 个新 job、短时突发 30 个、未开始任务 240 个，并给出共享数据库连接池 200 的预算拆分。这里的 7 是**每秒 7 个新逻辑 job**，不是七秒等待时间。

准入要分别限制速率、短时 burst (突发) 和持久等待槽。相同幂等键重放返回既有 job，不算新逻辑 job，也不多占令牌或槽，但每个 HTTP 重放仍耗 API 计算资源。新 job 在 202 前同时拿到 job/outbox/等待槽；恢复器重排也必须先取得槽再提交新 outbox。已有 broker 深度很低不证明系统空闲：outbox 未发布的 queued job 仍在 240 槽统计中。持续容量不足时拒绝新任务；本例每个 job 最多三个 attempt (包含首次)，暂时失败与租约恢复都须在当前 job/attempt 条件下决定取消、耗尽、容量或重排。最多三次只限制开始次数，不是旧 attempt 立即停止的保证；被 fence 的 attempt 仍占物理槽直到该 attempt 停止并释放资源，故要用有限读取/上传截止时间及可观察的停止路径限制资源重叠。无等待槽时将 job 持久失败为 `failed/capacity_exhausted`，不可通过无限消息重排把存储和数据库压力转成看不见的积压。

上线时要让 API、relay、worker 的 schema (数据库结构与消息字段) 兼容窗口覆盖已经接受的任务；升级不能假定队列中只有新版本消息。运行中监控 API 受理时延、最老 pending outbox 与 queued job 年龄、broker 最老消息年龄和深度、活跃物理槽、成功完成分位数、重试/取消/容量失败、数据库连接池等待与 SQL 时长、对象存储用量。指标各自只覆盖一段路径；broker 没有积压，仍可能有旧 outbox 或数据库 queued 任务。容量估算与池上限见[如何估算并限制异步工作管线？](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)，各阶段的信号和响应见[怎样从报表服务信号定位发布后的故障？](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)。

**继续阅读：** [数据库约束与索引](#8.%20%E5%A6%82%E4%BD%95%E7%94%A8%E7%BA%A6%E6%9D%9F%E4%BF%9D%E6%8A%A4%E4%B8%9A%E5%8A%A1%E8%A7%84%E5%88%99%E5%B9%B6%E4%B8%BA%E8%AF%BB%E5%8F%96%E5%BB%BA%E7%AB%8B%E7%B4%A2%E5%BC%95%EF%BC%9F) 解释幂等唯一键；[事务隔离与预写日志](#9.%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%E9%A2%84%E5%86%99%E6%97%A5%E5%BF%97%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F) 解释数据库内的提交边界；[数据访问与连接池](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F) 解释每个请求和 attempt 的 ORM 连接生命周期；[HTTP 协议与 WebSocket](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F) 解释状态查询的传输边界；[发布确认与消费者确认](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) 解释所选 broker 的具体行为。更长的通用系统设计问答见[AI 系统设计案例](../../ai-engineering/systems/ai-system-design-interview-questions.md)。

> [!info]- 来源
> - `202 Accepted`：请求已接受但处理未完成，协议不承诺操作最终会成功；[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§15.3.3，核对于 2026-11-12。文中要求先持久提交再返回是本例服务比通用 HTTP 语义更强的应用合同。
> - 唯一约束、并发 `INSERT`、`ON CONFLICT` 和隔离级别：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)、[Index Uniqueness Checks](https://www.postgresql.org/docs/18/index-unique-checks.html)、[INSERT](https://www.postgresql.org/docs/18/sql-insert.html)、[Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，核对于 2026-11-12。唯一索引冲突检查会等待尚未提交的冲突行后再裁决；`READ COMMITTED` 下 `ON CONFLICT DO NOTHING` 可能因当前语句快照不可见的并发行而不插入，因此败方回滚后用新事务读胜者。[Data-modifying WITH Queries](https://www.postgresql.org/docs/18/queries-with.html) 支持将 `UPDATE ... RETURNING` 的实际行输入后续 `INSERT`；本例用 CTE 把 `report.ready` 限定到成功更新一行的情况。案例 SQL 与限流表不是文档中的完整 schema。
> - 数据库提交与消息通知的 dual-write 缺口、重复消息和消费者幂等：[AWS Prescriptive Guidance, Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)，核对于 2026-11-12。
> - attempt 对象的可选防覆盖写入：[Amazon S3, Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)，核对于 2026-11-12；所述数据库栅栏不依赖 S3。
> - 安全、可靠性、性能、运维与成本等非功能目标的通用背景：[Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework)，官方页面最后核阅于 2026-10-13，见“Pillars and perspectives”。[官方变更记录](https://docs.cloud.google.com/architecture/framework/whats-new) 记载其于 2024-08-27 移除 System Design 分类；本页不把它当作系统设计清单，具体异步化边界和报表状态是合成案例的分析。
## 16. 报表任务的发布确认、消费者确认与业务完成各证明什么？

案例中，账户 acct-17 发起 report 42 的 CSV 导出；断线后调用方仍要能查状态，并在成功后按授权下载私有对象。application programming interface（API，应用程序接口）在一个数据库事务里创建稳定 job ID（任务 ID）`job-demo-731`、待发布的 outbox（事务发件箱）意图和一个等待槽。等待槽是数据库中的准入计数：每个尚未领取的逻辑排队轮次占一个；领取后归还；重试或租约恢复器重新排队时再次预留；重复消息不增槽。它不是 RabbitMQ 的 consumer prefetch（消费者预取上限），也不是 BullMQ 的 job lock（任务锁）。客户端 idempotency key（幂等键）`report-demo-208`、报表 ID 42 与 job ID 是不同身份；读取报表状态、完成一个 job 和读取结果对象也是不同用户结果。

这条路径有三个能被不同组件观察的事实：数据库是否持久接受 job；broker（消息代理）是否按所配置的路由与持久性契约接受一次发布；应用是否提交了最终业务结果。relay（转发进程）把 outbox 意图发给 broker。publisher confirm（发布者确认）只证明 broker 侧的发布边界；consumer acknowledgement（消费者确认，ACK）只结束 broker 对当前 delivery（消息投递）的待确认状态。按应用的恢复合同，ACK 前还可以是成功、失败、取消等已提交终态，或已持久安排好的重试/接管路径；它本身不证明报表成功。只有 `succeeded` 与私有 object key（对象键）一起提交，才是本例的业务完成。各事实不能互相推导。

![outbox intent 从数据库经 relay 发布到 RabbitMQ；每条 publisher channel 同时只保留一条在途 publish，以当次 return 与 confirm 决定对应 intent 是否可标记 published](../../engineering-foundations/reliability/resources/queue-publish-confirm.svg)

图一使用 RabbitMQ 的 mandatory 发布：如果整条路由没有 queue 接收，broker 会先发 `basic.return`，随后仍可能发 confirm ACK。因此，本例只有收到并核对本次 confirm ACK、没有本次 `basic.return`，且预期目标拓扑与持久性条件均满足，才将该 outbox intent 标为 `published`。每条 publisher channel 只有一次在途发送，使回执能对应到单次发布；未知时弃用旧 channel 再重发，具体关联方式在下一节展开。

`published` 是 relay 记录的发布结果，不是 worker 开始执行的前提。broker 可以先把消息交给 worker，relay 之后才收到 confirm、回写 outbox；图二从消息到达 worker 继续，不需要等待这次回写。

![成功分支中工作进程条件领取、持久业务结果与 ready 意图，再向 RabbitMQ ACK 的顺序](../../engineering-foundations/reliability/resources/queue-consumer-ack.svg)

图二只画成功分支。worker（工作进程）先取得本进程物理执行槽，再在领取事务中同时递增 attempt（尝试号）、写入有界租约并归还逻辑等待槽；对象写好后，成功状态、对象引用与 `report.ready` outbox 意图在同一数据库事务提交，再按当前 RabbitMQ delivery tag 单条 ACK。取消、失败、持久重试和租约恢复分支见下文。

没有数据库与 broker 共享的原子事务时，持久 outbox 消除“数据库已提交、但进程在发布前崩溃”的双写空档；relay 和 worker 仍须接受重复。这里不把“最终业务效果只发生一次”简称为 exactly-once（恰好一次）：它依赖应用状态条件、幂等键、远端效果契约和恢复路径，而不是 broker 的一次确认。

### 发布者确认只回答 broker 是否接收

relay 先为发布 channel 启用 publisher confirms（AMQP 0-9-1 的 `confirm.select` 或客户端对应 API）；`mandatory` 本身不会开启 confirm，它只影响不可路由时是否退回消息。

publisher confirm 覆盖 publisher（发布者）到 RabbitMQ 的通信。它不知道 worker 是否已收到、确认或完成消息。如果 broker 接收了 publish，但 confirm 在网络中丢失，relay 无法区分“broker 未收到”和“broker 已收到但回复丢失”，重发便可能为同一 job 产生重复载荷。outbox 每次调度意图有独立唯一 ID，relay 用这个 ID 更新相应的发布状态；消息载荷只需 job ID。

confirm 的含义还受消息和 queue（队列）类型影响。RabbitMQ exchange（交换器）按 binding（绑定）把 publish 路由到零个或多个 queue；publisher confirm 不是路由保证。mandatory 发布的不可路由消息会以该次 publish 的 basic.return（不可路由返回通知）先于 confirm ACK 返回，因此必须将同一次发布的 return 和 confirm 一起关联；即使有 confirm ACK 且没有 return，也只能说明至少路由到一个 queue。备用 exchange（alternate exchange）可能把消息送往别处，所以预先核验交换器、绑定和目标 queue，不能只以“没有 return”判断目标正确。普通 durable queue 中的 persistent 消息在持久数据写入磁盘后才确认；quorum queue 在 quorum 副本接受并确认后才确认。放在 durable queue 中的 transient 消息即使会写到磁盘，也会在节点重启时被丢弃；要保留重启后的消息，队列和消息持久性都要满足所需契约。

outbox relay 按 intent 读取待发记录，发布它指向的稳定 job ID；publish attempt 的 channel 与 confirm 序号只在内存里关联到这条发送，数据库回写仍以 intent ID 为条件。`basic.ack`/`basic.nack` 在 channel 上带发布序号，可能用 `multiple=true` 一次确认此前多个序号；单条在途约定下，relay 仍核对当前发送对应的 channel 和序号。`basic.return` 是另一条异步回执，不带 confirm 序号；RabbitMQ 保证 mandatory 且不可路由的 return 先于该 publish 的 confirm，单条在途约定让它对应当前唯一未决发送。只有本次 confirm ACK 已按 channel 和序号核实、没有本次 `basic.return`、目标拓扑已核验且所选队列的持久性条件已满足，才把该 intent 标为 `published`。NACK、return、channel 异常/关闭、confirm 缺失或结果未知时保留 intent；若结果未知，关闭并弃用旧 channel 后才由新 channel 重发。这样不能消除 broker 已接受但数据库尚未回写时的重复：RabbitMQ 不按业务 job ID 替应用去重。数据库事务和 RabbitMQ 事务不是一个原子事务，worker 必须按持久 job 状态幂等领取。账户报表如何把 job、outbox 和等待槽同事务提交见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

### 消费者在业务结果持久后才 ACK

本节标题概括成功路径；所有 ACK 都要求应用已持久化终态，或已提交可恢复的重试/接管路径。RabbitMQ AMQP 0-9-1 用当前接收 channel 上的 delivery tag 确认一条投递，不能拿业务 job ID 代替；并行处理时使用单条 ACK（multiple=false），若设 multiple=true，会一并确认该 channel 上更早的未确认 delivery，可能误确认尚未完成的工作。basic.ack 是发送给 broker 的单向方法，没有逐条 ACK 回执；连接在发送后断开时，ACK 是否到达 broker 是未知的，重投后仍按 job 状态判断。

队列载荷只带稳定 job ID，不带 attempt（尝试号）。delivery 是唤醒 worker 查询权威 job 状态的线索，不能自行生成尝试。worker 先取得本进程的可用物理执行槽，再竞争数据库领取；领取事务只允许 `queued` 且 `available_at` 已到期的任务，把状态改为 `running`、增加 attempt、设置有界 `lease_expires_at`，并归还当前等待槽。首次任务可把 `available_at` 设为当前时刻；若需要延迟重试，就把它作为 job 的持久字段，并确保到期时有已提交的新 outbox intent 或其他可靠唤醒。

收到重复 delivery 后，先读权威 job，再决定是否能 ACK 当前这条消息：

| 数据库看到的状态 | worker 可以做什么 | 何时能 ACK 当前 delivery |
| --- | --- | --- |
| 排队已到期 | `status='queued'` 时先取得物理执行槽，再竞争条件领取；只有一个事务能转为 `running` 并增加 attempt。 | 领取成功后继续处理；此处不 ACK；领取失败则重读状态。 |
| 排队未到期 | `status='queued'` 不能让旧的早到消息越过退避。 | 只有后续到期唤醒已经持久安排好时，才能 ACK 早到的重复消息；否则按 broker 契约延后或保留未确认。 |
| 运行中租约有效 | `status='running'` 时不能另起并行 attempt。 | 只有确认独立、持久的数据库租约恢复器会在过期后持久处理（提交终态或可恢复的重排）时，才可 ACK 重复消息；否则保留或延后。 |
| 运行中租约过期 | `status='running'` 时 worker 不能自助领取下一代；到期只让独立恢复器有资格竞争接管。 | 恢复器把取消、尝试耗尽、容量失败或重新排队决定持久提交后，旧 delivery 才有可确认的终态或新唤醒路径；接管提交前不能把过期当作旧 attempt 已失权。 |
| 已到终态 | `succeeded`、`failed` 或 `cancelled` 时不再计算；按既定清理和可查询结果策略处理。容量耗尽以 `failed` 加 `error_code='capacity_exhausted'` 表示，不另造状态。 | 终态、错误码及必要清理/保留决定已持久后可 ACK。 |

取消也要按状态归还等待槽。API 取消一个仍为 `queued` 的 job 时，在一个条件事务中将其改为 `cancelled`、保存清理/保留决定，并只归还该排队轮次仍占有的槽；已发布或之后才发布的唤醒消息只会读到终态，不会领取或增加 attempt。领取与取消并发时由同一 job 行的条件更新决胜：若领取先提交，领取事务已归还等待槽，API 只能对 `running` 写 `cancel_requested=true`，不能再次归还等待槽；若取消先提交，worker 无法领取。

已领取当前 attempt 的 worker 要在有界工作步骤和成功提交前检查取消标志。看到 `cancel_requested=true` 时，由持有该 attempt 的 worker 以 `job_id`、`status='running'`、当前 attempt 和取消标志为条件提交 `cancelled` 与清理/保留决定；它不再归还共享等待槽，因为领取时已归还，只在停止执行时释放自己的物理槽。取消事务若先赢，成功更新将返回零行；若成功终态先赢，取消请求读到该终态，不改写它。若 worker 在持久取消终态前失联，保留可恢复信号，由租约到期后的恢复器先提交 `cancelled` 与同一清理/保留决定；delivery 仅在该决定持久后确认。

这里的 canonical 租期合同与下文独立 SQL 例的严格租期判断不同：领取时在同一事务中设置有界 `lease_expires_at`；到期只赋予数据库恢复器尝试接管的资格，不自动撤销旧 worker 的提交权。旧 worker 与恢复器以 job 当前状态、attempt 和 `cancel_requested` 条件竞争；谁先提交，谁决定后续状态。取消仍能单独阻止成功。只有恢复器接管事务先提交后，状态/代次栅栏才阻止旧 attempt 继续提交。领取、重试、恢复使用哪个 broker，也不改变数据库是业务状态权威这一点。

把同一个 `job-demo-731` 的接管时序展开，就能看清过期、接管和 ACK 不是同一个事件：

| 时点 | 持久状态变化 | 等待槽与 outbox | delivery 处理 |
| --- | --- | --- | --- |
| A 领取 | `queued → running`，`attempt=1`，同一领取事务写入有界租约。 | A 领取时归还该轮等待槽。 | A 处理当前投递；不能在领取后就 ACK。 |
| 租约到期、恢复器尚未提交接管 | 仅恢复器取得竞争接管资格；行仍为 `running / attempt=1`。 | 不变。 | 若 A 的完成事务先提交，job 成为成功且一同写入结果引用与 `report.ready` 意图；恢复器看到终态后不重排。 |
| 恢复器先提交且有取消请求 | 条件转为 `cancelled`，并持久化对象清理/保留决定。 | 不需等待槽。 | 取消终态与清理决定提交后可 ACK。 |
| 恢复器先提交、未取消、尚有尝试额度但 240 个共享等待槽已满 | 条件写入 `status='failed'` 和可查询的 `error_code='capacity_exhausted'`。 | 不预留槽，不写新 outbox。 | 失败状态和错误码提交后可 ACK。 |
| 恢复器先提交、未取消、尚有尝试额度且有空槽 | 同一事务将 job 改回 `queued`，清除旧租约。 | 原子预留一个等待槽并插入新的 `pending` outbox；relay 后续重发该意图。 | 重排、槽位和唤醒意图均持久后，旧 delivery 可 ACK。 |
| B 领取新唤醒 | `queued → running`，`attempt=2`，同一事务写新有界租约。 | B 领取时归还新排队轮次的等待槽。 | A 随后迟到的成功条件更新因状态或 attempt 不匹配而返回零行。 |

若 A 与恢复器同时争夺有效状态，条件更新以行锁与提交顺序选出一个胜者。租约到期本身不等于恢复器已提交；worker 也不能只因时钟已过期就自助递增 attempt。对 `running` 的重复投递，仅在独立恢复器确实会在租约到期后持续接管时，才能安全 ACK；否则要保留唤醒信号。

对象存储不是数据库事务的一部分。worker 先写 attempt 专属的私有对象键，再以 `job_id`、`status='running'`、当前 attempt 和 `cancel_requested=false` 为条件提交 `succeeded` 与对象 key。为保证“已就绪”只对应实际成功的结果，job 更新和 `report.ready` outbox 也必须在同一数据库事务中提交。以下假定 `report_outbox.operation_key` 有唯一约束，outbox 还记录 attempt、正文字节摘要和待发布正文；示例正文是紧凑 UTF-8 JSON，摘要按正文这些字节计算：

~~~sql
BEGIN;
WITH completed AS (
  UPDATE report_jobs
  SET status = 'succeeded', result_object_key = :object_key
  WHERE job_id = :job_id
    AND status = 'running'
    AND attempt = :attempt
    AND cancel_requested = FALSE
  RETURNING job_id, attempt
)
INSERT INTO report_outbox(operation_key, job_id, attempt, request_sha256, payload)
SELECT 'job-demo-731:report-ready:v1',
       job_id,
       attempt,
       'c0cbaddfd93fc90c8af3c368e008d39b71a35d461dc5e59494b3fd99ee31b42a',
       '{"jobId":"job-demo-731","reportId":42,"type":"report.ready"}'
FROM completed
RETURNING operation_key, attempt;
COMMIT;
~~~

只有 `INSERT ... RETURNING` 得到一行且应用确认 `COMMIT` 成功后，才能 ACK 当前 delivery；此时状态、私有对象引用和 ready 意图来自同一次提交。若 CTE 没有完成行，INSERT 也没有 ready 行，worker 必须按零行分支重新读 job 和 outbox。若 `COMMIT` 已发出但结果未观察到，持久结果未知，不能 ACK 或宣称回滚；可用新数据库连接查 job 与 ready 意图，或让 broker 重投后按权威状态恢复。**零行结果不能按普通成功 ACK，也不能与领取时遇到重复 delivery 混为一谈。** worker 重新读取 job 与 outbox，判定后续工作是否已由数据库持久接管：

- 若 job 已是成功、失败或取消终态，且结果/清理策略已持久，当前 delivery 已无待办工作，可 ACK。
- 若恢复器已将旧 attempt 原子重排为 `queued`，等待槽和新 outbox intent 都已提交，旧 delivery 可 ACK；relay 按 `available_at` 到期发布新唤醒，领取谓词阻止旧消息提前运行。
- 若后继 worker 已领取更大的 `running` attempt，只有在 claim 已提交、且独立租约恢复路径可靠时，旧 delivery 才可 ACK。
- 若恢复器尚未提交接管，或重排的槽/outbox 还没有持久化，仍需保住可恢复信号；同样，当前 attempt 仍有效且没有后续恢复保障时不能丢掉 delivery。
- `cancel_requested=true` 仍只是取消请求，不是持久取消终态。旧 worker 的报错或已上传对象都不能替代 `cancelled` 和配套清理/保留决定。
- 若成功 CTE 因 `cancel_requested=true` 返回零行，而该 worker 仍持有相同的 `running` attempt，它走上面的取消提交分支；只有 `cancelled` 与清理/保留决定提交后才能 ACK。若行已是另一 attempt 或其他终态，则按重读后的权威状态处理，不能由旧 worker 替它编造取消结果。

故障位置决定消息、job 和外部对象的关系：

| 失败时点 | broker 可能的动作 | 应用须保住的事实 |
| --- | --- | --- |
| broker 接受 publish，relay 没收到 confirm | relay 按 outbox 重发，同一 job ID 可出现多条消息 | 每个 outbox intent 用自己的 ID 回写；worker 仍以 job 的条件领取与终态更新消重。 |
| worker 在持久结果前崩溃且尚未 ACK | RabbitMQ 在连接或 channel 关闭后会重排未确认 delivery | 重投只触发读取 job；有效 attempt 不并行，租约过期还要等恢复器提交接管。 |
| 数据库已提交 `succeeded`，ACK 是否到达未知 | delivery 可再次到达 | 后继 worker 读到终态后 ACK，不重复生成/覆盖结果。 |
| 先 ACK，再提交结果前崩溃 | broker 可删除 delivery，不会因这条消息自动重投 | 任务是否可恢复只取决于独立、持久的租约扫描和重排；没有它，job 可能永久滞留。 |

若对象已写而数据库提交失败，会留下不可见对象。使用 attempt 隔离的不可变 key；清理时逐个检查候选对象键不被任何已提交 job 结果引用，而不要求整个 job 没有结果——例如 B 的不同键已成为结果，A 的键仍是孤儿。

清理计时从数据库提交 attempt 已不再当前的栅栏或 job 终态开始，不从租约过期开始。只有运行环境能保证旧 attempt 此后不能再发起 PUT，且 fence 时已开始的 PUT 有最大持续时间，才能在此上界、对象存储传播余量和安全宽限都过去后执行一次清扫。若停顿的旧进程仍可能在 fence 后开始 PUT，单轮扫描不足以证明它不会再出现；旧写入能力被撤销或到期后，还要从最后可能开始 PUT 的时刻等待最大上传时长与宽限，再做最终清扫。权限未设有限失效时间时，持续重扫候选键；每次删除前重查该键是否仍被结果引用。

数据库成功提交而 ACK 是否到达未知时，job 终态和 attempt 条件要让重复 handler 只确认已完成，不能再次产生业务副作用或覆盖引用。

### 重试、并发窗口与顺序会改变负载

RabbitMQ 4.4 的手动确认模式下，未 ACK 的 delivery 在 channel 或 connection 关闭后可被重新排队；这是 RabbitMQ 的行为，不能推广到所有 broker。automatic acknowledgement（自动确认）模式在 broker 发送后就视为已交付，worker 若尚未持久结果便崩溃，broker 不会为这条 delivery 自动重投。可靠工作使用手动 ACK，并在 ACK 前持久化终态或可恢复的后续路径。发送后 ACK 是否到达 broker 是未知的网络结果；basic.ack 不会再得到逐条 ACK 回执。

当前 attempt 遇到不可重试的业务错误时，以仍持有该 `running` attempt、且未请求取消为条件，先持久写入 `failed` 和有界错误码，再 ACK。若取消已请求或其他状态转移先赢，则重读 job，走相应的取消或恢复分支。

worker 遇到可重试的瞬时错误时，不能只对旧 delivery 执行 nack(requeue=true) 并期望它自然成为下一 attempt：job 若仍在 running，条件领取仍会拒绝它，快速重排还可能形成热循环。先按 job/attempt 条件锁定并重读取消状态：若已请求取消，持久写 `cancelled` 并完成清理决定；若尝试耗尽，持久写 `failed` 和有界错误码；若没有可预留的等待槽，在本例 240 个共享槽的上限下持久写 `status='failed'`、`error_code='capacity_exhausted'`。只有未取消、仍可重试且有容量时，才在同一数据库事务中把 job 改回 `queued`、写 `available_at=next_retry_at`、清除旧 lease、重新预留一个等待槽并插入新的 pending outbox intent。新时间、槽位和唤醒意图提交后才 ACK 旧 delivery；relay 在时间到期后发布，worker 领取条件再次核验数据库时钟。格式错误、无法映射有效 job 的消息不能无限重排；将它隔离到配置好的 dead-letter queue（死信队列，DLQ）或可告警拒绝路径。

RabbitMQ 的 consumer prefetch（消费者预取上限）限制尚未 ACK 的 delivery 数，决定 broker 可提前压到 worker 缓冲区多少任务。对 Advanced Message Queuing Protocol 0-9-1（高级消息队列协议，AMQP 0-9-1），`basic.qos(count)` 在 RabbitMQ 中按每个 consumer 分别施加；例如同一 channel 上三个 consumer 各设 4，可同时各有 4 条未确认消息。值 `0` 表示无限；若消费者没显式配置，broker 也可应用管理员设置的默认值。全局 per-channel QoS 从 RabbitMQ 4.3 起弃用并默认禁用。预取不是业务并发保证：还要看 handler 并发、进程内队列、数据库/对象存储容量和可用执行槽；过大预取会把等待从 broker 搬进 worker 内存，也延长停机时未确认工作的回收。

若业务要求按账户、订单或报表顺序处理，先定义顺序键与所需的提交顺序。first-in, first-out（先进先出，FIFO）队列只能描述某些消息的排队/交付次序；多个 consumer 并行执行时，较早 delivery 仍可能较晚完成。要保持业务完成顺序，需按键串行处理、单一有序分区，或用持久序号条件更新拦住越序提交。

### BullMQ 的租锁失效为什么会让任务重复执行？

BullMQ 6.7.5（2026-11-11 发布）将 job 状态存于 Redis。若 PostgreSQL job 行仍是报表状态、attempt、租期和结果引用的权威来源，BullMQ 只负责唤醒与调度。每条 outbox 意图有稳定 UUID；将 `outbox-` 前缀与该 UUID 拼成 BullMQ custom job ID 可避开纯数字和冒号。相同意图重发复用该 ID，恢复器生成的新 outbox 意图使用新 ID。BullMQ 6.7.5 官方文档要求 custom job ID 不能只由数字组成，也不能包含冒号；版本源码的校验会拒绝 `42` 和带冒号的 `a:b`，但前导零数字串 `0042` 会通过该校验块，因此不要依赖源码边缘行为，始终添加非数字前缀。custom ID 仅在该 queue 内唯一，job 保留时重复 add 被忽略，移除或自动清理后同 ID 可再次添加。

BullMQ worker 领取 job 后取得有时限的 Redis lock，并需在处理期间续租。进程异常退出、Redis 连接故障或 Node.js 事件循环被 CPU 密集工作占满，都可能使续租未及时到达；stalled checker（停滞任务检查器）随后把 job 放回 waiting 让 worker 重跑，超过 maxStalledCount 后转入 failed 集合。BullMQ 6.7.5 默认 maxStalledCount 为 1；普通处理器异常的 attempts/backoff 重试与锁丢失后的 stalled 恢复计数是两条路径。观察 stalled 事件并让 CPU 工作周期性把控制权交还事件循环；调大 lock duration 会延迟识别真实崩溃，单独调时间不会阻止业务副作用重复。

在本报表合同中，Redis lock 只影响 BullMQ 何时重新投递，不授予或撤销报表写权限。每个外部业务意图仍绑定 job、attempt、请求摘要和数据库状态栅栏；对象键带 attempt，由当前状态/attempt 的数据库条件提交决定哪个对象引用生效。外部操作键应以权威且唯一的 job ID 与操作类型组成，例如 job-demo-731:report-ready:v1；客户端幂等键 report-demo-208 可能只在账户/主体范围内唯一，不能未经范围限定就假设全局唯一。该外部 operation key 可以包含冒号，但不能直接用作 BullMQ job ID。远端按稳定操作键与相同请求摘要去重，并提供按键查询或明确保留期：查询确认完成就记录并停止；结果仍未知（包括查询不可用）且同键同摘要保证仍有效，才可重试原键；否则保留未知并对账，不换新键盲目再发。BullMQ/Redis 的持久化需由部署显式配置；若允许已确认 job 丢失，运维还须从长期停滞的数据库 queued job 发现并重建唤醒。通用未知效果边界见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

### SQL job 表怎样短时领取并阻止过期 worker 回写？

若任务状态已经权威地保存在 PostgreSQL，也可把 job 表用作 queue-like（类似队列的）工作池。FOR UPDATE SKIP LOCKED 让并发领取者跳过当前被其他事务锁住的候选行，避免把同一个候选同时发给多个 worker；它刻意返回不完整视图，只适合这种竞争领取，不适合作为普通一致性读取。领取事务选一行、提交 running 与递增 attempt/lease 后立即释放行锁；昂贵工作在事务外执行，短事务降低锁等待。这个选择把轮询、候选扫描和行锁压力留在数据库；需要观察空轮询、领取时延与锁等待，负载升高时再决定是否需要独立 broker。

以下独立 SQL 合成任务 ID 为 `pg-job-demo-42`，与上方 RabbitMQ 报表 `job-demo-731` 无关。代码可在 PostgreSQL 14+ 的单个 `psql` 会话从头运行；`psql` 默认每条独立语句自动提交，显式 `BEGIN/COMMIT` 块是示例事务边界，临时表仅在该会话有效。本例使用 PostgreSQL 默认的 `READ COMMITTED`；每条新语句取得新快照，所以在锁住 job 行的事务中，后续 `record_processing` 命令按当时已提交的状态判断当前写权。所有能写同一 job 意图的 worker 都必须先锁该 job 行，避免唯一键冲突来自绕过状态门的并发写入。若系统采用 `REPEATABLE READ` 或 `SERIALIZABLE`，必须按该隔离级别处理并发异常并在需要时重试整笔事务，不能假设仍看到同一结果。表结构故意缩小到 attempt、租约与意图，未建模 canonical 案例的账户授权、共享 240 等待槽或外部 broker。

这个 SQL 示例**特意采用严格租期变体**：每次领取写入 `lease_expires_at`；成功写入还要求条件 UPDATE 执行时租期仍有效，到期即拒绝旧 worker，即使恢复器尚未接管。`report.processing` 是示例中允许在最终结果前发送的事实，用来演示当前 attempt 下的唯一键与摘要判断；它与同一 job 的完成通知不同。前文 `job-demo-731` 的 canonical 合同不同：到期只让恢复器获得竞争接管资格，旧 worker 仍可在恢复器提交前先完成。一个系统必须为同一 job 状态选定一种合同，不能把两套条件混用。

先沿一次执行读结果，再按需展开后面的完整 SQL：

| 时点 | 当前状态与结果 |
| --- | --- |
| A 领取 | job 为 `running / attempt=1`，得到 30 秒租约。 |
| A 到期，B 尚未接管 | A 尝试完成，严格租期谓词不成立，更新零行。 |
| B 接管 | job 为 `running / attempt=2`，写新租约；B 登记 `report.processing` 意图，重复登记的结果见下表。 |
| B 正常完成 | 同一事务写 `succeeded`、`reports/42/attempt-2` 与唯一 `report.ready` 意图。 |
| A 迟到 | attempt 与状态条件均不满足，更新零行，不覆盖 B 的对象引用。 |

这个变体仍把 `report.ready` 与成功状态及对象引用放在同一 PostgreSQL 事务中。worker 先写 attempt 专属私有对象；只有成功条件更新影响一行，job 转为 `succeeded`，结果 key 与 ready outbox 意图才一起提交。若 UPDATE 返回零行，CTE `completed` 没有行，INSERT 也不写意图；因此后来失败或被取消的 attempt 不会发送“已就绪”通知。若 COMMIT 已提交但客户端没读到确认，应用应在新连接上查询持久的 job 与 outbox 表；本示例用临时表，只能在当前 `psql` 会话展示 COMMIT 后两行同时可见，连接结束后临时表也会消失。读取两行是核实事务结果，不是再次发通知。运行中的 B 若随后失联，ready 意图只会由 relay 在成功事务提交后发布；若业务终态是 `failed` 或 `cancelled`，同一事务从未创建 ready。

`record_processing` 的结果列依次是 `authorized`、`inserted`、`existing_intent`、`same_request`。`authorized=false` 时，查询结果不返回 outbox 摘要或比较结果；worker 没有写权，必须停止本次操作。`authorized=true, inserted=true` 表示这次事务新建意图，提交后由 relay 发布。`authorized=true, inserted=false, existing_intent=true` 才表示本次有权查看已存在的唯一键：同摘要是同一持久意图，异摘要是冲突，均不新增或覆盖行。相同摘要只确认意图内容，不授予 worker 绕过 outbox 直接发送或提交 job 的权力；实际发布仍由 relay 按自己的持久状态完成。若授权成立、没有插入但也找不到既有行，说明唯一键/保留假设被破坏，应回滚并告警，不能把 NULL 当成成功。

示例查询结果如下；`NULL` 表示本次没有读摘要：

| 情况 | `authorized, inserted, existing_intent, same_request` | 处理 |
| --- | --- | --- |
| B attempt 2 首次登记 | `true, true, false, NULL` | 提交这条新意图，交给 relay |
| B 同键同摘要重放 | `true, false, true, true` | 只确认原意图已存在，不再插入 |
| B 同键异摘要 | `true, false, true, false` | 报告冲突；不覆盖或再次发送 |
| B 租约已过期或已请求取消 | `false, false, false, NULL` | 无写权；查询结果不返回摘要或比较结果 |
| B 已领取 attempt 2 后的 A attempt 1 | `false, false, false, NULL` | 查询结果不返回 B 的摘要或比较结果，也不提交旧 attempt |

若直接 `INSERT` 抛唯一约束异常，PostgreSQL 当前事务已失败，先回滚再在新事务核查，不能在失败事务里继续 `SELECT`。

`report.processing` 是可在任务完成前发出的事实，与最终的 `report.ready` 分开；后者只由成功状态更新原子生成。成功后的重投只能只读查看既有 ready 意图。若同一 operation key 的摘要不同，它是数据冲突，不能覆盖旧意图或再次发布。外部副作用仍需远端按稳定 operation key 与同一请求摘要去重；远端结果未知且没有仍有效的去重保证时，保留未知并人工对账。

SQL 租期续期也须在锁定 job 行后，以新鲜 clock_timestamp() 检查当前状态、attempt 和未过期 lease；否则已过期 worker 可能等待锁后还把自己的租约续活。严格 SQL 变体里的租期谓词不适用于上方 canonical 报表案例。canonical 接管的完整选择、等待槽与旧 worker 时序见前文，另有[持久报表任务的状态与恢复合同](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

> [!example]- 完整 SQL：严格租期下的领取、意图去重与完成
>
> ~~~sql
> CREATE TEMP TABLE report_jobs (
>   job_id text PRIMARY KEY,
>   status text NOT NULL,
>   attempt integer NOT NULL DEFAULT 0,
>   available_at timestamptz NOT NULL,
>   lease_expires_at timestamptz,
>   cancel_requested boolean NOT NULL DEFAULT false,
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
> -- Worker A：取得执行槽后领取并提交；返回 attempt=1 和新的有界 lease_expires_at。
> WITH candidate AS (
>   SELECT job_id
>   FROM report_jobs
>   WHERE cancel_requested = false
>     AND ((status = 'queued' AND available_at <= clock_timestamp())
>       OR (status = 'running' AND lease_expires_at <= clock_timestamp()))
>   ORDER BY available_at, job_id
>   LIMIT 1
>   FOR UPDATE SKIP LOCKED
> )
> UPDATE report_jobs AS j
> SET status = 'running',
>     attempt = j.attempt + 1,
>     lease_expires_at = clock_timestamp() + interval '30 seconds'
> FROM candidate AS c
> WHERE j.job_id = c.job_id
>   AND j.cancel_requested = false
> RETURNING j.job_id, j.status, j.attempt, j.lease_expires_at;
>
> -- 为了不等待 30 秒，演示中把 Worker A 的 lease 手动置为已过期。
> UPDATE report_jobs
> SET lease_expires_at = clock_timestamp() - interval '1 second'
> WHERE job_id = 'pg-job-demo-42' AND attempt = 1;
>
> -- 严格租期变体：A 到期后、B 尚未接管时尝试完成，返回 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-1', lease_expires_at = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 1
>   AND cancel_requested = false
>   AND lease_expires_at > clock_timestamp()
> RETURNING job_id, status, attempt;
> COMMIT;
>
> -- B 接管过期任务并提交 attempt=2 与新的有界租约。
> WITH candidate AS (
>   SELECT job_id
>   FROM report_jobs
>   WHERE cancel_requested = false
>     AND ((status = 'queued' AND available_at <= clock_timestamp())
>       OR (status = 'running' AND lease_expires_at <= clock_timestamp()))
>   ORDER BY available_at, job_id
>   LIMIT 1
>   FOR UPDATE SKIP LOCKED
> )
> UPDATE report_jobs AS j
> SET status = 'running',
>     attempt = j.attempt + 1,
>     lease_expires_at = clock_timestamp() + interval '30 seconds'
> FROM candidate AS c
> WHERE j.job_id = c.job_id
>   AND j.cancel_requested = false
> RETURNING j.job_id, j.status, j.attempt, j.lease_expires_at;
>
> -- 每个写 intent 的尝试都先锁 job 行；relay 只读 outbox，不绕过此写权门。
> -- 该单条语句仅在当前 attempt 有权时才插入，或比较一个既有同键意图。
> -- existing 与 eligible 连接，所以无写权时查询结果不返回摘要或比较结果；MATERIALIZED 让本次
> -- 决策使用同一条锁定行、当前 attempt、未取消状态和严格租期判定。
> PREPARE record_processing(text, integer, text, text, text) AS
> WITH eligible AS MATERIALIZED (
>   SELECT job_id, attempt
>   FROM report_jobs
>   WHERE job_id = $1
>     AND status = 'running'
>     AND attempt = $2
>     AND cancel_requested = false
>     AND lease_expires_at > clock_timestamp()
> ),
> inserted AS (
>   INSERT INTO job_effect_outbox(operation_key, job_id, attempt, request_sha256, payload)
>   SELECT $3, e.job_id, e.attempt, $4, $5
>   FROM eligible AS e
>   ON CONFLICT (operation_key) DO NOTHING
>   RETURNING operation_key, attempt
> ),
> existing AS MATERIALIZED (
>   SELECT o.request_sha256
>   FROM eligible AS e
>   JOIN job_effect_outbox AS o
>     ON o.job_id = e.job_id
>    AND o.operation_key = $3
>   WHERE NOT EXISTS (SELECT 1 FROM inserted)
> )
> SELECT EXISTS (SELECT 1 FROM eligible) AS authorized,
>        EXISTS (SELECT 1 FROM inserted) AS inserted,
>        EXISTS (SELECT 1 FROM existing) AS existing_intent,
>        (SELECT request_sha256 = $4 FROM existing) AS same_request;
>
> -- B 用 attempt=2 首次登记可在完成前发送的 report.processing；摘要对应下面的原始 JSON 字节。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
>
> -- B 同 attempt、同操作键、同摘要重放；授权仍成立，识别既有 intent，不再插入一行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
>
> -- B 仍有写权但用同一键提交异正文：结果显示摘要冲突，不覆盖既有 intent。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '7d5a6ce6ab778ec8937d1dd76a25e4a3d1b5f9e4cb5c3d7fb43196f3ea8a77f3',
>   '{"jobId":"pg-job-demo-42","type":"report.processing","phase":"other"}'
> );
> COMMIT;
>
> -- B 先过期：即使同键、同摘要 intent 已存在，查询结果也不返回摘要；B 无权发起外部动作。
> UPDATE report_jobs
> SET lease_expires_at = clock_timestamp() - interval '1 second'
> WHERE job_id = 'pg-job-demo-42' AND attempt = 2;
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
>
> -- 恢复租期但请求取消：同摘要行仍不可由该 attempt 读取或再次驱动。
> UPDATE report_jobs
> SET lease_expires_at = clock_timestamp() + interval '30 seconds',
>     cancel_requested = true
> WHERE job_id = 'pg-job-demo-42' AND attempt = 2;
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
>
> -- 当前 job 仍为 B/attempt=2，但租期有效且取消未请求；A attempt=1 无写权，查询结果不返回 B 的摘要。
> UPDATE report_jobs
> SET cancel_requested = false,
>     lease_expires_at = clock_timestamp() + interval '30 seconds'
> WHERE job_id = 'pg-job-demo-42' AND attempt = 2;
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 1, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
> DEALLOCATE record_processing;
>
> -- 只有当前 attempt=2 成功条件更新时，才在同一事务创建 report.ready 意图。
> -- 若 UPDATE 无权提交或影响 0 行，completed 为空，下面 INSERT 也写入 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> WITH completed AS (
>   UPDATE report_jobs
>   SET status = 'succeeded',
>       result_key = 'reports/42/attempt-2',
>       lease_expires_at = NULL
>   WHERE job_id = 'pg-job-demo-42'
>     AND status = 'running'
>     AND attempt = 2
>     AND cancel_requested = false
>     AND lease_expires_at > clock_timestamp()
>   RETURNING job_id, attempt
> )
> INSERT INTO job_effect_outbox(operation_key, job_id, attempt, request_sha256, payload)
> SELECT 'pg-job-demo-42:report-ready:v1',
>        job_id,
>        attempt,
>        'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c',
>        '{"jobId":"pg-job-demo-42","reportId":42,"type":"report.ready"}'
> FROM completed
> RETURNING operation_key, attempt;
> COMMIT;
>
> -- 核实 succeeded、对象引用与 ready 意图来自同一提交。
> SELECT j.status, j.attempt, j.result_key,
>        o.operation_key, o.attempt AS intent_attempt,
>        o.request_sha256 = 'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c' AS same_request
> FROM report_jobs AS j
> JOIN job_effect_outbox AS o USING (job_id)
> WHERE j.job_id = 'pg-job-demo-42'
>   AND o.operation_key = 'pg-job-demo-42:report-ready:v1';
>
> -- A 在 B 提交成功后再迟到完成，仍返回 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-1', lease_expires_at = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 1
>   AND cancel_requested = false
>   AND lease_expires_at > clock_timestamp()
> RETURNING job_id, status, attempt;
> COMMIT;
>
> -- 在本会话核实 COMMIT 后的权威状态和 ready 意图；若真实连接断开，应使用永久表的新连接查询。
> SELECT j.status, j.attempt, o.operation_key,
>        o.request_sha256 = 'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c' AS same_request
> FROM report_jobs AS j
> LEFT JOIN job_effect_outbox AS o
>   ON o.job_id = j.job_id
>  AND o.operation_key = 'pg-job-demo-42:report-ready:v1'
> WHERE j.job_id = 'pg-job-demo-42';
> ~~~

### 观测每个交接点，不能只数 ACK

单独记录 publish 尝试、confirm/return、queue depth 和 oldest-message age、unacked 数、重投、重试、ACK、DLQ、job succeeded/failed 及对象引用提交。oldest-message age 持续增长表示结果延迟，即使队列还在接受消息。broker 继续接收并不代表 worker 有容量；worker 发 ACK 也只表示应用确认到达选择的处理边界，不等于用户后来成功下载了报告。更完整的事故定位见[如何从报表服务信号定位发布故障？](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)。

调用方断线后仍从持久 job 行查询进度；只有 job 到达 `succeeded`，API 才按当前主体权限提供私有结果对象的授权下载。

> [!info]- 来源
> - RabbitMQ 4.4.0（官方 Release Information 标为 2026-10-20 发布；当前文档版本为 4.4，核对于 2026-11-12）：[Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)，publisher confirm 与 consumer ACK 的方向、delivery tag 的 channel 范围、发布序号与 `multiple` 确认、持久消息/queue 与 quorum queue 的确认责任、unroutable 消息在 confirm ACK 前发 `basic.return`、手动/自动确认及关闭 channel/connection 后的未确认消息处理；[AMQP 0-9-1 extended specification](https://github.com/rabbitmq/amqp-0.9.1-spec/blob/main/xml/amqp0-9-1.extended.xml)，`basic.return` 的方法字段不含 confirm 序号；[Java client unroutable handling](https://www.rabbitmq.com/client-libraries/java-api-guide#unroutable)，return callback 接收退回消息属性与正文；[Reliability Guide](https://www.rabbitmq.com/docs/reliability)，故障中途状态与重发；[Consumer Prefetch](https://www.rabbitmq.com/docs/consumer-prefetch)，RabbitMQ 的 per-consumer QoS、`0` 无上限、可配置默认值和 4.3 起 per-channel global QoS 弃用/默认关闭；[Release Information](https://www.rabbitmq.com/release-information)，当前维护版本。队列副本、持久性、exchange/binding/alternate exchange 和客户端 API 仍须按实际部署核实。
> - BullMQ 6.7.5（GitHub 官方发布记录显示 2026-11-11 发布，核对于 2026-11-12）：[Important Notes](https://github.com/taskforcesh/bullmq/blob/v6.7.5/docs/gitbook/bull/important-notes.md) 与 [Stalled Jobs](https://github.com/taskforcesh/bullmq/blob/v6.7.5/docs/gitbook/guide/workers/stalled-jobs.md)，至少一次运行、锁续期、事件循环阻塞与达到 stalled 上限后转失败；[WorkerOptions](https://github.com/taskforcesh/bullmq/blob/v6.7.5/src/interfaces/worker-options.ts) 的 `maxStalledCount` 默认值为 1；[Retrying failing jobs](https://github.com/taskforcesh/bullmq/blob/v6.7.5/docs/gitbook/guide/retrying-failing-jobs.md)，普通失败重试与 backoff；[Job IDs](https://github.com/taskforcesh/bullmq/blob/v6.7.5/docs/gitbook/guide/jobs/job-ids.md)，队列范围内的自定义 ID、保留期间重复 add 的行为、自动移除后的去重边界，以及不能含 `:` 或仅由数字构成的文档约束；版本源码 [job.ts](https://github.com/taskforcesh/bullmq/blob/v6.7.5/src/classes/job.ts#L1278-L1289) 实际拒绝 `"42"`、`"a:b"`，但前导零 `"0042"` 通过该校验块；[Going to production](https://docs.bullmq.io/guide/going-to-production)，Redis 后端持久化需由部署显式配置；[release](https://github.com/taskforcesh/bullmq/releases/tag/v6.7.5)，版本日期。BullMQ/Redis 接收后的持久性仍取决于部署设置。
> - PostgreSQL 当前文档版本 18：[SELECT 的 locking clause](https://www.postgresql.org/docs/18/sql-select.html)，`SKIP LOCKED` 会跳过不能立即加锁的行、并刻意提供不一致视图，适合 queue-like 多消费者领取；[Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html)，行锁生命周期与竞争写入；[Date/Time Functions](https://www.postgresql.org/docs/18/functions-datetime.html)，`clock_timestamp()` 与事务起始时间的区别；[INSERT](https://www.postgresql.org/docs/18/sql-insert.html)，`ON CONFLICT` 和 `RETURNING` 只报告实际插入的行；[Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，默认 `READ COMMITTED` 为每条语句取新快照，重复读和可串行化事务须处理异常/重试。代码在隔离的 PostgreSQL 14.24 临时实例实跑；该版本核查时列于官方支持版本。应用级 attempt、lease 与外部副作用合同不由 PostgreSQL 定义。
> - job/outbox/等待槽/恢复器的 canonical 报表状态见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)；外部未知结果与操作键见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。
## 17. Webhook（回调通知）接收方如何验证并可靠受理？

报表 42 生成后，发送服务要把完成事件交给另一个服务。对方可能暂时不可用，接收方也可能已经提交事件、但返回的响应在网络中丢失；发送端因此无法只靠一次 HTTP 往返知道双方进度。可靠交接要分开回答两个问题：签名验证请求是否来自持有共享密钥的一方、签名所覆盖的字节是否被改动；持久去重判断这个逻辑事件是否已受理。签名不能阻止一份有效请求被重放，事件 ID 也不能单独证明发送方身份。

发送方先在业务事务中写入待投递事件，再由 `relay`（转发进程）发送。接收方完整验证请求后，在同一数据库事务中写入 `inbox`（收件箱）与处理 `outbox`（事务发件箱）。应用观察到提交成功后才向发送方返回首次受理的 HTTP 202；这个提交同时让 `worker`（工作进程）获得可恢复的处理意图，所以 worker 可独立于 HTTP 响应开始运行。每一层都需要自己的稳定标识、持久状态和重复处理规则。队列发布确认、消费者 ACK 与业务完成也各有自己的边界，见[队列投递、确认与业务完成](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

本文定义一个仅供教学的合成 HMAC（Hash-based Message Authentication Code，基于哈希的消息认证码）协议，不兼容 Stripe、GitHub 或任何其他 webhook 提供方。协议参数、请求头、字段格式、重试范围和时间窗口都是本地合约。所有域名、密钥和业务数据均为合成示例。

### 一次通知从业务提交到签名请求怎样走？

报表生成事务把业务状态改为完成，并写一条发送端 `outbox` 行。行里保存稳定的 `eventId`、事件类型、不可变的 UTF-8 正文字节和待投递状态；只有业务事务提交后 `relay` 才可发送它。`eventId` 表示一次逻辑事件，所有重试保持不变。每次新的应用层 HTTP 投递生成新的 `attemptId`、发送时间戳和签名；一次网络层重传同一个 HTTP 请求时，则原样保留这一组头。

正文是一行 JSON。代码围栏不是正文的一部分，围栏内 JSON 结尾也没有额外换行：

~~~json
{"eventId":"evt-report-42-ready-001","type":"report.ready","reportId":42,"createdAt":"2026-11-09T04:00:00Z"}
~~~

第一次应用层发送如下。示例正文恰为 108 个字节，`Content-Length` 只用于 HTTP/1.1 消息定界，不属于本合成签名：

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

在假设的 `2026-11-09T04:10:01Z` 时刻，若重发第一次尝试的原请求，它的签名时间已旧 601 秒，超出 ±300 秒而回 401；第二次应用层尝试使用当前签名时间，时间差为 0 秒。虽然正文的 `createdAt` 已早 601 秒，新尝试仍在验签窗口内；若第一笔已提交，就只命中同摘要重复受理，若第一笔未提交，第二次仍可成为首次受理。

假设接收方已提交 `inbox` 和处理 `outbox`，但 202 响应丢失。发送方在 10 分钟 1 秒后重新投递相同 `eventId` 和完全相同的 108 个正文字节；这次是新的应用层尝试，所以头部时间、`attemptId` 和签名改变，正文中的 `createdAt` 不变：

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

合成合约把要认证的字段和字节定义为：

~~~text
UTF8("v1" + LF + keyId + LF + decimalTimestamp + LF + eventId + LF + attemptId + LF) || rawBody
signature = lowercase_hex(HMAC-SHA-256(secret[keyId], signingInput))
~~~

所有文本字段都为 ASCII，字段之间是单个 LF 字节（0x0A），末尾一个 LF 后直接拼接原始正文。ID 只接受 1–128 个 [A-Za-z0-9._-] 字符；时间戳只接受无前导零的十进制 Unix 秒。示例签名使用演示密钥 synthetic-demo-secret-never-use-outside-example，它不能作为真实凭据。HMAC 通过共享密钥验证完整性和持钥者身份，但不加密正文，也不能提供非否认性：任一持钥方都能生成有效签名。

签名原文不含 HTTP 方法、Host、URL 或路径，所以本例的密钥只用于固定的 `POST /hooks/reports` 授权端点。密钥授权作用域是 (`endpointId`,`sourceId`)；不同端点、发送来源（`sourceId`）或租户授权域必须使用不同密钥值。也可以在已版本化的签名原文中加入受保护的目标字段，额外把签名绑定到请求目标，但这不能替代按来源和租户隔离共享密钥与业务权限。多租户服务要先从已验签的注册项确认来源，再检查该来源获准的租户、事件类型和资源。HTTPS 保护传输通道，仍不能替代事件级验签、去重和业务授权。

![签名输入由本次尝试字段和原始正文组成；`Content-Length` 不参与 HMAC。](../../engineering-foundations/reliability/resources/webhook-signature-input.svg)

### 接收方先验哪一份字节和时间？

#### 保留原字节，先确定请求格式

接收边界应在任何 JSON 解析之前保留应用实际收到的正文内容字节，并先设请求头与正文大小上限。HTTP 消息 framing（定界）由服务器解析；签名覆盖的是 framing 之后的正文内容，不是网络包或 `Content-Length` 文本。此合约拒绝任何 `Content-Encoding`，而且必须在代理或框架自动解压之前拒绝；不能以“在压缩后的字节上验签”作为接受编码请求的替代路径。网关和应用也不得规范化或重序列化正文。本合成端点要求 `Content-Type: application/json`；缺失或使用其他媒体类型时按合约拒绝。

RFC 9110 允许接收方把同名 HTTP 字段行按逗号合并，因此应用仅看到“一个值”并不能证明请求原本只有一个字段行。合约要求每个 X-Webhook 字段在入口只出现一次，字段值必须符合上述 ASCII 语法；重复字段、代理合并后的逗号值、空值、格式错误或不支持的签名版本均返回 400，不得让不同代理与应用使用不同解析结果。入口需在字段折叠前拒绝重复，或能可靠拒绝合并后的值。签名要求 64 个小写十六进制字符；解码为等长 32 字节后，用 constant-time comparison（常数时间比较）与计算摘要比较，避免比较时间透露前缀信息。

#### 从密钥注册项确认来源和时间

接收端先由固定路由确定 `endpointId`；因可信 `sourceId` 还未确定，密钥注册表必须以 `(endpointId,keyId)` 唯一查到一条记录（例如唯一约束 `UNIQUE(endpoint_id,key_id)`），不能等验签后才用来源作用域来消歧。尚不可信的 `keyId` 只用作这个查找键。只允许当前可用的键进入 HMAC 校验；未知、未生效和已撤销的键统一返回 401。用收到的受保护字段和原始正文重算 HMAC，再以常数时间比较摘要，并检查签名时间戳是否落在服务端当前时间的 ±300 秒内。只有这些检查都通过后，才信任所选注册记录中的 `sourceId`（发送来源 ID）；不能从未经验证的头或正文直接取来源。旧、新 `keyId` 在轮换时映射到同一稳定 `sourceId`。撤销按接收方当前生效的注册表状态执行，签名早于撤销时间不保留授权。此 ±300 秒窗口只是合成协议选择，既不是 HTTP 默认，也不是提供方通用规则。认证错误要在查 `inbox` 前拒绝，否则攻击者可通过猜测 `eventId` 探测事件是否存在。

#### 再解析载荷并检查业务授权

通过身份验证后才解析 JSON 并做业务授权：本例只接受指定 `sourceId` 的 `report.ready`，且只允许通知 `reportId` 42；头和正文 `eventId` 必须相同，字段类型、必需字段和 UTC `createdAt` 格式也必须通过。解析器还必须拒绝重复 JSON 成员名并返回 400：HMAC 保证收到的原文字节没被改动，却不会让不同 JSON 解析器对重复的 `reportId` 得出相同值。接收端和恢复 `worker` 必须共享这条严格解析规则，worker 不得用更宽松的解析器从原始正文重新得出不同授权对象。`v1` 是签名格式版本，不是载荷 schemaVersion（结构版本）。收到身份有效但类型或资源未获授权的事件返回 403，不写 `inbox`。

本例还给事件设一个固定投递期限：发送端在 `outbox` 首次提交时写好 `createdAt`，此后保持整份正文不变；新尝试的签名时间戳必须严格早于 `createdAt` + 30 天。示例 `createdAt` 为 `2026-11-09T04:00:00Z`，固定截止点记为 D，值为 `2026-12-09T04:00:00Z`，恰在 D 签发就已过期。身份、签名时间窗、载荷与业务授权检查都通过后，若发送方签发的时间戳达到或超过 D，接收端返回 410 且不写 `inbox`；截止前一秒签发的请求，仍须在 ±300 秒签名时间窗内到达。30 天是这份教学合约的选择，不是 RFC 或 webhook 提供方的默认期限。

#### 每种验证结果对应什么响应

| 验证结果 | 合成合约响应 | 持久状态 |
| --- | --- | --- |
| 重复/格式错误字段、正文过大、错误内容编码、重复 JSON 成员名或无效载荷语法 | 400 | 不写 `inbox`；安全日志只记失败类别 |
| 缺失或不支持的 Content-Type | 415 | 不写 `inbox`；按合约说明支持的媒体类型 |
| `keyId` 未知/未生效/已撤销、摘要不匹配、时间戳超出 ±300 秒 | 401，统一的通用认证失败正文与 challenge | 不写 `inbox`；不暴露具体失败原因 |
| 签名有效，但来源无权发送该类型或报表 | 403 | 不写 `inbox` |
| 身份、时间窗、载荷与业务授权检查均通过，但发送方签发时间达到或超过 `createdAt` 加 30 天 | 410 Gone | 不写 `inbox` |
| 完整验证通过，唯一事件已存在且正文摘要相同 | 202 | 只对照已提交行；不新增处理意图 |
| 完整验证通过，唯一事件已存在但正文摘要不同 | 409 Conflict | 写受限冲突审计/隔离记录，告警 |
| 首次受理的 `inbox` 与处理意图已提交且数据库确认成功 | 202 | 两行均已持久化；worker 可早于应用观察到提交成功时启动 |
| 已观察到唯一键冲突，但后续查询找不到仍应保留的 inbox 墓碑 | 503 + 完整性告警 | 不重跑首次插入；端点/来源首次受理门闩保持关闭，直到恢复或对账 |
| 数据库明确确认受理事务未提交（如正文存储失败后回滚、COMMIT 前失败或明确回滚） | 503 | 两行均未提交；按原事件重试 |
| COMMIT 已发出，但连接中断或未收到提交结果 | 503（若连接仍可应答）；否则请求结果未知 | 可能已提交也可能未提交；不得声称回滚，发送方按原 `eventId` 和原正文重试 |

401 必须包含适用于目标资源的 `WWW-Authenticate` challenge。这里的 Webhook-HMAC 是本合成协议自己定义的私有 auth-scheme（认证方案）；HTTP 规范只提供 challenge/response 框架，并未定义它。由于本例的凭据实际放在 `X-Webhook-*` 自定义请求头，而不在 `Authorization` 中，challenge 不会让这些头自动变成标准 HTTP 认证凭据。公开互操作实现必须发布完整方案规范，并按 RFC 9110 的认证方案注册程序处理；泛型 HTTP 客户端也可能不认识私有方案。由于凭据放在 HTTP 标准认证缓存规则无法识别的自定义请求头上，本合成端点对所有响应都设 `Cache-Control: no-store`；通用认证失败正文不含 `keyId` 是否存在或摘要比较细节：

~~~http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Webhook-HMAC realm="report-webhooks"
Cache-Control: no-store
Content-Type: application/problem+json

{"type":"https://receiver.example.test/problems/invalid-webhook-authentication","title":"Webhook authentication failed","status":401}
~~~

application/problem+json 使用 RFC 9457 问题详情格式；它适合传达 HTTP 接口错误，不是调试信息的出口。`type` 使用稳定且不含敏感数据的 URI；堆栈、密钥查找细节、用户数据和可枚举的攻击线索都不应进入响应字段。RFC 9110 的 401、403、410、409、202、503 语义与此处合成策略分开：具体状态如何对应本合约由本页定义。对 429，RFC 6585 允许 `Retry-After` 提示，并要求缓存不得存储该响应；本例是否遵守提示仍要服从固定截止时间。

### 为什么验签后还要持久去重再应答？

验签只证明请求可信且字节匹配，不证明这条逻辑事件此前没有受理。接收端用 (`sourceId`, `eventId`) 唯一键保护 `inbox`，并存储正文 SHA-256、原始正文 `raw_body`、接收时间与处理状态。处理 `outbox` 通过外键引用 `inbox` 行，并以同一个 `(sourceId, eventId)` 唯一约束限制每个事件至多一条处理意图。该意图表示需要恢复的后续工作。首次受理必须在同一数据库事务内插入两行；只有应用收到该事务提交成功的结果后才返回首次受理 202。提交后的处理意图可独立于 HTTP 响应被 `worker` 领取。HTTP 202 只代表接收方接受待处理工作，不代表 `worker` 已运行、报表已写入或远端副作用已完成。

![接收方先完整验证并授权，再由唯一键决定首次提交或重复分支；数据库提交 `inbox` 与处理 `outbox` 后，worker 可领取已提交意图；应用观察到提交成功后才返回首次 HTTP 202。](../../engineering-foundations/reliability/resources/webhook-acceptance-boundary.svg)

如果请求正文已经保存在数据库，`inbox` 行可直接保留原字节。若用不可变对象存储引用替代字节列，必须先确保对象已完整写成、持久可读，再提交引用；否则 `worker` 无法恢复输入，不能返回 202。对象先写、数据库后提交可能留下孤儿对象，应按不再被引用且经过宽限期后清理。数据库不可写或对象不可读时返回 503。处理终结后可按数据保留政策删除正文，但摘要去重墓碑及其 `dedupe_until` 必须至少保留到下文计算出的时刻；清理只删除已到期且处理 outbox 已终结的墓碑。正文可能含个人或业务数据，限制访问与保留；日志不写正文。

#### 去重墓碑要比最后一份合法请求活多久？

去重墓碑保存“这个事件已经受理”的证据。它必须活到最后一份仍可验签的请求完成数据库裁决之后；否则一份迟到的重复请求会因为旧行已删而被当成新事件。签发截止点 D 已在前文算出，另外三个时间量要覆盖接收端的在途工作与时钟差：

| 记号 | 从哪里开始、覆盖到哪里 |
| --- | --- |
| D | 固定签发截止点，即 `createdAt + 30 天`；本例为 `2026-12-09T04:00:00Z` |
| B | 从最后一次成功检查 ±300 秒新鲜度，到数据库完成提交或确认中止的最长耗时；包含解析、授权、排队、连接池、锁等待和全部事务语句 |
| S | 清理所用数据库时钟最多领先验签实例多少时间；本合约固定该上界 |
| G | 清理调度与存储安全余量 |

能进入数据库受理的请求必须通过验签，且签名时间 `< D`，检查时验签实例的时间因而 `< D + 300 秒`。数据库裁决还可能再占用 B，清理时钟最多快 S，所以把 `dedupe_until ≥ D + 300 秒 + B + S + G` 随墓碑持久保存。清理进程使用数据库时钟，且只清理已经到期、处理 outbox 也已终结的记录。

> [!example] 把保留时间换算到本例时钟
> 为便于计算，假设已强制限制 B = 20 秒、固定 S = 5 秒，再留 G = 5 秒。墓碑最早到 `2026-12-09T04:05:30Z` 才允许清理：它比 D 晚 300 + 20 + 5 + 5 = 330 秒。这些数值只演示推导；部署前必须证明自己的实际上界。

B 不是 HTTP 响应超时：应用返回或断开后，已发出的数据库命令仍可能运行并提交。用从新鲜度检查开始计时的单调预算覆盖所有在途阶段，数据库端还需能强制结束超时事务。PostgreSQL 的 `statement_timeout` 限制单条语句，`lock_timeout` 按锁等待分别计时；PostgreSQL 17+ 的 `transaction_timeout` 限制普通事务时长，较旧版本需另配等效的服务端事务上限。COMMIT 已发出但结果未观察到时，持久状态仍未知，不能因 HTTP 超时宣称事务已停止。

上调 B 前，先延长所有尚未清理的墓碑。S 则不能在旧墓碑删除后放宽：一个更落后的验签实例可能重新接受已被其他实例判为过期的旧签名。持续监控各实例相对数据库清理时钟的偏差与时间回退；偏差超过固定 S，或回退可能重新打开已过期窗口时，暂停该实例受理直到时钟回到固定边界内且稳定。无法监测并强制执行 S 或 B，就不能依此期限删除墓碑。

发送方的重试和人工重放仍须保持原正文与 `eventId`，不能借改写 `createdAt` 重置期限。墓碑一旦删除，接收方无法仅凭 HMAC 复原旧正文，因此此清理规则还依赖已授权发送方遵守事件不可变的合约。较旧但仍合法的签名也可能首次到达；是否重复由有效保留期内的已提交唯一行判断，不能仅凭时间戳或尝试日志返回 202。

#### 同时到达的两个请求怎样裁决？

并发首次投递的裁决依赖数据库唯一约束。验证并授权后的首次插入还要保存 `dedupe_until`：应用按已校验的 `createdAt` 算出固定截止点 D，再加 300 秒、受限最大数据库裁决时间 B、清理时钟偏差上界 S 和清理余量 G。这个参数是保留合同的一部分，不得短于配置上界。可先在 `READ COMMITTED` 事务中做一条无异常分支的插入：

~~~sql
BEGIN ISOLATION LEVEL READ COMMITTED;

INSERT INTO webhook_inbox
  (source_id, event_id, body_sha256, raw_body, status, received_at, dedupe_until)
VALUES
  (:source_id, :event_id, :body_sha256, :raw_body, 'accepted', clock_timestamp(), :dedupe_until)
ON CONFLICT (source_id, event_id) DO NOTHING
RETURNING source_id, event_id;
~~~

应用根据 `RETURNING` 是否返回一行分支处理。若本事务插入了 `inbox` 行，同一事务再插入对应的处理 `outbox` 意图，然后提交；只有 `COMMIT` 成功才可回 202。`outbox` 插入失败时回滚整笔受理事务，响应 503，让发送端在同 `eventId`、同正文下重试。

如果 `RETURNING` 没有行，唯一键已由另一个事务占用。不要把普通 `INSERT` 的唯一约束异常捕获后仍在同一事务里 `SELECT`：PostgreSQL 报错会使当前事务处于失败状态，后续查询要等回滚。使用 `ON CONFLICT` ... `DO NOTHING` 走正常控制流，再用下一条 SQL 读取获胜行并核对摘要：

~~~sql
SELECT body_sha256
FROM webhook_inbox
WHERE source_id = :source_id
  AND event_id = :event_id;
~~~

在 PostgreSQL `READ COMMITTED` 中，每条命令都有新的快照；若先前插入等待了并发事务，后续 `SELECT` 可看到已经提交的获胜行。摘要相同，确认这条仍在有效保留期内的已提交记录后返回重复受理 202，不创建第二个处理意图；摘要不同，把冲突写入受限隔离记录、提交审计后返回 409。有效期内唯一冲突后的下一条 `SELECT` 必须找到墓碑：上面的 `dedupe_until` 保留契约保证清理任务不可能在合规窗口内删掉它。如果 `SELECT` 仍无行，这是保留/时钟/清理不变量遭破坏，不是可重试的正常冲突；回滚并返回 503、告警，不能重跑 `INSERT` 或只告诉发送方稍后重试，否则已经受理的 ID 可能变成新事件。立即把该端点/来源的首次受理切到所有接收实例共享的 fail-closed 门闩，恢复墓碑或完成持久记录核对后才解除；不能确认门闩已覆盖所有实例时，暂停该端点的受理。不能只让当前请求返回 503 后继续接受同一键的自动重试。`REPEATABLE READ` 或 `SERIALIZABLE` 返回的明确序列化失败是另一分支：回滚并重试整个事务；不要把“冲突后读不到墓碑”伪装成序列化重试。

发出 `COMMIT` 后，应用只有在收到数据库提交成功结果时才能返回首次受理的 202。若数据库已明确确认受理事务未提交（例如正文存储失败后回滚、`COMMIT` 前失败或数据库明确报告回滚），503 表示两行都未提交；但如果 `COMMIT` 已发出、连接断开或提交回复没有到达应用，持久状态就未知，不能把它写成“必须未提交”。此时不发 202；连接尚可应答时可返回本合约定义的 503“结果未知”，连接已经断开时发送方观察到的也是未知。数据库可能已提交 inbox 与 outbox，worker 可能已开始；也可能两行都不存在。发送方保留同一 `eventId` 和原始正文重试，让唯一键判定状态，而不是生成新事件键。PostgreSQL 的异步命令接口把“命令已发送”和“应用已取回命令结果”分成两个步骤；单凭客户端未读到结果不能证明服务端没执行提交。

该模式让并发第一次请求只有一个事务能创建处理意图：先行者提交则后行者读到摘要；先行者回滚则等待中的请求可以成为首次写入者。时间戳窗口本身不能当作去重，签名也不能说明 `inbox` 是否已提交。身份认证与业务授权都必须先完成，再用数据库唯一约束判断事件状态。

| 崩溃或不确定时点 | 持久事实 | 接收方后续行为 |
| --- | --- | --- |
| `inbox`/`outbox` 事务提交前 | 两行均不存在，不能回 202 | 合法重试重新走验签、授权和首次受理 |
| `inbox` 与处理 `outbox` 同事务提交后，202 送达前 | 正文、摘要和处理意图都已提交；worker 可独立开始 | 重试先完整验证；同键同摘要只返回 202，不再排队 |
| 已发出 `COMMIT`，但应用未观察到数据库结果 | 两行可能已提交，也可能都不存在 | 不宣称回滚、不回首次受理 202；按原 `eventId` 与正文重试，由唯一键查明状态 |
| 202 已送达、`worker` 尚未完成 | 收件内容与处理意图仍可恢复 | `worker` 从持久输入继续；发送端无需等业务终态才停止重试 |
| 外部效果可能已完成、本地完成记录未提交 | 结果未知 | 按下表查询或以相同稳定 operation key 对账，不生成新键猜测重试 |

异步 `worker` 调用外部系统时，即使请求超时，也可能是远端已完成而本地没收到确认。先用稳定 operation key（业务操作键）查询结果；若远端确认已完成，就本地记录完成并停止。如果结果未知，只有当远端仍明确保证“同一操作键与同一请求摘要”在保留期限内去重时，才用原键和原摘要重试。查询接口暂时不可用，但同键、同摘要去重保证仍有效时，仍可按该保证用原键重试；若查询不可用且无法证明去重保证仍有效、摘要不一致或期限已过，则保持结果未知并人工对账，不造新键自动重发。webhook `inbox` 去重不能替代下游自己的幂等边界。

| 远端副作用结果 | 处理方式 |
| --- | --- |
| 查询按原 operation key 确认已完成 | 持久记录完成，不再发送 |
| 结果仍未知，但远端保证同键、同请求摘要在有效保留窗内去重 | 在该保证仍有效时以原键和原摘要重试，并继续对账 |
| 结果仍未知且没有仍有效的同键去重保证，或摘要不同/期限已过 | 保持未知并人工对账；不换新键自动重发 |

这两个期限彼此独立：webhook 的 30 天截止不会延长远端操作键的去重期限；若远端保证先过期，即使 webhook 发送仍在 30 天窗口内，也不能再盲目重试副作用。反过来，接收端的 `inbox` 墓碑也不能保证远端业务效果不会重复。通用的未知结果与安全重试边界见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

本合成协议不保证事件顺序。若业务要求逐账户或逐资源有序，载荷还需要定义受保护的资源序号；接收方要按序号条件更新或串行化。不能把 HTTP 到达先后当成业务顺序。


### 发送端怎样重试、停止和人工重放？

发送端必须把业务变更与待发送事件放在同一个事务中。否则业务状态已提交、进程却在写 `outbox` 前崩溃时，通知会永久丢失。`relay` 读取已提交 `outbox` 后再发请求；对目标返回 2xx 时把逻辑事件标为已接受。连接超时、连接断开或响应丢失都是结果未知，不表示接收方没有提交：继续用原 `eventId` 和原正文重试，让接收方的唯一键区分首次受理与重复通知。

每次新的应用层尝试先持久记下 `attemptId`、`keyId`、签名时间、事件 ID 和待发送状态，再发请求。若进程在发送前后崩溃，恢复时只把已持久确认的 2xx 视为已接受；若不能证明请求未发出，就视为结果未知并用相同逻辑事件安全重试或对账。保存 `keyId` 和 attempt 记录也使撤销某一密钥后可以找到受影响的未确认事件。网络库自动重发同一请求时，不生成新 `attemptId`，因为它仍是同一组签名头；每个新签名的应用层发送才分配新 `attemptId`。

以下退避、次数与期限是合成发送端策略，不是 HTTP 或 webhook 的统一调度标准：

| 响应/结果 | 策略 |
| --- | --- |
| 任意 2xx | 视为已受理，结束该逻辑事件的发送；本合约接收方返回 202 |
| 408、429、5xx，或连接结果未知 | 在截止前有限重试；429/503 若有 `Retry-After`，按提示等待但仍检查截止时间 |
| 其他 4xx | 停止自动重试，保留原因并进入需处理状态 |
| 3xx 或未定义响应 | 不自动跟随、不猜测含义；进入需处理状态，先修复目标或契约 |

合成 backoff（退避）从约 1 秒开始，指数增长并封顶在 15 分钟，加入随机抖动避免大量发送者同时重试。最多自动发送 12 次（总发送次数，含首次），不是 12 次额外重试。发送端每次发前都检查当前时间，新的签名时间戳必须严格小于正文 `createdAt` 加 30 天；达到截止时间或自动次数上限就停下并告警。若 `Retry-After` 指向截止时刻或更晚，不能越过期限继续投递。RFC 9110 对 503 和重定向中的 `Retry-After` 定义等待建议，RFC 6585 允许 429 携带提示；它们不会覆盖本合约的投递期限。真实提供方的响应码、签名时间、重试与重定向语义必须逐条按其官方契约实现。

达到次数上限后，持久保存原事件、每次尝试与最终原因，等待人工处理。操作员只能在相同的绝对截止时间前重放；正文和 `eventId` 不变，`attemptId` 改变，并用当前有效密钥重新签名。若旧尝试已受理但响应丢失，接收方返回重复 202，不会新建处理意图；若从未提交 `inbox`，此次可成为首次受理。新业务动作应生成新的逻辑事件 ID，并用 causationId（因果事件 ID）关联原事件，而不是改写旧 ID 绕过去重。

### 密钥轮换和撤销怎样覆盖在途请求？

`keyId` 用于查找共享密钥，并且自己也被纳入签名。由于来源尚未通过 HMAC 确认，注册表必须保证 `(endpointId,keyId)` 唯一；`keyId` 在同一端点内是唯一查找键，而不是依赖已验证的来源才能消歧的局部版本名。所选记录包含稳定 `sourceId`、密钥值、可用状态与生效/撤销时间；验签通过后，密钥授权主体仍以 (`endpointId`,`sourceId`) 为作用域。不同端点或不同来源不能复用同一密钥值；同一发送来源轮换时，新旧 `keyId` 映射到同一 (`endpointId`,`sourceId`)，确保 (`sourceId`,`eventId`) 去重仍贯穿密钥版本。密钥值只放在受控 secrets manager（秘密管理服务）或等价安全存储中，不进入代码仓库、明文部署配置或日志。

正常轮换先在所有可能接收请求的实例部署新密钥，使短暂重叠期同时接受旧、新 `keyId`；确认接收侧新键可用后，所有发送实例切到新 `keyId` 并停止用旧键签名。只有在所有发送实例都已停止旧键签发之后，才统计最后一次旧键签发时间的最大值。待每个可能接收请求的实例时钟都晚于“最大旧签名时间 + 300 秒”，并再经过最大请求处理时限与已知时钟偏差余量，才从接收侧撤下旧键。本文 `outbox` 保存未签名的原始正文，签名在每次尝试时生成，因此未发事件可用新密钥签名，不需用旧密钥延长积压期。不能简单从最后一次发送开始等待 300 秒，因为接收方时钟可能落后。若系统把已签名请求提前排队，必须在期限前重签，或等请求失效并完成在途排空后再撤键。

怀疑旧键泄漏时，走紧急撤销，不等待正常排空：撤销操作的生效边界是所有可能接收请求的实例都已拒绝该旧 `keyId`；在此之前仍可能有实例接受它。不得只为交付可用性继续信任泄漏密钥。如果新键尚未下发，暂停该来源的发送并完成安全换键后恢复。根据旧 `keyId` 筛选所有未确认事件，再在原 30 天期限内以相同 `eventId`、相同原始正文和新 `attemptId` 重新签名投递。事件此前若已被受理，唯一键会让重试只得到重复 202；已确认的事件不需重放。密钥撤销不会删除 `inbox`/`outbox`、延长期限或撤销已发生的外部副作用。

### 怎样观察交接有没有卡住？

发送端需要把 `eventId` 与每个 `attemptId`、`keyId`、端点标识、发送时间、状态码/传输结果、下一次尝试时间和事件年龄关联起来；接收端记录 `eventId`、`attemptId`、`keyId`、签名时间偏移、验签类别、业务授权类别、首次受理或重复命中、正文摘要冲突和 `inbox` 到业务终态时延。日志不记录密钥、完整签名头、`Authorization`、自定义凭据头或原始正文。摘要也可能成为敏感数据的稳定指纹，应受同样访问控制，不要拿它替代公开日志中的事件 ID。

监控要把边界分开：认证失败或时间偏移升高表示请求尚未进入受理；认证通过后 503 要区分数据库明确确认未提交的持久化/对象故障，与 COMMIT 结果未知——后者不能据此判断数据未写入；冲突后找不到墓碑则是保留完整性告警并暂停自动首次受理。已受理 `inbox` 数量或最老年龄持续增长表示异步处理积压；外部结果停留未知表示需要业务对账。发送端的事件年龄、自动尝试次数、需处理量和将到期量则帮助在 30 天期限前处理积压。事件能从稳定 `eventId` 追到每次尝试、接收端受理和最终业务状态，但不要把“发出过请求”“收到 202”和“副作用已完成”混成一个成功指标。

> [!info]- 来源
> - HMAC 的定义、共享密钥模型与安全说明：[IETF RFC 2104](https://www.rfc-editor.org/rfc/rfc2104.html)，§1–§3，1997-02；`HMAC-SHA-256` 标识与测试向量：[IETF RFC 4231](https://www.rfc-editor.org/rfc/rfc4231.html)，§2–§4，2005-12。示例签名在 2026-11-12 以 Python 标准库 hmac/hashlib 按文中字节定义复算。
> - JSON 对象成员名与互操作性：[IETF RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html)，§4，2017-12。规范指出对象成员名应唯一；本地合约进一步选择拒绝重复名称，避免接收端与 worker 对同一签名正文解释出不同业务对象。
> - HTTP 字段重复与合并、内容编码、401 challenge、状态码、`Retry-After` 与认证方案注册：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§5.2–§5.3、§8.4、§11.1–§11.6、§15.3.3、§15.5、§15.6.4、§16.4.1，2022-06。核实范围是本页涉及的 HTTP 语义，不把私有 HMAC 协议归为 RFC 定义。
> - 缓存的 `no-store` 响应指令：[IETF RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.5)，§5.2.2.5，2022-06；429 与 `Retry-After` 建议：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，§4，2012-04；问题详情类型及错误信息的安全边界：[IETF RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html)，§3、§5，2023-07。
> - 并发 `inbox` 冲突与新鲜查询：[PostgreSQL 18 Documentation](https://www.postgresql.org/docs/18/sql-insert.html)，`INSERT` ... `ON CONFLICT` ... `RETURNING`；[PostgreSQL 18 Documentation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1 `READ COMMITTED` 每条命令使用新快照。[PostgreSQL 18 Client Connection Defaults](https://www.postgresql.org/docs/18/runtime-config-client.html)，核实 `statement_timeout` 对单条语句计时、`lock_timeout` 对每次锁等待计时，而 `transaction_timeout` 限制普通事务的时长且不覆盖 prepared transaction；[PostgreSQL 17 配置文档](https://www.postgresql.org/docs/17/runtime-config-client.html) 已列出该参数，[PostgreSQL 16 配置文档](https://www.postgresql.org/docs/16/runtime-config-client.html) 尚无此参数，故较旧运行版本需另配等效服务端事务上限。另在隔离环境使用 PostgreSQL 14.24 实际复放冲突模式；没有将实验提升成所有数据库的保证。
> - 数据库提交与客户端观察的边界：[PostgreSQL 18 libpq asynchronous command processing](https://www.postgresql.org/docs/18/libpq-async.html)，§32.4，说明发送命令与取回命令结果是分开的客户端步骤。复放本文 SQL 时另以本地独立连接验证了提交结果未被应用读取但行已可见的情形。
> - 2026-11-12 核对版本：IETF RFC 2104、4231、6585、8259、9110、9457 当前有效规范文本；PostgreSQL 官方文档当前稳定主版本为 18，19 为开发版。SQL 示例依赖的 `ON CONFLICT` / `RETURNING` 能力也在本地 PostgreSQL 14.24 实际复放。
## 18. 怎样用 Kafka 分区保序、推进偏移并安全接手？

**合成案例：** 报表服务为 `reportId=42` 按业务序号发布 `queued`、`rendered`、`ready` 三条记录。在线消费者把它们应用到数据库 projection (投影)；值班时，同一报表投影还要重建到一张新表。两个 consumer group (消费者组) 各自维护读取位置。本页沿这三条记录说明 Kafka 保证什么顺序、消费者怎样记录进度，以及进程失联或组成员变化后为何会重放。案例中的 offset (偏移量) 是讲解用位置，不是线上测量值。

先看端到端边界：生产者用稳定的键把同一报表送往同一个分区；分区只给出 broker (代理节点) 实际追加的顺序；每个传统 consumer group (消费者组) 独立读取并保存位置；外部数据库写入是否完成，要由数据库自己的事务和业务序号判断。Kafka 的 offset 不能替数据库确认业务效果。

![同一分区由在线组与重建组各自读取](../../engineering-foundations/reliability/resources/partition-groups.svg)

图中的 `G-live` 和 `G-rebuild` 是两个组，所以它们各有一份进度；两组都独立读取同一分区的全部可见记录。同一个传统组内，一个分区在某一时刻只交给一位成员。组收到的记录顺序仍不代表并行数据库写入完成顺序。

### 哪个顺序由分区保证？

Kafka 的 topic (主题) 由多个 partition (分区) 组成；每个分区是一条按追加位置排列的日志，分区 leader (主副本) 决定该分区的追加顺序。分区内的 offset (偏移量) 标识位置，不同分区之间没有天然的全局次序。Kafka 4.4 Java producer (生产者) 在默认 `BuiltInPartitioner` (内置分区器) 下，会用记录 key (键) 序列化后的字节计算语义分区：同一个 `report-42` 键在分区数量、序列化和分区策略都稳定时会被路由到同一分区。下面的具体计算固定 UTF-8 key serializer (键序列化器)、未覆盖 `partitioner.class`、未显式指定 partition (分区)，且 `partitioner.ignore.keys=false`；后者是默认值。自定义 partitioner (分区器)、不同字节编码或忽略 key 都可以改变映射。

本例固定三个分区、一个生产者按业务序号串行发送，使用 Kafka 4.4 默认的 `enable.idempotence=true` 且不覆盖其约束。报表 42 的三条载荷记录带有 `reportId=42`、`seq` 和稳定 `event_id`；表末的 `report-17` 只是另一条路由计算，不属于报表 42：

| 分区与 offset | key | 业务序号 | 记录 |
| --- | --- | ---: | --- |
| `report-events / P0 / 40` | `report-42` | 1 | `queued` |
| `report-events / P0 / 41` | `report-42` | 2 | `rendered` |
| `report-events / P0 / 42` | `report-42` | 3 | `ready` |
| `report-events / P2 / 18` | `report-17` | 1 | `queued` |
| `report-events / P2 / 19` | `report-17` | 2 | `ready` |

对给定 UTF-8 字节，Kafka 4.4 Java 内置路由先算 `toPositive(murmur2(keyBytes)) % partitionCount`：`report-42` 的正值 hash (散列值) 为 `1051128390`，模 3 得 `P0`；`report-17` 的正值为 `417961679`，模 3 得 `P2`。这是按 Kafka 4.4.0 的 `Utils.murmur2` 和 `BuiltInPartitioner.partitionForKey` 复算出的路由，不是 broker 现场日志。offset `40–42` 是示意位置；业务序号 `1–3` 才是报表状态的因果顺序。Kafka 会按 `P0` 日志次序交付可见记录，但不会替业务判断哪个事件应该先发生。若多个生产者并发发布同一个键，broker 仍会形成一个追加顺序，却不保证它就是业务所需的序号顺序；应让上游定义序号，并在应用侧检查缺口或拒绝旧序号。

同一传统 consumer group 中，分区由组内一位活跃成员负责。三个分区最多提供三份这种分区级并行度；组内增加第四个消费者不会分出第四个分区。另一个 `G-rebuild` 组可以从自己的位置读取相同日志，不会移动 `G-live` 的 offset。Kafka 4.4 另有 share group (共享组)这种逐记录协作模型，它允许多个成员处理同一分区；本页讨论的是用于分区有序处理的传统 consumer group，不把两种模型混用。

扩分区也会改变顺序边界：默认的 key→partition 映射受分区数影响。保持上述 producer、serializer 和分区器不变，把分区数从 3 增到 4，`report-42` 的同一个 hash 从 `1051128390 % 3 = 0` 变为 `1051128390 % 4 = 2`，也就是从 `P0` 移到 `P2`；`report-17` 则从 `P2` 移到 `P3`。新分区 offset 与旧分区 offset 不能比较，因此不能靠它们推导 `report-42` 的跨分区顺序。若必须在变更分区数时保序，应安排可验证的迁移边界：暂停该键的新发送、等待旧分区已发布记录处理到约定序号，再切换路由；消费者仍校验 `seq` 并在缺口时等待或修复。仅更换一个自定义分区器不会为两条分区日志建立全局顺序。

#### 生产者的确认与重试各证明什么？

`acks` 是 Kafka producer (生产者) acknowledgment (确认) 的配置，决定生产者等到什么复制边界才把发送视为成功；它不证明消费者已处理，也不证明数据库里已有报表结果。

| 配置 | 成功响应边界 | 仍需考虑的条件 |
| --- | --- | --- |
| `acks=0` | 不等待 broker 响应 | 可能连 broker 是否收到都不知道，重试也无法据此判断失败 |
| `acks=1` | 分区 leader 将记录写入自己的日志 | leader 在复制给 follower (从副本) 前故障时，记录可能丢失 |
| `acks=all` | 当前 in-sync replicas (同步副本集，ISR) 确认 | 等待当前 ISR，不等 `replication.factor` 中的所有副本；若唯一持有已确认数据的副本永久丢失，确认本身不能恢复那份数据 |

这张表只说明生产者等到的确认边界。Kafka 4.4 新集群默认启用 eligible leader replicas (合格主副本，ELR)：当 ISR 小于 `min.insync.replicas` 时，高水位不会前进，leader 选举资格也会考虑 ELR。因此，不能只看 `acks=all` 推断副本丢失后的接管结果；还要核对 `replication.factor`、`min.insync.replicas`、ELR 是否启用，以及持有已提交记录的副本是否仍存活。

若生产者超时，它可能不知道请求是在追加前还是追加后失去响应。Kafka 的 producer idempotence (生产者幂等性)用生产者身份和分区序号去重同一次生产者重试；Kafka 4.4 默认开启幂等性，前提是没有冲突配置，幂等配置要求 `acks=all`、启用重试且 `max.in.flight.requests.per.connection <= 5`。若关闭幂等性、启用重试且同一连接允许多个未确认请求，早先批次重试期间，后发批次可能先写入。即使幂等生产者工作正常，它也不判断两个由应用重新发起的 `send` 是否代表同一个业务事件；应用级重放仍需用 `event_id` 或同等业务键去重。

### 提交的 offset 为什么是“下一个要读的位置”？

Kafka consumer (消费者) 有两个容易混淆的位置。`position` (当前位置) 是当前消费者下一步要取的位置；每次 `poll()` 交付记录后会前进。committed offset (已提交偏移量) 是持久保存、进程重启或重新分配后要恢复到的位置。`poll()` 已把记录交给应用，不代表数据库处理完成；也不能把本地 `position` 自动当成可安全提交的业务进度。

对 `P0` 而言，成功处理 offset `40` 后，提交 `41` 表示下次从 offset `41` 起继续；Kafka Java consumer API 要求提交的是下一条要处理记录的 offset。若已经交付 `40、41、42`，consumer 的当前位置可以是 `43`，但异步 worker (工作线程) 还没完成 offset `40` 时，安全的持久进度仍是 `40`：它是最早未完成的可见记录位置，否则崩溃恢复会跳过它。

![当前位置可领先于最早未完成记录，提交位置只越过连续完成前缀](../../engineering-foundations/reliability/resources/offset-prefix.svg)

同一分区若派给并行 worker，就按**已交付记录的顺序**维护连续完成前缀：假设 `41`、`42` 完成而 `40` 仍运行，可提交位置保持 `40`；等 `40` 也完成后，才推进到 `43`。若 `40` 已完成、`41` 还在运行而 `42` 已完成，安全位置是最早未完成记录 `41` 的 offset。worker 只把完成结果交还 consumer 线程；`KafkaConsumer` 本身非线程安全，由同一个 consumer 线程拥有 poll、分区分配、前缀状态和提交。可以串行处理分区，也可以并行计算，但只能让提交器提交最早未完成记录的 offset；一个分区所有已交付记录均完成时，再提交最后一条可见记录之后的 next offset。

例如，offset `40` 的数据库事务提交成功后、且 consumer 仍有效拥有 `P0` 时，只提交这一分区的安全位置：

```java
consumer.commitSync(Map.of(
    new TopicPartition("report-events", 0),
    new OffsetAndMetadata(41L)
));
```

如果在一次 `poll()` 已交付 `40、41、42` 后调用无参 `commitSync()`，它提交的是最近一次 poll 的位置，可能是 `43`；当 worker 的 `40` 尚未完成时，这会让恢复跳过尚无数据库效果的记录。用显式 map 只提交连续完成前缀；失去分区后，应用不能把旧完成通知带入新分配的前缀。

offset 整数不一定连续。日志压缩会移除同键的旧记录；`read_committed` 隔离级别会隐藏已中止事务的记录。因此，假设应用实际收到 `40` 和 `42`，而 `41` 在日志中不可见，完成 `40` 后，下一条要处理的可见记录是 `42`，不必等待不存在的 `41`；提交 `41` 也只是一个更早的扫描起点，会在读取时越过空洞。不能因为看见 offset 数字有缺口就认为一条业务记录丢失，也不能在 `42` 尚未完成时把进度提交到它后面。`read_committed` 还会等未完成事务的边界（last stable offset (最后稳定偏移)），所以消费者可能暂时看不到日志尾部的后续记录。

连续完成前缀限制的是恢复位置，不会自动让外部副作用按业务序号发生。若 worker 先写 `seq=2 rendered`、再写 `seq=1 queued`，数据库状态仍可能倒退。相同 `event_id` 的去重只能阻止同一事件重复产生效果，不能修正不同事件的乱序。

如果投影存的是“可由最新完整快照替换”的状态，而非每一步都要执行的转换，可以用业务序号拒绝旧快照。本例先创建 `report_id=42, last_seq=0`（非 NULL）的一行，并让每条记录都携带完整状态：

```sql
UPDATE report_projection
SET status = :status, last_seq = :seq
WHERE report_id = :report_id AND last_seq < :seq;
```

先应用 `seq=2 rendered`、再应用 `seq=3 ready` 后，迟到的 `seq=1 queued` 影响零行，投影保留 `ready/3`；这条旧快照被较新快照替代，因此是成功的无操作，之后 offset `40` 才算完成并允许连续前缀前进。此写法**只适用于可跳过中间状态的完整快照**。若 `queued → rendered → ready` 每一步都有不可省略的副作用，就应按 `reportId` 顺序提交，或要求 `seq = last_seq + 1` 并把缺口留待补齐，不能用 `last_seq < seq` 假装所有转换都执行过了。

### 崩溃发生在处理与提交的哪一边？

假设 `G-live` 当前应从 offset `40` 处理 `queued`，效果写入 PostgreSQL，消费位置保存在 Kafka。两个系统之间没有普通的单次原子提交：

| 崩溃/确认边界 | 数据库中的状态 | 恢复起点 | 结果 |
| --- | --- | --- | --- |
| 数据库事务提交后、Kafka offset 尚未提交 | `event_id` 对应效果已持久 | 仍从 `40` 起 | offset `40` 会重放；数据库须在同一本地事务中用 inbox (收件箱)/唯一 `event_id` 去重，或让完整快照条件更新成为无操作 |
| Kafka 已提交 `41`、数据库事务还未提交 | 事件 `40` 效果不存在 | 从 `41` 起 | Kafka 不会再交付 `40`，投影漏掉这次更新 |

所以写外部数据库的一般消费者会先让数据库事务提交，再提交 Kafka offset，接受至少一次处理和可能重放。外部处理要关闭自动 offset 提交（`enable.auto.commit=false`），否则后台自动提交可能先于数据库事务。如果数据库提交成功但响应丢失，重新查询数据库的 inbox/投影并安全重放；不要把 Kafka offset 的提交响应当成数据库提交证明。不能靠交换两条语句的先后消除“两边都恰好成功一次”的窗口。

反过来，producer 的发送确认也可能在记录追加后丢失。幂等性让同一个 producer 的协议重试不再追加重复副本；如果应用收到不确定结果后作为一次新业务调用重新发布，仍需要业务 `event_id` 去重或查询已发布状态。这样，生产端消除的是限定范围的重试重复，消费端仍要自己对付数据库与 offset 的崩溃窗口。

### 再均衡怎样拒绝旧成员的提交？

组成员加入、退出、poll 超过允许间隔等情况会触发 rebalance (再均衡)，改变分区分配。先看一个明确使用 classic group protocol (经典组协议)和 eager assignor (整体撤销式分配器)的时序：C1 持有 `P0`，已提交位置是 `40`；C2 加入，组从代次 5 进入代次 6，把 `P0` 交给 C2。

| C1 的提交时机 | offset 提交结果 | C2 起点 |
| --- | --- | --- |
| C1 停止派发、等 offset `40` 的数据库事务确认成功，并在代次 5 仍有效时提交 `41` | 持久位置变为 `41` | 从 `41` 起 |
| 携带旧代次 5 的请求在代次 6 生效后抵达 | coordinator (协调器)拒绝；仍被识别的成员使用旧代次时为 `ILLEGAL_GENERATION`，成员已移出时先报 `UNKNOWN_MEMBER_ID`；持久位置仍为 `40` | 从 `40` 重放 |

这次拒绝的根据是 C1 交来的成员/代次已过期；不能写成“只要 P0 改给 C2，broker 就一定拒绝 C1”。Kafka 4.4 classic coordinator 验证 group/member/generation 状态，再对每个 partition offset 不做额外的分配归属校验。应用仍应只提交当前分配中已完成的前缀；这条服务端验证不是外部数据库写入的 fencing。

正常的 `onPartitionsRevoked` 回调发生在有序交接时：consumer 线程停止派发，可以在有界时间内等待正在执行的数据库事务确认成功，再在旧成员资格仍有效时提交已完成的连续前缀。异常情况下可能直接收到 `onPartitionsLost`：此时分区可能已由别的成员拥有，C1 不再尝试提交旧进度，而是停止派发、丢弃旧分配的完成通知；C2 从最后一次成功保存的位置恢复，未提交的数据库效果可能重放。回调不会撤销已经运行的后台任务，因此外部存储仍须防止旧任务迟到写入。

Kafka 4.4 的 `group.protocol=classic` 是 Java consumer 默认值。新 consumer rebalance protocol (消费者再均衡协议，KIP-848)从 Kafka 4.0 起已正式可用，但需设置 `group.protocol=consumer` 选择；它按分区增量调整成员，不应照搬 classic 的整组撤销时序。classic 下的 generation (组代次) 和新协议下的 member epoch (成员代次) 都参与组提交的成员校验，但协议差异会影响分配与配置方式，具体回调时机应按所选协议核实。排空工作也必须受该协议的成员存活与 poll 时限约束；若等待数据库时超过时限，旧成员可能先失去分区，提交就会失败并留下重放。

Kafka 的 group fencing (组成员栅栏)只保护 consumer group 的分配和 offset 提交。若 C1 已将异步工作派给后台线程，组撤销不会自动停止那个线程，也不会撤销它已经写入数据库的事务。应用须在撤销时停止派发并等待或取消仍未完成的工作；若旧任务可能迟到，就让目标数据库也执行持久所有权栅栏。下面是简化的 PostgreSQL 合同：每个 topic/partition 有一条唯一 owner row (所有权行)；C2 以当前 token (令牌)作条件更新并提交，再开始新所有者的业务写入；C1 的每个副作用事务先锁同一所有权行、验证 token，再写投影，锁保持到同一事务提交。 这里的 owner 表专属于 `G-live` 的在线投影；同时运行的 `G-rebuild` 应使用独立的 owner 表，或把 `projection_id` 加入唯一键及每条所有权读写条件，否则两个合法消费者组会互相撤销所有权。

```sql
-- C2：新所有者 token=6 先落库。业务写入只能在这个事务提交后开始。
BEGIN;
UPDATE partition_owners
SET owner_token = 6
WHERE topic = 'report-events' AND partition_id = 0 AND owner_token = 5;
-- 必须恰好更新一行；否则此 worker 没有取得新的持久所有权。
COMMIT;

-- C1：owner 检查和投影效果在同一事务中；FOR UPDATE 的锁保持到 COMMIT。
BEGIN;
SELECT owner_token
FROM partition_owners
WHERE topic = 'report-events' AND partition_id = 0
FOR UPDATE;
-- 应用只在查到 owner_token=5 时继续；否则 ROLLBACK 并丢弃旧任务。
UPDATE report_projection
SET status = :status, last_seq = :seq
WHERE report_id = 42 AND last_seq < :seq;
COMMIT;
```

两个所有权代次和投影写入都必须遵守同一 owner row。若 C1 先取得行锁，C2 的 token 更新要等 C1 提交后才能生效；若 C2 已提交 token 6，之后 C1 锁行会看到 6 并拒绝写入。普通 `SELECT` 读 token 再稍后 `UPDATE`，即使两句放在 Read Committed 同一事务，也没有这项互斥。业务 `seq` 仍能拒绝旧快照，却不能单独证明当前写入者有权；数据库 fencing 与报表 job 自己的 attempt (运行尝试)/lease (租约)是两个独立合同。仅捕获 `CommitFailedException` 不能撤回已提交的 SQL。

### 回放能重建到哪里？

在线投影用 `G-live` 持续消费；同一报表投影的重建表应由独立 `G-rebuild` 读取。把数据库初始快照与它对应的每分区位置向量 `S[p]` 一起保存：快照包含每个分区所有 offset `< S[p]` 的效果，且不包含任何 `>= S[p]` 的效果；重建组从 `S` 开始。`S` 是快照的恢复起点，之后选择的 `T` 是在线与重建投影共同对齐的切换边界，二者不是同一个位置。若重置 `G-live` 的 offset，改变的是在线投影自身的恢复点，不是复制出第二份进度。

以 `P0` 为例：数据库快照已经包含 offset `<40` 的投影效果，而且没有任何 `>=40` 的效果，因此 `S[P0]=40`。在线投影和新表都处理当前仍可见且保留的 `40、41、42`；选 `T[P0]=43` 后，两边都暂停应用 `>=43` 的事件，并确认各自的安全数据库效果前缀和 committed offset 都停在 `43`。此刻每张表都应恰好等于“快照 + `[40,43)` 中可见记录的效果”，且没有 `[43,…)` 的效果。确认两边状态相同后，切到新表，由 `G-rebuild` 从恢复位置 `43` 继续。这里的 `[40,43)` 是一个分区内半开 offset 区间；多分区时每个分区分别有自己的 `S[p]` 和 `T[p]`，不能把它们合成全局时间。

在线表与重建表如果都用 inbox 去重，应让去重键至少包含 `(projection_id, event_id)`，或给每张投影单独 inbox。若 inbox 只以 `event_id` 全局唯一，在线组处理过 `event_id` 后，重建组会误以为新表也已处理，跳过重建事件。还要保证每个分区的 `[S[p],T[p])` 仍完整可读，并在切换期间保留 `>=T[p]` 的事件；compact/retention 已删掉所需记录时，停止切换并恢复与快照匹配的历史来源，不能靠 `auto.offset.reset=earliest` 静默补齐。offset 中可能有压缩或事务导致的不可见空洞，例子中的 40、41、42 是该合成分区内的可见记录；对齐条件针对全部可见且已应用的记录，不要求整数连续。

重建能力还受 retention (保留)和 compaction (压缩)策略限制。offset 已超出当前最早可读范围时，`auto.offset.reset=earliest` 只能从**现在仍保留的最早记录**开始，不能找回已删除记录。日志压缩保留每个 key 的较新值，不承诺保留同一 key 的所有历史状态转换；若要从空白重建完整事件历史，主题必须按重建时间和最慢速度留足未压缩记录，或提供匹配 offset 向量的快照。

Kafka 的 transaction (事务)能把输入分区的消费位置与 Kafka 输出 topic 的记录一起提交。典型 Kafka→Kafka 流程让每个并发 producer instance 使用唯一、重启后可复用的 `transactional.id`；新实例先调用 `initTransactions()`：旧实例失败时仍在进行的事务会被中止；若旧事务已经开始提交或中止，则等待该过程结束，同时通过新的 producer epoch 拒绝旧实例。对任何包含事务记录、且只应处理成功提交记录的输入 topic，消费者都应设置 `isolation.level=read_committed`，不把已中止的记录当成业务输入。处理时关闭自动 offset 提交，通过 producer 的 `sendOffsetsToTransaction(offsets, consumer.groupMetadata())` 把下一读取位置及当前 consumer group metadata (消费者组元数据)加入当前事务，不再另行手动提交这些 offset。正确配置并处理提交与中止时，Kafka 输出与输入消费位置一起提交或一起中止；这不是“单次 poll 原子返回所有分区输出”的保证。中止后组提交位置仍是旧值，输入可以重处理；消费者内存中的 `position` 不会自动倒回，应用要重新读取已提交位置，例如调用 `seek`、重启 consumer 或等组接手。

但 transaction 不会把 PostgreSQL `UPDATE`、对象存储写入或 HTTP 调用拉入 Kafka 事务。若 `ready` 已写入 PostgreSQL、随后 Kafka transaction 中止，数据库副作用不会跟着回滚。Kafka 到外部系统仍需该系统合作：数据库可在同一事务写业务结果、inbox 和数据库自己的消费位置，并在恢复时从这个持久位置 `seek`；或先提交数据库效果，再提交 Kafka offset，并让业务写入对重放幂等。数据库 outbox (发件箱)负责可靠发布已经提交的数据库变更，但它本身不会推进 Kafka consumer 的读取位置。远端 API 则须以稳定操作键对重复请求提供业务幂等性。相关报表任务合同见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)，消息确认与未知结果见[报表任务的发布确认、消费者确认与业务完成各证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源与版本边界
> 核对日期：2026-11-13。Apache Kafka 官方 Downloads 将 4.4.0 列为受支持版本，发布公告日期为 2026-10-22；下列 Kafka 4.4 文档用于核对当前术语与配置，案例中的事件、offset、分区数、崩溃点和完成顺序均为合成推演。
>
> - [Apache Kafka Downloads](https://kafka.apache.org/downloads/) 与 [4.4.0 发布公告](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/)：支持版本列表与发布日。
> - [Apache Kafka 4.4 Design](https://kafka.apache.org/44/design/design/) 与 [Eligible Leader Replicas](https://kafka.apache.org/44/operations/eligible-leader-replicas/)：key 到分区的语义路由、分区内全序、传统消费者组成员与位置、producer 可靠性、Kafka 事务及外部系统边界、share group 与传统 group 的区别、复制和 ELR/min ISR 边界。
> - [Apache Kafka 4.4 Producer Configs](https://kafka.apache.org/44/configuration/producer-configs/) 与 [KafkaProducer 4.4 Javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html)：`acks`、默认幂等性、重试排序、`transactional.id` 和 `sendOffsetsToTransaction`。
> - [KafkaConsumer 4.4 Javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html)：consumer position 与 committed position、offset 可有空洞、提交的 next offset、提交失权时的失败，以及传统组撤销/分配回调。
> - [Apache Kafka 4.4 Consumer Configs](https://kafka.apache.org/44/configuration/consumer-configs/) 与 [Consumer Rebalance Protocol](https://kafka.apache.org/44/operations/consumer-rebalance-protocol/)：`enable.auto.commit`、`read_committed`、`auto.offset.reset`、`max.poll.interval.ms`，及 `classic` / `consumer` 协议的选择边界。Kafka 4.4 的 Java consumer 默认 `classic`；新协议从 4.0 起 GA，但仍需显式选择。
> - [Kafka 4.4 Protocol](https://kafka.apache.org/44/design/protocol/) 和 [Topic Configs](https://kafka.apache.org/44/configuration/topic-configs/)：offset 提交的 generation/member epoch 字段，主题保留与压缩配置。本文关于扩分区引起的跨分区排序缺口，是 key 哈希路由与多分区独立日志的推论；迁移步骤是应用侧合同，不是 Kafka 自动提供的排序。
> - [Kafka 4.4.0 `BuiltInPartitioner`](https://github.com/apache/kafka/blob/4.4.0/clients/src/main/java/org/apache/kafka/clients/producer/internals/BuiltInPartitioner.java)、[`Utils.murmur2`](https://github.com/apache/kafka/blob/4.4.0/clients/src/main/java/org/apache/kafka/common/utils/Utils.java) 与 [`UtilsTest`](https://github.com/apache/kafka/blob/4.4.0/clients/src/test/java/org/apache/kafka/common/utils/UtilsTest.java)：用于限定上述 UTF-8 hash 与分区数计算；不是所有客户端都必须采用相同语言实现。
> - [Kafka 4.4.0 `ClassicGroup.validateOffsetCommit`](https://github.com/apache/kafka/blob/4.4.0/group-coordinator/src/main/java/org/apache/kafka/coordinator/group/classic/ClassicGroup.java#L798-L874)、[PostgreSQL 18 Read Committed](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-READ-COMMITTED) 与 [Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html)：classic commit 检查组状态/成员/代次，Read Committed 下的语句快照以及行锁直到事务结束并在等待后返回更新行的依据。数据库 owner row 的互斥写入流程是应用合同；本文所述隔离与锁语义依据 PostgreSQL 18 文档。
## 19. 何时选择轮询、SSE、流式 Fetch 或 WebSocket？

**案例：** 报表查看者已请求刷新报表 42，并获准读取它。前一篇[说明浏览器怎样验证缓存中的 v8 表示并取得 HTTP 响应](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F)；本例是在后续一次权威读取中得到新的 `version=9`、`status=running` 和事件日志游标 `103`。本章比较 short polling (短轮询)、long polling (长轮询)、Server-sent Events (SSE，服务器发送事件) 与浏览器 EventSource 接口、Fetch API (网页请求接口) 响应流，以及 WebSocket 双向消息通道。查看者最终需要判断是重新读取当前状态，还是必须处理每一次状态变化；“重新连上”本身不会补回应用漏掉的工作。

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

### 先按方向、请求形状和恢复目标选通道

| 方式 | 请求与消息方向 | 恢复由谁负责 | 合适的条件与成本 |
| --- | --- | --- | --- |
| 短轮询 | 客户端按间隔发普通 HTTP 请求，取得当前状态或自上次游标以来的变化 | 客户端控制间隔、退避、抖动和停止；接口定义版本或游标 | 更新不密、简单性重要。间隔越短，发现变化越快，但空响应和请求数越多 |
| 长轮询 | 服务端暂留一次请求，等到有变化或期限到，再返回；客户端随后带新游标发下一次请求 | 客户端重新请求；服务端为等待中的请求设上限，双方仍处理代理超时和断线 | 需要普通 HTTP 请求形状又想减少空轮询。每个挂起请求仍占服务端状态、HTTP 流及相关资源；过期后应带游标续问 |
| Server-sent Events (SSE，服务器发送事件) + `EventSource` | 浏览器用 `GET` 建立 `text/event-stream` 响应，主要从服务端收事件 | 原生接口通常重连并带 `Last-Event-ID`；服务端还须保存事件并按有效游标重放 | 服务端单向推送，原生事件格式和重连合用。构造器不能设置自定义字段、请求方法或正文 |
| 流式 Fetch (Fetch response stream，Fetch 响应流) | 一次请求按 API 契约使用方法、字段和正文；响应体可逐块读取 | 应用实现解析、恢复游标、重试、退避、取消和授权 | 需要 `Authorization` 字段、POST 查询或自定义线格式。读到的字节块不是事件边界 |
| WebSocket 双向消息通道 | 握手后，客户端和服务端都可主动发送消息 | 应用定义重连、身份更新、确认、序号和重放 | 需要在长连接上持续双向低延迟交互。浏览器原生 API 不替应用恢复消息，也没有接收侧背压 (backpressure，消费较慢时令上游减速) 接口 |

若更新不密但又要求尽快到达，长轮询和推送都可减少等待：长轮询在事件出现或请求期限到时结束本次请求，客户端马上带新游标再问；它仍要承担挂起请求、代理超时和重新建连成本。SSE 或 Fetch 推送保持一个响应打开，减少反复请求，却要检查代理缓冲、空闲超时和长连接容量。选择取决于目标延迟、服务器资源和部署链路，不存在只凭“实时”二字就必然胜出的方式。短轮询可带版本或条件字段来少传正文，但仍会发请求；Entity Tag (ETag，实体标签) 与 `304` 的边界见[HTTP 请求与缓存笔记](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F)。

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

一万名客户端若各自每 0.5 秒轮询一次，粗略请求率为 `10,000 ÷ 0.5 = 20,000` 次/秒；这是请求数估算，不等于同样数量的数据库查询或固定 CPU 开销，也未计入重试和同步突发。加随机抖动可以摊平同时请求；更新少时可延长间隔，服务端报错时按退避重试，任务结束或页面不再需要更新时停止。容量与准入见[Web 服务如何限制拒绝服务的影响？](#29.%20Web%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%8B%92%E7%BB%9D%E6%9C%8D%E5%8A%A1%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F)。

### 断线后，客户端要重建状态还是补齐每条事件？

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

### SSE 如何从快照游标续读事件？

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

![从一致快照游标开始订阅，并沿同一日志从历史回放衔接到实时尾读](../../engineering-foundations/networking/resources/sse-snapshot-to-events.svg)

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

![浏览器解析游标与逐事件确认的恢复分支：ACK=103 重放104，ACK=104 续读105](../../engineering-foundations/networking/resources/sse-parse-vs-ack.svg)

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

### 流式 Fetch 如何从任意字节块组装有限结果？

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

### WebSocket 怎样维持双向消息并限制慢客户端？

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

### 把通道结果接回报表权威状态

重新连上 SSE、重新发 Fetch，或重建 WebSocket，都只恢复传输。报表任务的权威状态仍由状态接口或持久化任务记录负责；若最终结果未知，客户端应重新查询报表/作业资源。只有状态本身满足重建条件时才丢弃中间通知；若每条变化都重要，要让服务端日志保留期覆盖断线窗口，并为每次订阅确定授权范围、游标格式、顺序、确认和过期后的重置流程。不要把客户端提供的游标当成授权信息。

本例 SSE 的 `reset` 处理是“取新快照并从其游标继续”；有限 Fetch 则以 `result.complete` 加完整 EOF 确认单次搜索结束；WebSocket 遇到可恢复的普通关闭时，在持久游标仍可回放的前提下退避重连并重订阅，已知 `cursor.expired` 则停止重连、进入对账，不能用快照跳过缺口。若客户端需要接回已受理的异步任务而不是只更新页面状态，先查稳定状态资源，见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)；长期任务状态持久化也见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)和[AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复？](../../ai-engineering/systems/ai-application-architecture.md)。

> [!info]- 来源
> - SSE 字段语法、多行与空负载 `data`、单个前置 BOM、空行分发、EOF 丢弃、EventSource 认证选项、`Last-Event-ID`、`retry`、`204` 停止重连和非 `200` /错误媒体类型处理：[WHATWG HTML Living Standard, Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)，§9.2，最后更新 2026-11-11，核对于 2026-11-12。
> - Fetch 请求/响应体、CORS：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，Living Standard，最后更新 2026-10-19；增量解码与 `TextDecoder` 的 BOM 选项：[WHATWG Encoding Standard](https://encoding.spec.whatwg.org/)，Living Standard，最后更新 2026-10-19，§7.1–§7.2；可读流取消、队列和背压：[WHATWG Streams Standard](https://streams.spec.whatwg.org/)，Living Standard，最后更新 2026-10-25，§4.2.4；均核对于 2026-11-12。
> - 轮询、长轮询、挂起请求、流式传输的中间代理行为与超时：[IETF RFC 6202, Known Issues and Best Practices for the Use of Long Polling and Streaming in Bidirectional HTTP](https://www.rfc-editor.org/rfc/rfc6202.html)，§2.1–§2.2、§3.2、§5.5，2011-04；该文为 Informational RFC，核对于 2026-11-12。
> - 反向代理是否缓冲上游响应及默认配置：[NGINX `ngx_http_proxy_module`, `proxy_buffering`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering)；gzip 响应过滤器与压缩缓冲：[NGINX `ngx_http_gzip_module`, `gzip_buffers`](https://nginx.org/en/docs/http/ngx_http_gzip_module.html#gzip_buffers)，当前官方文档均核对于 2026-11-12。
> - 浏览器 WebSocket 构造器、凭据模式、消息与发送队列：[WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/)，Living Standard，最后更新 2026-10-19，核对于 2026-11-12；接收侧无背压：[MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)，核对于 2026-11-12。
> - WebSocket 握手、帧/消息顺序与 `Origin` 安全：[RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)，§4–§5、§10.2，2011-12；HTTP/2 Extended CONNECT：[RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)，§3–§4，2018-09；HTTP/3 Extended CONNECT：[RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)，§3，2022-06；均核对于 2026-11-12。
> - Node.js `ws` 的服务端广播、`bufferedAmount`、`pause()` / `resume()` 和 `send` 回调：[ws 官方 API 文档](https://github.com/websockets/ws/blob/master/doc/ws.md)，当前仓库文档核对于 2026-11-12。此实现文档不是 WebSocket 协议规范；代码展示机制，不包含生产认证、订阅授权或完整连接恢复。
> - 按订阅持久保存连续 ACK、用日志高水位衔接回放与尾读，以及游标过期后的审计对账，都是本例定义的应用协议；HTML SSE 和 WebSocket 标准不替应用提供这些业务交付保证。
## 20. 何时选线程、进程或异步 I/O？

**合成案例：** 报表服务接到 acct-17 的导出任务，需要读数据库、格式化几万行并写出压缩文件。读库和写文件可能在等 I/O，格式化与压缩也可能持续占用 CPU。这个作业会经过不同阶段，因此可以在 I/O 阶段按支持情况使用 async I/O（异步 I/O），或用有界阻塞池隔离同步调用；较长的 CPU 计算再交给合适的执行资源。选择前要看每阶段在等什么、要共享什么，以及停止时谁负责清理资源。

### 进程、线程和异步 I/O 各自拥有哪种边界？

在常见操作系统模型中，process（进程）是资源与保护边界，通常有自己的虚拟地址空间；thread（线程）是进程里的执行路径。同一进程的线程共享地址空间中的堆、全局数据和许多句柄，但每个线程仍有自己的寄存器状态和栈。进程间通常用管道、套接字、消息或显式映射的共享内存通信。进程可通过显式配置共享部分资源，因此“进程绝不共享”也不准确。

| 选择 | 报表服务里的合适工作 | 付出的责任 |
| --- | --- | --- |
| async I/O（异步 I/O） | 当前运行时为数据库、网络或文件操作提供适用的异步 API | 在事件循环运行时，任务等待结果期间事件循环线程仍可处理其他任务；在途操作仍占连接、缓冲区等资源，必须限制并发 |
| 工作线程 / 有界线程池 | 运行时支持并行的 CPU 密集型转换；或把同步阻塞调用移入池，释放请求线程 | 通用 OS 线程共享进程地址空间，共享可变状态需同步；阻塞调用会占一个 worker，线程数与队列都要有界 |
| 独立进程 | 需要独立生命周期、故障或地址空间边界的计算 | 消息/序列化、独立内存和启动成本；必须管理退出。子进程可能继承父进程的 OS 身份和打开句柄；独立地址空间本身不会限制文件、网络等访问。运行不可信代码时，要由操作系统策略缩减其可访问的权限与资源 |

concurrency（并发）指多个任务能在重叠的时间段内推进；在单个处理单元上，调度器常靠交替运行它们实现并发。parallelism（并行）指多个处理单元同一时刻执行指令。单线程事件循环可以在一个请求等待 I/O 时处理另一个请求；一个很长的同步回调仍会堵住这条线程。CPU 计算能否并行，还取决于语言运行时、数据交换和负载大小。Node 的运行时选择见[Node.js 如何在事件循环、工作线程与进程之间调度工作？](#21.%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

blocking I/O（阻塞 I/O）会让调用线程等操作完成或可以继续；non-blocking I/O（非阻塞 I/O）在暂时无法继续时迅速返回，但一次返回可能只表示“目前没数据”；async I/O 则让调用方提交操作，并在稍后收到完成结果。异步 API 描述调用关系，不表示底层必定由某个工作线程执行：网络 I/O 可由操作系统就绪通知驱动；Node.js v26.13.0 的回调式与 Promise 式文件系统 API（`fs.FSWatcher()` 除外）使用 libuv 线程池。Node 的 `worker_threads` 则针对 CPU 密集型 JavaScript，I/O 密集任务通常优先使用异步 API。使用有界阻塞池封装同步 API 也能释放请求线程，但那是用 worker 承担同步等待，并没有把底层调用变成原生异步操作。

读数据库、接网络响应或写文件时，先看运行时是否提供适用的异步 API：

~~~mermaid
flowchart TD
    IOWait[I/O 阶段] --> HasAsync{有合适的异步 API？}
    HasAsync --> AsyncAPI[有：任务等待时，<br/>事件循环处理其他工作]
    HasAsync --> BlockingPool[无：有界线程池，<br/>等待占一个 worker]
    AsyncAPI --> Limit[限制在途操作、连接、缓冲和队列]
    BlockingPool --> Limit
~~~

CPU 计算可以有不同目标；隔离、响应和跨核并行可能同时出现。先列出必须满足的目标，再对照可选路径与需要验证的条件：

| 要求 | 可选路径 | 必须验证的条件 |
| --- | --- | --- |
| 独立故障或地址空间边界 | 独立进程 | 进程边界能否隔开所需故障或内存；不可信代码的 OS 权限需另行限制；跨进程数据交接及成本。 |
| 满足响应预算，不要求跨核 | 当前路径拆成短片段并让出；工作线程；若前两种方式不达标，也可评估独立进程 | 当前片段能否在预算内；工作线程能否让响应路径及时获得调度（即使不并行也可能有用）；进程路径能否在当前负载下达到同一预算。 |
| 硬性要求跨核并行 | 能跨核执行该工作负载的线程；否则使用可并行的多进程 | 运行时是否真的并行执行该工作；系统是否有可用处理单元和 CPU 配额；数据交接成本；若同时有响应预算，两项都须满足。 |

无论选择哪条路径，都要限制作业入口和在途数据；使用线程池或进程池时，再限制执行槽和排队任务。

工作线程把 CPU 计算移出请求或事件循环线程；即使运行时不能让两段代码在多个处理单元上同时执行，调度器仍可能交替运行它们，让响应路径及时获得执行机会。这只能改善响应机会，不保证达成某个延迟预算。跨核并行要求多个处理单元同时执行，需按实际运行时语义判断；用进程跨边界时，通过 IPC（进程间通信）或显式共享内存交接数据。

**acct-17 的一次具体执行（教学假设）：** 服务运行 Node.js v26.13.0，数据库驱动支持按需异步游标；每次只取一批有界的订单行，字段为订单号、金额和日期。读库会等待 I/O，因此走异步 API。作业不要求硬性跨核；即使把 CPU 工作拆到当前可接受的最小片段并在片间让出，单片耗时仍超过请求响应预算，而移到 worker 后假设能达标。Node `worker_threads` 可以并行执行 JavaScript，但本例选择它是为响应路径让出执行机会，不以提高吞吐为前提；工作也不需要隔离可能崩溃的本地库。本例特意假设压缩器是同步调用、能保留状态的增量压缩器；不使用 `node:zlib` 异步流，因为 Node 的异步 zlib API 已使用内部线程池，选择它时 CPU 工作的放置方式不同。一个工作线程持有这条压缩流，并按顺序处理一批行；跨线程消息按运行时规则复制或转移数据，成本计入批次预算。

1. **读取。** 异步游标最多返回一个有界批次订单行；当前批次处理和写完前不拉下一批。
2. **压缩并写入。** worker 同步增量处理这批订单，回传零个或多个定长字节块以及“本批完成”确认；即使本批没有输出字节也会发确认。写入方按序写完所有字节、等写操作完成并收到批次确认后，才请求下一批。这样在途输入至多是一批。
3. **输入结束。** 游标读到 EOF 后，单独通知 worker 收尾/flush 压缩流。worker 发完全部尾块、清除这条压缩流的作业状态后，再发 `streamFinished` 确认；确认也表示它不再产出字节；协调者收到这个确认后，才把本作业的 worker 槽归还池。写入方收到确认并写完所有尾块、等待写操作完成，再关闭临时文件。
4. **发布。** 临时文件与本作业专属的最终路径位于同一文件系统，避免替换其他作业的文件。文件关闭后，同一协调者先把作业从 `running` 转到 `publishing`，紧接着提交 rename，中间不等待其他事件。rename Promise 的真实结果决定发布成功或失败；失败后按作业策略清理仍存在的临时文件。

同一事件循环上的作业协调者串行裁决取消与发布。若取消先在 `running` 状态被接受，作业转到 `cancelling`，不提交 rename；停止拉取数据，按游标契约请求取消并丢弃迟到行，等待查询取消或结束，并停止接受 worker 的迟到字节。若协调者尚未归还本作业的 worker 槽，就请求该 worker 停止，等待 `streamFinished` 或停止确认后归还一次；若已归还，则无需再通知该 worker。停止确认仍需在当前有界片段结束、压缩状态清理后发出。协调者还要等待已提交的文件写入结束，之后关闭并删除临时文件，再把作业标为 `cancelled`。若协调者先进入 `publishing` 并提交 rename，后到的取消不能覆盖结果；作业保持发布中，直到 rename 成功或失败，再据其结果进入成功或失败状态。

同步 CPU 片段里，消息回调不能打断正在运行的 JavaScript；只在同一同步回调的片段间读取由消息回调设置的局部变量也不会看到新值。要让取消消息生效，worker 必须在片段间把控制权交还 event loop，例如 `await timersPromises.setImmediate()`（`timersPromises` 来自 `node:timers/promises`），使消息回调运行；若需要在同步循环内响应，则由协调者对共享 buffer 执行 `Atomics.store`，worker 在片段间用 `Atomics.load` 检查停止标志。

这条合成路径说明机制和预期契约，不是已集成的报表服务。单独的 Node.js `fsPromises.writeFile()` AbortSignal 复演验证了取消后可能留下部分写入；没有连接数据库、worker 增量压缩或发布协调器做端到端回放，也没有测量吞吐或延迟。

### 共享计数为什么会丢更新？

race condition（竞态）是结果取决于并发操作顺序。`count += 1` 看起来是一条语句，概念上却是读、加一、写回三个步骤。若两个线程都先读到 10，再各自写 11，最终还是 11；预期的 12 丢了一次更新。对共享不变量，选择一条明确的所有权规则：锁、原子操作、单一写入者消息循环，或数据库约束。数据库中的库存不能靠进程内锁在所有服务副本间保护。

为说明两个 worker 同时上报完成数量时的读—改—写竞态，这里把报表缩小为一个共享计数器。以下例子把一个 32 位计数器放进共享内存，用 `Atomics.add` 将读—改—写变成原子操作。每个 worker thread（工作线程）加 100,000 次，因此两者结束后应为 200,000。Node 用 structured clone（结构化克隆）传递普通对象；本例则通过 `SharedArrayBuffer` 明确共享计数器所依赖的内存。

~~~javascript
// 保存为 counter.cjs；使用 Node.js v26.13.0 运行
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

经典资源分配模型中的“不可抢占”指资源不会被系统强行收回，不是 OS 调度器不能抢占线程。若等待不会超时或取消、线程也不会在等待中放弃所持资源，那么在每类资源只有一个实例且实例互斥时，wait-for graph（等待图）出现环就能证明 deadlock（死锁）。图中节点是线程，A→B 表示 A 等待由 B 持有的资源。例如 A 持有 R1 并等待 B 持有的 R2，B 持有 R2 并等待 A 持有的 R1，就形成 A→B→A。

若资源有多个可互换实例，应看 resource-allocation graph（资源分配图）：资源类型节点标出各实例，请求边与分配边分别表示等待和持有；图中有环只是死锁的必要线索，不足以单独证明死锁。设只有一个 R1、两个可互换的 R2 实例：A 持 R1 并等待任一 R2，B 持 R2a 并等待 R1，C 持 R2b 但能独立完成；C 归还 R2b 后，A 可继续并释放 R1，随后 B 也可继续，尽管分配图中曾有环。经典资源模型把互斥、持有并等待、资源不可强行收回和循环等待列为死锁的必要条件；消除任一条件可预防这类死锁，但多个资源实例下四者同时出现仍不保证系统已死锁。

这些条件不是判断任意慢请求的打勾清单：请求等待 I/O 或 Promise 未完成本身不构成资源等待环，先找出实际的资源与依赖关系。浏览器中等待 `fetch` 的 Promise 不会持有 DOM 独占锁，event loop 可在其 pending 期间运行其他代码；但真实依赖环、永不完成的 Promise 或资源耗尽仍可能让应用停滞。按全局一致的顺序取得多把锁可阻止这类锁环；缩短临界区能减少持锁时间。不要在持锁期间等待不确定时长的网络调用。

### 取消信号能证明什么？

在许多应用级任务 API 中，cancellation（取消）是要求任务协作停止，而不是调用方已经证明任务结束。代码需按 API 语义观察取消、停止提交后续副作用，并通过 `finally` 或等价清理路径释放自己拥有的资源。以 POSIX 为例，新线程默认启用延迟取消；目标线程可更改取消状态或类型。取消仍启用时，延迟请求会在取消点处理，异步取消则可能在任意时刻处理。`pthread_cancel` 成功只说明请求已排入，不代表线程已终止。对 joinable thread（可 join 线程）调用 `pthread_join` 会等待其终止；函数本身返回 `0` 表示 join 成功，`PTHREAD_CANCELED` 是通过输出参数取得的线程退出值，只有它能确认目标线程因取消而结束。若取消的是等待方，底层线程、数据库操作或远端请求仍可能继续；已提交的写入也不会因此回滚。调用方应以持久化业务结果确认副作用，而不是把“本地任务已取消”当成“操作没有发生”。

**接下来：** 本章区分执行资源和共享状态；Node 章节把这些边界落实到 isolate、worker 和进程。异步作业何时接受、重试或显式取消见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - Linux 中 `fork()` 后父子进程有不同内存空间，`mmap()` 可建立显式共享映射：[Linux man-pages 6.19, fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)，Description；[mmap(2)](https://man7.org/linux/man-pages/man2/mmap.2.html)，`MAP_SHARED` / `MAP_PRIVATE`；2026-11-11 核对。
> - 阻塞 `read`、非阻塞时可能返回 EAGAIN、`poll` 等待描述符就绪，以及提交操作后收到完成通知：[Linux man-pages, read(2)](https://man7.org/linux/man-pages/man2/read.2.html)、[poll(2)](https://man7.org/linux/man-pages/man2/poll.2.html)、[aio(7)](https://man7.org/linux/man-pages/man7/aio.7.html)，2026-11-11 核对。
> - POSIX 线程共享全局数据与堆、各自栈及线程状态：[Linux man-pages 6.19, pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)，2026-11-11 核对。
> - 子进程继承凭据和打开文件描述符的常见情况，以及可用 OS 策略限制文件与网络访问：[Linux man-pages 6.19, fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)，Description；[Linux kernel, Landlock](https://docs.kernel.org/userspace-api/landlock.html)，2026-11-11 核对。
> - 延迟与异步线程取消、请求不等于终止：[Linux man-pages 6.19, pthread_cancel(3)](https://man7.org/linux/man-pages/man3/pthread_cancel.3.html)，2026-11-11 核对。
> - joinable thread 的终止状态，以及通过 `PTHREAD_CANCELED` 区分取消退出：[Linux man-pages 6.19, pthread_join(3)](https://man7.org/linux/man-pages/man3/pthread_join.3.html)，2026-11-11 核对。
> - Node worker 的 CPU 用途、共享内存选项与 worker 池建议：[Node.js v26.13.0, worker_threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html)，计数程序于该版本重放，输出 200000。
> - `worker.postMessage()` 的结构化克隆与转移列表：[Node.js v26.13.0, Worker threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html#workerpostmessagevalue-transferlist)，2026-11-12 核对。
> - Node 异步 zlib API 使用内部线程池，同步 API 除外：[Node.js v26.13.0, Zlib](https://nodejs.org/download/release/v26.13.0/docs/api/zlib.html#threadpool-usage-and-performance-considerations)，2026-11-12 核对。
> - 将控制权让回 Node 事件循环的 Promise 版 `setImmediate()`：[Node.js v26.13.0, Timers](https://nodejs.org/download/release/v26.13.0/docs/api/timers.html#timerspromisessetimmediatevalue-options)，2026-11-12 核对。
> - Node 文件 API 的异步执行方式：[Node.js v26.13.0, File system](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#threadpool-usage)，核对于 2026-11-11。
> - Node.js v26.13.0 `fsPromises.writeFile()` 的 `AbortSignal` 只尽力取消内部缓冲，部分数据仍可能写入：[Node.js v26.13.0, File system](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#fspromiseswritefilefile-data-options)，2026-11-12 核对。
> - `fsPromises.rename()` 在 Promise 成功时完成名称变更；Linux 要求同一文件系统，目标已存在时会原子替换，因此本例使用专属目标名：[Node.js v26.13.0, File system](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#fspromisesrenameoldpath-newpath)，[Linux man-pages, rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html)，2026-11-12 核对。
> - 经典资源分配死锁的互斥、持有并等待、不可抢占与循环等待条件，以及多实例图中环的限制：[Coffman, Elphick, and Shoshani (1971), “System Deadlocks,” pp. 70–73](https://uobdv.github.io/Design-Verification/Supplementary/System_Deadlocks-Four_necessary_and_sufficient_conditions_for_deadlock.pdf)，2026-11-11 核对。
## 21. Node.js 如何在事件循环、工作线程与进程之间调度工作？

**合成案例：** API 收到导出 acct-17 报表的请求：异步数据库游标逐批读取订单行，服务把它们转换并压缩后写出文件；同一服务还要响应其他用户请求。沿用前一章的教学假设：数据库驱动通过网络 socket 等待读取；CPU 阶段使用应用或第三方库提供的同步、有状态增量压缩器，而不是 Node 内置的异步 zlib 流。每批输入有上限，压缩交给有界 `worker_threads` 池。这里要看 Node.js v26.13.0 如何把等待和 JavaScript 计算安排到不同线程或进程，并说明跨边界传递的数据。

![acct-17 的一批数据从异步数据库等待、主事件循环到 CPU 工作线程的可能交错](../../engineering-foundations/backend/resources/node-js-fundamentals-acct17-runtime-sequence.svg)

图中是一种可能的执行交错，不按时间比例绘制；步骤 7–9 是本批产生输出块时的写入分支，没有输出块时只等 `batchDone`。socket 通知报告 I/O 已就绪或操作已完成，并不等于数据库行已经生成；在本例里，驱动在主 isolate 的回调中取得并解析字节、组出有界订单行，`cursor.next()` 的 Promise 才结算。工作线程运行同步 CPU 代码或 libuv 池处理异步文件写入时，主事件循环仍可运行其他已就绪回调；消息或文件完成回调仍要等相应的事件循环获得执行机会。写入方何时停止提交数据、`write()` 与 `drain` 的通用规则见 [Node.js 流如何传播背压？](#23.%20Node.js%20%E6%B5%81%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%E8%83%8C%E5%8E%8B%EF%BC%9F)。

### 默认的 JavaScript 执行路径是什么？

Node.js 进程中的每个 JavaScript isolate（隔离环境）都有自己的 JavaScript 执行线程和事件循环（event loop）。主线程一次执行一个 JavaScript 回调；回调调用异步 API（application programming interface，应用程序编程接口）后可以注册后续处理并返回。若在回调里运行一段很长的同步循环，它会一直占住该 isolate 的线程，直到循环结束或代码主动让出控制权；这期间同一事件循环不能运行其他 JavaScript 回调。

`await` 本身不会创建线程，也不会把表达式自动交给后台。等待的 Promise 尚未结算时，`async` 函数会挂起并把控制权还给事件循环；Promise 结算后，函数剩余部分作为 JavaScript 工作在原来发起它的 isolate 中继续运行。因而，“异步”等于“调用方不必同步等结果”，不等于“所有工作都在另一个线程执行”。事件循环阶段、`process.nextTick()` 和 Promise 微任务的顺序见 [Node.js 事件循环阶段与微任务队列如何交互？](#22.%20Node.js%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E9%98%B6%E6%AE%B5%E4%B8%8E%E5%BE%AE%E4%BB%BB%E5%8A%A1%E9%98%9F%E5%88%97%E5%A6%82%E4%BD%95%E4%BA%A4%E4%BA%92%EF%BC%9F)。

若网络读取失败，驱动返回的 Promise 会拒绝，`await` 后的代码通过同一 isolate 的异常路径处理；Node 不会自动重试，也不会因调用方退出等待就自动取消底层操作。连接是否可取消、如何释放，属于具体驱动和应用的契约。

Node.js v26.13.0 下，常见 I/O 与计算路径可按具体 API 区分：

| 报表中的操作或 API | 等待或计算发生在哪里 | JavaScript 回调在哪里继续 |
| --- | --- | --- |
| 假设中的异步数据库驱动、网络 socket | 数据在网络中传输时，主 JavaScript 调用栈不必等待；运行时使用操作系统提供的异步 socket I/O 机制，具体采用就绪通知还是完成通知取决于平台 | 在发起操作的 isolate 事件循环中运行。驱动若使用其他实现，须按驱动契约确认 |
| `node:fs` 回调和 Promise 式文件系统 API（不含 `fs.FSWatcher`）、`dns.lookup()`、`crypto.pbkdf2()` / `scrypt()` / 回调形式的 `randomBytes()` 等特定加密 API，以及异步 `node:zlib` API | 已在池线程中执行的工作占用线程，包括它阻塞在系统调用中的时间；仍在队列中的提交任务等待空闲线程。执行时间长的工作可能拖慢同池其他 API | 回到提交该任务的事件循环 |
| 普通同步 JavaScript | 当前 JavaScript 线程执行；Node 不会因为函数很耗 CPU 就自动把它搬走 | 当前回调返回后，事件循环才能继续 |
| `node:worker_threads` | 应用创建的工作线程运行 JavaScript；可用于 CPU 密集型 JavaScript | 结果通过消息在接收方的事件循环中处理 |

libuv threadpool 与应用创建的 `worker_threads` 不是同一个池。v26.13.0 报告所带 libuv 版本为 1.53.0；libuv 将其线程池描述为在同一进程的多个事件循环之间共享。它服务的是特定 Node API 与 native addon 提交的工作，不会替应用运行任意一段 JavaScript。DNS 是一个常见边界：`dns.lookup()` 使用该池，而 `dns.resolve()` 通过异步 DNS 网络请求工作，不占用这个池。反过来，工作线程也不是处理一般网络等待的捷径：Node 内置异步 I/O 对此通常更合适。不要只从函数返回 Promise 推断其底层机制，先查该 API 的契约。

### 该把计算放在哪种执行资源上？

按 acct-17 的路径，异步数据库读取可以在主事件循环等待；若把压缩循环直接留在该线程，它会阻塞同一 isolate 的其他回调。案例的 CPU 片段无法在主路径的响应预算内完成，所以把有界批次交给工作线程。此处的同步增量压缩器是明确的案例假设，并非 Node 内置 zlib 的接口承诺：Node 异步 zlib API 使用 libuv threadpool，若改用它，计算的运行位置和共享池资源会不同。

| 选择 | 适合什么工作 | 成本与条件 |
| --- | --- | --- |
| 主事件循环上的异步 API | 数据库、网络等有适用异步 API 的 I/O 等待 | 让出调用栈不代表操作或缓冲区消失；同步 JavaScript 仍会阻塞该事件循环 |
| libuv threadpool 中的 API | Node 明确使用该池的文件、DNS、加密或压缩操作 | 共享有限池槽位；长任务会使其他同池任务排队。它不是可任意提交 JavaScript 的应用工作池 |
| `worker_threads` | CPU 密集型 JavaScript，且可以承担消息传递与线程管理成本 | 同一进程中的另一条 JavaScript 线程，可并行执行；需限制线程数、排队任务和输入字节 |
| `child_process` | 需要独立进程生命周期、地址空间或更强故障边界的工作 | 启动、内存和 IPC 成本；进程边界本身不构成权限沙箱 |
| `cluster` | 多个 Node 进程共同提供 HTTP/TCP 服务 | 每进程各有堆、缓存、连接池和运行时；连接分发不共享进程内会话，也不保证吞吐线性增长 |

如果多个导出任务同时进入，不能为每个任务无限创建一个工作线程。使用有限 worker pool（工作线程池）与有界等待队列；队列满时由服务明确拒绝、等待或施加上游背压。容量如何按阶段估算见 [如何估算并限制异步工作管线？](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)。进程、线程与响应预算的一般选择见 [何时选线程、进程或异步 I/O？](#20.%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)。

### Node 工作线程如何接收任务并回传数据？

`worker_threads` 在同一 Node.js 进程中创建另一条 JavaScript 执行线程。工作线程有自己的 JavaScript isolate 和普通堆，因此主线程中的普通对象不会因为地址相同而自动变成可见的共享对象；两条线程仍属于同一操作系统进程，共享进程生命周期和操作系统身份。Node.js 默认通过 `postMessage()` 传数据：普通可克隆值经 structured clone（结构化克隆）复制；把可转移的 `ArrayBuffer` 列入 transfer list（转移列表）则交出这块内存的所有权，发送方原来的视图会变为不可用；`SharedArrayBuffer` 才让双方访问同一块字节。若两线程可能并发访问同一共享区，使用 `Atomics` 建立同步；也可通过消息明确交接访问权，确保一方写入时另一方不同时读取或写入。

![一个 Node.js 进程内主线程与工作线程的数据所有权，以及它们和进程边界的区别](../../engineering-foundations/backend/resources/node-js-fundamentals-thread-ownership.svg)

acct-17 的每批订单行可作为一个有界消息发送给 worker。若发送 `Buffer`，接收端按结构化克隆得到的是 `Uint8Array`，需要 Buffer API 时可在接收侧转换。转移时要使用本次任务独占且可转移的 backing `ArrayBuffer`，例如单独分配的 `new ArrayBuffer(n)`；不要直接转移池化 `Buffer` 的 `.buffer`。池化 Buffer 通常不能转移，克隆时还可能复制整个 Buffer 池。转移后主线程不能再读取已交出的视图。无论复制还是转移，消息数量、数据量与等待队列都要受控。

本例按一个简化的作业协议串起批次与压缩流：

1. 作业从有界等待队列取出并分配 worker 槽后，固定到该线程；仍在队列中的作业不占工作线程。压缩器状态留在这个 worker 中，所有输入批次按序发给同一个 worker。等待读库或写入完成时，worker 可以暂时不执行 CPU 指令，但这个运行中的作业仍保留它的槽位。
2. 每批 worker 按序回传零个或多个输出块，再单独发送 `batchDone`。完成确认独立于块数量，所以没有输出字节的批次也能结束。主线程按序提交这批的异步文件写入；本例等所有输出写入完成并收到 `batchDone` 后，才请求下一批。`node:fs` 的异步文件操作使用 libuv threadpool；主事件循环在写入待完成期间仍可处理其他已就绪回调。
3. 这个批次边界比普通流背压更严格：对于处于正常可写状态的 `Writable`，`write()` 返回 `true` 表示可以继续提交块，不表示写入已完成；返回 `false` 才应暂停并等 `drain`。本例选择等本批写入操作全部完成及 `batchDone` 两项条件都满足后再读下一批。写操作完成不等于文件已经物理持久化。
4. 游标读到 EOF 后，主线程通知同一个 worker 冲刷压缩流。worker 发完全部尾块、清除作业的压缩状态后再发 `streamFinished`；收到它表示 worker 不会再产出字节，协调者可归还槽位。文件写入方收到 `streamFinished`，并确认所有尾块都已写完（也可能没有尾块）后，才关闭临时文件。临时文件发布与取消的竞争顺序见[前一章的单一作业协调者](#20.%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)。

下面用同一个小型 Fibonacci 输入演示 `Worker` 的任务和结果消息。它只展示 API 形状；`fib(10)` 很轻，运行结果不能证明线程会加速任务。

~~~javascript
// 保存为 worker-fib.cjs；使用 Node.js v26.13.0 运行
const { Worker, isMainThread, parentPort } = require('node:worker_threads');

function fib(n) {
  let a = 0;
  let b = 1;
  for (let i = 0; i < n; i++) [a, b] = [b, a + b];
  return a;
}

if (isMainThread) {
  const worker = new Worker(__filename);
  worker.once('error', error => {
    console.error(error);
    process.exitCode = 1;
  });
  worker.once('message', result => console.log(result));
  worker.postMessage(10);
} else {
  parentPort.once('message', n => parentPort.postMessage(fib(n)));
}
~~~

输出 `55`。真实 CPU 任务应复用一个有界工作线程池，而不是每次请求都构造 `Worker`。同步 JavaScript 正在占用 worker 时，worker 的消息回调也要等到当前回调让出后才能执行；若工作必须响应取消，需在片段间交还事件循环或检查共享停止标志，细节见前一章[线程工作取消的顺序](#20.%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)。工作线程出现未捕获 JavaScript 错误时，父线程可通过 `Worker` 的 `error` 事件处理；它仍不是隔离 native 崩溃的独立进程边界。

### 子进程怎样接收一个计算任务？

`child_process.fork()` 会启动一个新的 Node.js 进程并建立 IPC（进程间通信）通道；它不是 POSIX `fork(2)`，不会复制正在运行的父进程内存。`send()` 的消息会序列化后在另一侧解析；默认是 JSON，数字 `10` 和 `55` 可直接往返。子进程拥有独立地址空间，但若没有另行设置凭据和操作系统策略，它不因此失去父进程用户本来能访问的资源；它不是安全沙箱。

![child_process.fork 的序列化消息边界，以及 cluster 默认轮询时由 primary 接收并分发连接、worker 共用服务端口的关系](../../engineering-foundations/backend/resources/node-js-fundamentals-process-cluster.svg)

下面仍用同一个输入计算 `fib(10)`，只展示父进程和子进程间的请求与结果消息，不是生产任务队列：它没有排队上限、重复任务保护或 supervisor 级别的重启策略。

~~~javascript
// 保存为 report-child.cjs；使用 Node.js v26.13.0 运行
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

输出 `55`。若传输较大的订单批次，IPC 仍需序列化和数据复制；也可显式传递受支持的 socket/handle。进程只隔开地址空间，不会自动隔开磁盘、网络、CPU 配额或数据库连接额度。

### cluster 怎样把 HTTP 连接交给多个进程？

`cluster` 创建的是 Node 子进程，不是 `worker_threads`。常见的默认 round-robin（轮询）路径由 primary 在监听端口上接收新 TCP 连接，再把每条连接交给一个 worker；Windows 默认使用另一种由 worker 自行接受连接的方式。Node 不提供应用级路由保证：cluster 按连接安排，持久连接上的多条 HTTP 请求仍可落在同一进程，登录会话或缓存也不会在 worker 间自动共享。若要共享这些状态，应使用进程外存储或明确的通信协议。

~~~javascript
// 保存为 cluster-report.cjs；使用 Node.js v26.13.0 运行
const cluster = require('node:cluster');
const http = require('node:http');
const { availableParallelism } = require('node:os');

const configuredLimit = 2; // 教学配置；不是通用容量建议
const workerCount = Math.min(availableParallelism(), configuredLimit);

if (cluster.isPrimary) {
  for (let i = 0; i < workerCount; i++) cluster.fork();
  cluster.on('exit', (worker, code, signal) => {
    console.error('worker exited', worker.id, code, signal);
  });
} else {
  http.createServer((request, response) => {
    response.end(`report API served by process ${process.pid}`);
  }).listen(8000);
}
~~~

示例的 worker 退出回调只记录事件；Node 不会自动补充进程或决定重启退避策略，生产服务需要明确这些恢复行为。上限 `2` 只是教学配置。Node 文档建议用 `os.availableParallelism()` 估算可用并行度，而不是用 `os.cpus().length`；实际进程数还要按容器 CPU 配额、请求时延与每进程连接池等总资源预算决定。每个进程都有独立 JavaScript 堆、缓存与按进程设置的池；进程数增大通常会提高内存需求，但操作系统也可能共享只读页面，因此不是严格按进程数成倍增长。若本例运行 2 个 cluster worker，并为每个服务 worker 配置 2 个 CPU 工作线程槽位和最多 5 个数据库连接，服务配置上限就是 4 个计算槽位与 10 个连接。4 个槽位不保证有 4 个处理单元能同时运行；共享 CPU 配额或数据库容量更小时，仍会排队。

若用 PM2 管理多个实例，可显式给出数量，例如 `pm2 start app.js --name api -i 2`，再用 `pm2 list` 或 `pm2 monit` 查看，用 `pm2 reload api` 发起集群重载。PM2 的 reload 可能在重载超时时退化为 restart。在支持 POSIX 信号的平台上，停止时默认先发 `SIGINT`，应用若未在默认 `kill_timeout` 约 1600 ms 内退出，PM2 会发 `SIGKILL`。需要更换首个停止信号时，可配置 `PM2_KILL_SIGNAL`；应用必须处理部署实际发来的信号并排空请求、工作线程与连接池。完整的关闭次序见 [Node.js 服务如何排空并关闭？](#24.%20Node.js%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E6%8E%92%E7%A9%BA%E5%B9%B6%E5%85%B3%E9%97%AD%EF%BC%9F)。

> [!info]- 来源
> - `worker_threads` 的 CPU 适用场景、消息和共享内存：[Node.js v26.13.0, Worker threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html)，2026-11-12 核对；本页工作线程 Fibonacci 示例于 Node.js v26.13.0 重放。
> - structured clone、ArrayBuffer 转移后发送方视图失效、池化 Buffer 不能直接转移，以及 Buffer 接收为 Uint8Array：[Node.js v26.13.0, Worker threads, TypedArray/Buffer 注意事项](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html#considerations-when-transferring-typedarrays-and-buffers)，2026-11-12 核对。
> - 子进程 `fork()` 的新 Node 实例、IPC 序列化和默认 JSON 模式：[Node.js v26.13.0, Child processes, `fork()` / IPC](https://nodejs.org/download/release/v26.13.0/docs/api/child_process.html#child_processforkmodulepath-args-options)，示例于 Node.js v26.13.0 重放，输出 `55`。
> - `cluster` 共享服务端口、连接调度方式及进程内会话不共享：[Node.js v26.13.0, Cluster, “How it works”](https://nodejs.org/download/release/v26.13.0/docs/api/cluster.html#how-it-works)，2026-11-12 核对。
> - `availableParallelism()` 与 `os.cpus().length` 的区别：[Node.js v26.13.0, OS](https://nodejs.org/download/release/v26.13.0/docs/api/os.html#osavailableparallelism)，2026-11-12 核对。
> - 异步文件系统 API 使用 libuv threadpool；`dns.lookup()` 与 `dns.resolve()` 的不同实现；`crypto.pbkdf2()`、`scrypt()` 等指定 API 与异步 zlib API 使用该池：[Node.js v26.13.0, File system](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#threadpool-usage)、[DNS](https://nodejs.org/download/release/v26.13.0/docs/api/dns.html#implementation-considerations)、[Crypto](https://nodejs.org/download/release/v26.13.0/docs/api/crypto.html)、[Zlib](https://nodejs.org/download/release/v26.13.0/docs/api/zlib.html#threadpool-usage-and-performance-considerations)，2026-11-12 核对。
> - 普通可写状态下 `Writable.write()` 的 `true` / `false`、`drain` 与写操作完成的区别：[Node.js v26.13.0, Stream, `writable.write()`](https://nodejs.org/download/release/v26.13.0/docs/api/stream.html#writablewritechunk-encoding-callback)，2026-11-12 核对。
> - 多线程共享字节区的同步指导：[ECMAScript Shared Memory Guidelines](https://tc39.es/ecma262/multipage/memory-model.html#sec-shared-memory-guidelines)，2026-11-12 核对。
> - libuv threadpool 的全局共享范围、工作线程执行任务及完成回调返回事件循环：[libuv 1.x, Thread pool work scheduling](https://docs.libuv.org/en/v1.x/threadpool.html)，Node.js v26.13.0 本机 `process.versions.uv` 输出 `1.53.0`。
> - Node.js 返回依赖版本字符串及 v26.13.0 的当前版本状态：[Node.js v26.13.0, `process.versions`](https://nodejs.org/download/release/v26.13.0/docs/api/process.html#processversions)，[Node.js 下载页](https://nodejs.org/en/download/)，2026-11-12 核对。
> - PM2 集群重载失败后的 restart 回退、`SIGINT` 与 `kill_timeout` 的终止顺序，以及可配置的 `PM2_KILL_SIGNAL`：[PM2, Cluster Mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/)、[Graceful Start/Shutdown](https://pm2.keymetrics.io/docs/usage/signals-clean-restart/)、[Environment Variables](https://pm2.keymetrics.io/docs/usage/environment/)，2026-11-12 核对。
## 22. Node.js 事件循环阶段与微任务队列如何交互？

**合成案例：** Node.js 服务收到 GET /api/reports/42。请求处理函数（handler）启动异步报表读取、安排一个计时器回调，然后返回。为让例子可以离线运行，下面用 CLI 主模块顶层代码代演 handler 同步发起工作并返回的部分，再用读取脚本文件的 I/O callback 展示读取完成后的调度。顶层 timeout 与 immediate 只校准 CLI 入口的顺序，不代表 HTTP handler 内的顺序。

Node.js 的事件循环（event loop）按阶段安排 I/O 回调和计时器，但主 JavaScript 线程一次只运行一个同步调用栈。调用异步 I/O API 后，函数可以先返回；数据就绪时，Node 再把回调交给该隔离环境（isolate）。底层 I/O 由驱动、操作系统和 libuv（Node.js 使用的跨平台 I/O 库）具体完成，不能仅凭返回 Promise 推断某个数据库驱动的实现。

### I/O 回调、定时器和 setImmediate() 何时推进？

先看概念顺序：Node 从一段由宿主派发的 JavaScript 回调（callback）重新取得控制权时，会在调度检查点清空 nextTick 和微任务（microtask）队列。检查点不是 libuv 阶段，也不只出现在阶段边界：同一阶段的两个 callback 之间也可能执行检查点；普通 JavaScript 嵌套函数返回给它的调用方不会触发这个交接。图只放大本例的 I/O→检查点→check/timer 交接，不表示所有阶段都只按这一条路径运行。

![Node.js v26.13.0 中 I/O callback 返回后，经调度检查点、check 阶段和 timer 的局部流程](../../engineering-foundations/backend/resources/node-event-loop-io-phases.svg)

下表列出常见阶段及职责；它不是每轮实际执行顺序的时间线。特别是 libuv 1.45.0 调整了到期 timer 的检查位置，见表后说明。

| 阶段 | 在本例中要看什么 |
| --- | --- |
| timers（计时器） | 执行已达到时间门槛的 setTimeout / setInterval 回调；门槛过了也仍须等待可运行的调度机会 |
| pending callbacks（待处理回调） | 执行少数被推迟到下一轮的系统回调 |
| idle、prepare（内部阶段） | libuv 内部阶段，不是一般应用代码的回调点 |
| poll（I/O 轮询） | 处理大多数 I/O 回调；没有可运行 I/O 时，可能等待新事件 |
| check（检查） | 执行已排入的 setImmediate 回调 |
| close callbacks（关闭回调） | 处理部分 handle 的关闭事件 |

从 libuv 1.45.0 起（该版本随 Node.js v20.3.0 引入），默认循环模式在 poll 之后检查到期 timer；为兼容旧行为，进入默认循环前仍有一次预检查。较早版本每轮 poll 前也会检查 timer。无论版本如何，阶段名不能当作精确时钟：setTimeout(fn, 0) 在 Node.js v26.13.0 中按 1 毫秒门槛处理；计时器不会切断正在运行的回调，也不保证在指定毫秒恰好运行。

**最小可运行回放。** 为避免连接真实数据库，以下 CLI 主模块同步发起异步工作，代演 handler 发起读取后返回的部分；它的顶层 timer/immediate 仅用于校准 CLI 入口顺序。读取本脚本文件的 `fs.readFile` callback 代表“报表读取已完成”，只用来展示 I/O callback 返回时的队列交接，不模拟数据库驱动的底层传输或耗时。I/O callback 失败时只输出错误并结束该分支；成功时才登记后续队列：

~~~javascript
// 保存为 node-event-loop-io-demo.cjs；使用 Node.js v26.13.0 运行
const fs = require('node:fs');
console.log('CLI main module starts');
process.nextTick(() => console.log('nextTick checkpoint'));
Promise.resolve().then(() => console.log('Promise reaction'));
queueMicrotask(() => console.log('queueMicrotask'));
setTimeout(() => console.log('top-level timeout'), 0);
setImmediate(() => console.log('top-level immediate'));

fs.readFile(__filename, error => {
  if (error) {
    console.log('I/O failed; stop this branch');
    return;
  }

  console.log('I/O callback: report bytes are ready');
  process.nextTick(() => console.log('nextTick from I/O callback'));
  Promise.resolve().then(() => console.log('Promise from I/O callback'));
  queueMicrotask(() => console.log('queueMicrotask from I/O callback'));
  setTimeout(() => console.log('timer from I/O callback'), 0);
  setImmediate(() => console.log('immediate from I/O callback'));
});
~~~

Node.js v26.13.0 的一次本地运行输出：

~~~text
CLI main module starts
nextTick checkpoint
Promise reaction
queueMicrotask
top-level immediate
I/O callback: report bytes are ready
nextTick from I/O callback
Promise from I/O callback
queueMicrotask from I/O callback
immediate from I/O callback
top-level timeout
timer from I/O callback
~~~

这是一次运行记录，不是完整固定序列。CLI 主模块中 top-level timeout 与 top-level immediate 的相对先后不保证；文件 I/O 何时就绪也会影响它们相对 I/O callback 的位置。可依赖的局部事实是：同一个 I/O callback 排入的 immediate 在它排入的 0ms timer 前运行；该 callback 交还控制权后，Node 在继续调度之前处理 nextTick 与微任务。检查点跟宿主接管 callback 的边界有关，不是每个阶段结束时的统一钩子；下面用同阶段的两个 immediate 展示这一点。

~~~javascript
setImmediate(() => {
  console.log('immediate 1');
  process.nextTick(() => console.log('nextTick'));
  queueMicrotask(() => console.log('microtask'));
});
setImmediate(() => console.log('immediate 2'));
~~~

在 Node.js v26.13.0 中运行此 CLI 文件，输出为 `immediate 1 → nextTick → microtask → immediate 2`：Node 在同一 check 阶段的两个 callback 之间处理检查点。普通 JavaScript 函数的嵌套 `return` 仍在当前调用栈内，不会因此触发同一检查点。

如果某段同步 callback 花了 120ms，即使一个 100ms timer 已越过门槛，callback 仍会先跑完。timer 回调只能晚些得到执行；它不会中断 callback，也不会自动取消尚未完成的数据库查询。服务端应以明确的 deadline（截止时间）判断请求是否已超时。若要取消底层操作，必须用该驱动支持的取消机制；计时器本身只负责安排一段未来代码。

### nextTick 与 Promise 微任务的顺序为何会变？

process.nextTick() 使用 Node 管理的 nextTick 队列；Promise reaction（Promise 的处理回调）与 queueMicrotask() 共用 JavaScript 微任务队列。下面的排序示例都由 Node CLI 直接把文件作为主模块运行：CommonJS（CJS）主模块 `node queues.cjs` 在同步入口返回后的检查点先排空 nextTick，再排空微任务；ES module（ESM）主模块 `node queues.mjs` 的入口模块求值处于微任务处理中，所以模块代码安排的微任务先于 nextTick。这个差异取决于开始执行这段代码时是否已在处理微任务，不能只凭文件扩展名推断。

![Node.js v26.13.0 直接运行 CJS 和 ESM 入口，以及独立嵌套微任务示例的队列顺序](../../engineering-foundations/backend/resources/node-event-loop-queue-contexts.svg)

分别保存并直接以 Node CLI 运行以下两段代码；文件扩展名决定模块语法：

~~~javascript
// queues.cjs — Node.js v26.13.0
const { nextTick } = require('node:process');

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
~~~

输出：

~~~text
nextTick
promise
microtask
~~~

~~~javascript
// queues.mjs — Node.js v26.13.0
import { nextTick } from 'node:process';

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
~~~

输出：

~~~text
promise
microtask
nextTick
~~~

Promise 与 queueMicrotask 共享同一个先进先出（FIFO）微任务队列，因此这两段代码中它们按登记顺序运行。上下文差异不是 Promise 语言改了规则；在这个直接以 CLI 运行的例子里，ESM 入口模块在 Node 处理 Promise/microtask 队列时求值。

若 CJS 主模块顶层同步 `require()` 同一份 ESM 文件，求值发生在当前 CJS 同步栈内，不能套用“直接运行 ESM 主模块”的顺序。同步 `require(esm)` 仅适用于不含顶层 `await` 的 ESM 依赖图；上面的 `queues.mjs` 没有顶层 `await`。将两个文件保存在同一目录再运行：

~~~javascript
// require-esm-context.cjs — Node.js v26.13.0
require('./queues.mjs');
console.log('CJS require returned');
~~~

输出：

~~~text
CJS require returned
nextTick
promise
microtask
~~~

因此扩展名标明文件使用何种模块语法，但不独自决定它在 Node 调度器中的执行上下文。

还要注意微任务正在运行时发生的情况。以下是另一个独立的 CJS CLI 回放：

~~~javascript
// 保存为 node-event-loop-nested-tick.cjs；使用 Node.js v26.13.0 运行
Promise.resolve().then(() => {
  console.log('microtask A');
  process.nextTick(() => console.log('nextTick X'));
  Promise.resolve().then(() => console.log('microtask B'));
  queueMicrotask(() => console.log('queueMicrotask C'));
});
~~~

输出是 microtask A、microtask B、queueMicrotask C、nextTick X。A 运行时把 B 和 C 放进当前微任务队列，又把 nextTick X 单独排队；当前微任务队列先排空，Node 才处理新排入的 nextTick。不能把“nextTick 先于 Promise”推广到所有正在执行的上下文。

Node.js v26.13.0 将 process.nextTick() 标为历史状态（Legacy），并建议多数用户代码优先用 queueMicrotask()。旧库可能依赖 nextTick 的排序或额外参数，因此迁移时要保留并检查其既有调用契约。若递归调用 nextTick 不断制造工作，Node 会持续清空队列，迟迟不能进入 poll，I/O 回调也就无法推进。对一般可移植的同步调用后延续，用 queueMicrotask() 更合适。

一种仍可能需要兼容的旧 API 约定是：工厂函数先返回事件发射器（emitter），再于当前调用栈退栈后发出 ready，让调用方来得及注册监听器。callback API 也曾用 nextTick 延后交付同步发现的验证错误。下面只演示前一种顺序，不表示新代码应普遍选择 nextTick：

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

运行输出 ready；若同步调用后的延续无需兼容 nextTick 特有顺序，优先使用 queueMicrotask()。

### 读报表请求在哪一步继续或停止？

把一次请求重新串起来：

| 时点 | 输入或状态 | Node 执行到的结果 |
| --- | --- | --- |
| handler 运行 | GET /api/reports/42；启动读取、排入 timer | 同步 handler 跑完并返回；timer/I/O 不能抢占它 |
| 等待或继续 | 读取仍未就绪 | poll 可等待 I/O；到期 timer 也可能先获得运行机会，但不会自动停止读取 |
| 读取成功 | 回调收到字节或驱动结果 | 处理当前 callback；控制权交还 Node 后处理 nextTick / 微任务，再继续调度；下一项不一定属于新阶段 |
| 读取失败 | callback 收到错误 | 请求代码进入错误处理并结束该分支；是否重试或取消由应用与驱动契约决定 |

本地回放只读取自己的脚本，成功分支可实际运行；数据库错误和请求取消的语义必须按具体驱动实现确认。浏览器有自己的事件循环、task 和渲染规则，不能把 Node 的 libuv 阶段图套过去，见[浏览器事件循环](../../frontend/runtime/event-loop.md)。Node 主线程、worker_threads、libuv threadpool 与进程的工作边界见[Node.js 如何在事件循环、工作线程与进程之间调度工作？](#21.%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

> [!info]- 来源
> - Node.js v26.13.0 的 nextTick Legacy 状态、额外参数与递归行为：[process.nextTick()](https://nodejs.org/download/release/v26.13.0/docs/api/process.html#processnexttickcallback-args)；CommonJS/ES module 队列排序：[When to use queueMicrotask vs process.nextTick](https://nodejs.org/download/release/v26.13.0/docs/api/process.html#when-to-use-queuemicrotask-vs-processnexttick)；CJS 主模块同步加载 ESM 的边界：[modules — Loading ECMAScript modules using require()](https://nodejs.org/download/release/v26.13.0/docs/api/modules.html#loading-ecmascript-modules-using-require)；核对日期：2026-11-12。文中的 CJS、ESM、同步 require(esm) 和嵌套队列代码已在该版本重放。
> - 阶段职责、poll 对 I/O 和 timer 的调度、Node.js v20.3.0 引入 libuv 1.45.0 后的 timer 检查变化、CLI 主模块与 I/O callback 中 timer/immediate 顺序，以及 nextTick 检查点的宿主交接边界：[Node.js Event Loop](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick)；精确的 libuv 引入版本：[Node.js v20.3.0 release notes](https://nodejs.org/en/blog/release/v20.3.0)；核对日期：2026-11-12。Learn 文档说明较早版本的阶段行为与当前版本差异。
> - setTimeout 的最小 delay 处理、时间门槛及“不会精确准点”的保证：[Node.js v26.13.0 Timers](https://nodejs.org/download/release/v26.13.0/docs/api/timers.html#settimeoutcallback-delay-args)；核对日期：2026-11-12。
> - libuv loop 阶段与网络 I/O callback 的运行线程：[libuv Design overview](https://docs.libuv.org/en/v1.x/design.html#the-i-o-loop)；核对日期：2026-11-12。具体数据库驱动实现不由本地文件回放证明。
## 23. Node.js 流如何传播背压？

**案例接续 acct-17：** [Node.js 运行时章的导出任务](#Node%20%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E5%A6%82%E4%BD%95%E6%8E%A5%E6%94%B6%E4%BB%BB%E5%8A%A1%E5%B9%B6%E5%9B%9E%E4%BC%A0%E6%95%B0%E6%8D%AE%EF%BC%9F)从数据库逐批读取账户活动行，工作线程用同步增量压缩器生成字节，再写入本作业的临时文件。这里有意缩小并切换实现：用 Node.js 原生 `Readable → Transform → Writable` 管线处理同一账户的三条教学报表行，观察缓冲、backpressure（背压）、文件结束和取消。这个小例子使用 `node:zlib` 的 `createGzip()`，不代表运行时章选择的压缩执行位置，也不模拟对象存储的发布确认。

### 什么状态表示写入方该等一等？

Readable（可读流）产生数据块；Writable（可写流）接收数据块；Duplex（双工流）的可读与可写两侧独立工作；Transform（转换流）是一种 Duplex，一侧接收输入，另一侧输出转换后的块。对处于正常可写状态的 Writable，`write(chunk)` 先接收当前块：若调用返回 `true`，当前可以继续提交；若返回 `false`，当前块已经被接收，但内部写缓冲已达到 `highWaterMark`（缓冲阈值），此时停交后续块，等 `drain` 再继续。`drain` 表示 Writable 的底层实现已处理到可以恢复写入；它不证明文件已持久化或远端应用已收到数据。

若流已结束、销毁或报错，`false` 不再保证当前块已被接收，也不保证之后会发出 `drain`；这时处理 `error`、`close` 或管线失败结果，而不是继续等待 `drain`。

`highWaterMark` 是各流队列自己的阈值：Readable 据此决定是否继续拉取，Writable 据此反馈上游是否该暂停交块；它不是整条管线的硬性内存上限。按 Buffer 缓冲时计字节；队列里保留为 JavaScript 字符串时按 UTF-16 code unit（码元）计，例如 Readable 调用 `setEncoding()`，或 Writable 设置 `decodeStrings: false`；对象模式按对象个数计。Writable 默认会把字符串转成 Buffer。`Readable.from()` 默认使用对象模式；下面明确设置 `objectMode: false`，让每一行按流的非对象模式处理。Readable、Writable 各有自己的队列；Transform 也分别维护写侧和读侧缓冲。因此每个阶段的阈值、单个大块、驱动的预取和管线外队列都要计入内存预算。只有生产者能响应需求时，背压才能让它减慢；若生产者另有后台预取，或先把全部行装进数组，流无法自动限制那部分工作。

使用 `pipe()` 或 `pipeline()` 时，背压先沿相邻流传播：若 Writable 的 `write(chunk)` 返回 `false`，Node 暂停直接上游的可读侧（这里是 Transform 的读侧）。若 gzip 仍有输出，它会留在 Transform 的读缓冲；这个队列持续积压到阈值后，Transform 会延后处理后续输入，使写侧消化变慢。写侧还可继续吸收已经在途的数据；当它自己的队列也达到阈值，`Transform.write()` 才会返回 `false`，让 pipe 暂停更早一段的 Readable。两侧缓冲独立计量，阈值可以相同，反馈只沿相邻流逐段传。`drain` 使直接上游恢复，缓冲逐段退下后各段继续工作；这不是 sink 一次性向整条管线广播暂停。手写 `write()` 循环则必须自己遵守 `false` / `drain` 契约。选 `pipeline()` 主要是连接流并统一处理错误和结束，不会自动给管线外的任务队列、数据库预取或远端副作用设置上限。

![数据按顺序流经 Readable、Transform、Writable 和文件；write(chunk) 返回 false 先暂停直接上游的可读侧，Transform 的读写缓冲分别积压后再向更早一段施加背压](../../engineering-foundations/backend/resources/node-stream-backpressure-and-cleanup-buffer-flow.svg)

### 如何按需读取报表行并调用游标清理？

下面把合成游标包装成异步生成器：数组只模拟三条固定教学报表行；每次 `next()` 取一行，生成器不会另存整份 CSV。它逐行格式化 CSV，`Readable.from()` 按需读取这些字符串，再经 gzip Transform 写入本地文件。这里的本地文件只用于演示流的接口；每次运行创建独占临时目录，只清理该目录；实际导出仍由任务协调者决定何时发布。

~~~javascript
// 保存为 export-report.cjs；使用 Node.js v26.13.0 运行
const { createWriteStream } = require('node:fs');
const { mkdtemp, rm } = require('node:fs/promises');
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const { createGzip } = require('node:zlib');
const { tmpdir } = require('node:os');
const { dirname, join } = require('node:path');

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
      console.error('cursor closed:', closed);
    },
  };
}

function openPendingCursor(accountId, controller) {
  let started = false;
  let release;
  return {
    next() {
      if (started) return Promise.resolve(null);
      started = true;
      const pending = new Promise(resolve => {
        release = resolve;
      });
      console.error('1 next started; query is pending');
      setTimeout(() => {
        console.error('2 request abort');
        controller.abort();
      }, 20);
      setTimeout(() => {
        console.error('3 release pending query');
        release(null);
      }, 100);
      return pending;
    },
    async close() {
      console.error('4 cursor closed after query release');
    },
  };
}

function csvCell(value) {
  const text = String(value);
  return /[",\r\n]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
}

async function* reportRows(accountId, signal, openCursor) {
  const cursor = openCursor(accountId);
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

async function* csvRows(accountId, signal, openCursor) {
  yield 'id,accountId,amount\n';
  for await (const row of reportRows(accountId, signal, openCursor)) {
    yield [row.id, row.accountId, row.amount].map(csvCell).join(',') + '\n';
  }
}

async function exportReport(signal, openCursor = openReportCursor) {
  const tempDir = await mkdtemp(join(tmpdir(), 'acct17-report-'));
  const tempPath = join(tempDir, 'report.csv.gz.part');
  try {
    await pipeline(
      Readable.from(csvRows('acct-17', signal, openCursor), { objectMode: false }),
      createGzip(),
      createWriteStream(tempPath, { highWaterMark: 32 * 1024 }),
      { signal },
    );
  } catch (error) {
    console.error('pipeline rejected:', error.name);
    try {
      await rm(tempDir, { recursive: true, force: true });
      console.error('removed this run temp directory:', tempDir);
    } catch (cleanupError) {
      throw new AggregateError(
        [error, cleanupError],
        'export failed and this run temp directory could not be removed: ' + tempDir,
      );
    }
    throw error;
  }
  return tempPath;
}

async function main() {
  const abortReplay = process.argv.includes('--abort-replay');
  const controller = new AbortController();
  const openCursor = abortReplay
    ? accountId => openPendingCursor(accountId, controller)
    : openReportCursor;

  try {
    const outputPath = await exportReport(controller.signal, openCursor);
    if (abortReplay) {
      await rm(dirname(outputPath), { recursive: true, force: true });
      console.error('unexpected success in abort replay; removed this run directory');
      process.exitCode = 1;
      return;
    }
    process.stdout.write(outputPath + '\n');
  } catch (error) {
    if (abortReplay && error.name === 'AbortError') {
      return;
    }
    console.error('export failed:', error);
    process.exitCode = 1;
  }
}

main().catch(error => {
  console.error('unexpected top-level failure:', error);
  process.exitCode = 1;
});
~~~

把代码保存为 `export-report.cjs` 后可直接重放：

~~~sh
report_path="$(node export-report.cjs)"
printf '产物：%s\n' "$report_path"
gzip -dc < "$report_path"
~~~

解压结果应为：

```csv
id,accountId,amount
event-1,acct-17,12
event-2,acct-17,8
event-3,acct-17,-2
```

成功时命令打印本次运行独占目录内的产物路径并保留文件。输入数组只模拟三条固定游标记录；流生成器逐行产出，不会另存整份 CSV。代码没有刻意制造慢 sink：`32 KiB` 仅是本地文件写流的阈值，短小的四行输出不证明实际触发 `write(chunk) === false` 或 `drain`。`createGzip()` 是 Node 内置异步 zlib Transform，压缩工作由 libuv threadpool（线程池）执行；这与运行时章的自建 JavaScript worker 不同。

`openReportCursor()` 是教学 mock，不代表生产 job 的数据读取方式。生产 worker 要从已经持久接受且已授权的 job 读取账户、时间范围和页数上限，不能重新信任队列正文。现有报表设计最多顺序读 12 页，每页最多 100 行；不足 100 行时结束，若第 12 页仍满则以范围超限失败，不能静默截断。每页各用一个短事务；读完一页先归还连接，再压缩与写出，而且不承诺所有页面来自同一数据库快照，见[如何限定 ORM Session 并排查连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。若换成一直持有数据库游标的长流，下游背压可能延长事务和连接的占用时间，需计入连接池与 worker 槽预算。确需同一快照时，应明确采用有界长事务或版本化快照并核算代价，不能静默把短事务分页换成长游标。

若要重放挂起读取期间的取消，运行 `node export-report.cjs --abort-replay`。该路径在首次 `cursor.next()` 已开始并挂起后，20 ms 触发 abort，100 ms 才释放模拟查询；日志顺序应是 next 开始、请求取消、查询释放、finally 调用并等待 `cursor.close()`、管线以 `AbortError` 拒绝、清理本次运行的临时目录。预期没有产物路径写到 stdout，退出码为 0。

### 输入结束、写完和取消分别能证明什么？

正常路径中，`cursor.next()` 返回 `null` 表示合成结果集耗尽；它不是在读取文件时遇到的 EOF。生成器离开 `try` 后会在 `finally` 调用并等待 `cursor.close()`，然后不再产出 CSV；这只表示它等待了关闭操作，不保证真实 driver 的关闭一定成功。源 Readable 的数据耗尽后发出 `end`；输入结束后，gzip 仍可能产生尾块，写入方随后才结束。Transform 的输出块数量不必等于输入块数；压缩器须把尾块交给写入方后，文件写流才可能完成，所以不能把“最后一行已送进压缩器”当成文件完整。

| 可观察状态 | 它说明什么 | 它没有证明什么 |
| --- | --- | --- |
| 源 Readable `end` | 所有源输入块已被消费，没有更多输入 | gzip 读侧结束或下游已写完、文件已持久化 |
| Writable `finish` | 调用 `end()` 后，所有写入数据已交给底层系统处理 | 数据已在断电后仍可恢复，或 HTTP 客户端已收到完整正文 |
| 文件流 `close` | 流及其文件描述符等底层资源已关闭 | 内容已满足所需的崩溃持久性 |
| `pipeline()` Promise fulfilled | 管线按正常路径完成 | 报表业务记录已成功发布或远端对象存储已持久接受 |

本例用默认自动关闭的本地文件流。若业务要求本地文件经过系统重启仍可恢复，需要另外按平台和文件系统契约请求 `fsync` 等持久化操作；`finish` 和 `close` 本身都不报告这项持久化保证。若目标是 HTTP 响应或对象存储，使用相应协议/SDK 的确认定义。对客户端下载而言，服务器本地响应流完成不等于客户端应用收到并保存了全部字节。

取消与失败走另一条路径。`pipeline(..., { signal })` 在信号触发时销毁仍参与管线的流，并以 `AbortError` 拒绝；这会停止继续沿流发送数据，但不会撤回已交给文件系统或远端的字节，也不会自动取消不属于流的数据库请求。生成器会在 `finally` 调用并等待自己拥有的游标 `close()`；若取消时它正等待 `cursor.next()`，而驱动不支持取消，只有等该查询结束，代码才能检查 signal 并运行 `finally`。等待 `close()` 返回本身不证明游标/连接已成功释放；owner 仍要按 driver 的结果确认状态，不能在 pending query 期间提前归还连接。

本例把同一个 signal 传给 `pipeline()`，并在 `await cursor.next()` 之后检查它。模拟 `close()` 会成功；若真实 driver 的关闭操作失败，本例的 `finally` 只保证调用并等待它，不把 `AbortError` 分支当成成功释放的证明。`--abort-replay` 用一个真实挂起的 `next()` 重放在途取消：20 ms 时触发 abort，100 ms 时释放模拟查询；观察到生成器的 `finally` 和 `pipeline()` 的 `AbortError` 都在查询释放后出现。真实数据库驱动是否有可用的取消 API、取消何时确认，要以该驱动的契约为准。

文件写流遇到取消或错误时，已写出的部分内容仍可能留在文件中。本例先用 `mkdtemp()` 创建本次运行独占的临时目录，再写入其中；只在管线 Promise 拒绝且其流已停止后删除这个目录，正常完成则打印并保留产物路径。这里没有实现重命名或业务发布。本地文件使用本次 attempt 独占的临时路径；数据处理和写入完成后，是否通过 `rename` 发布由作业协调者裁决。生产对象存储则使用本次 attempt 独占的私有对象键；完整上传后，仍须由当前 attempt 在数据库中按条件提交结果引用并将 job 置为 `succeeded`，对象上传成功本身不等于任务已完成。取消/普通错误时的本地清理不会覆盖进程崩溃；强杀也可能留下本例的本地临时目录或生产上传的私有对象。生产环境中遗留的私有对象应由独立回收责任方处理：只有 attempt 已被接管或 job 已终结、持久状态确认没有结果引用，且有界的上传时限与额外安全宽限期都已过去，才可删除，见[工作进程重试怎样避免旧结果覆盖新结果](#%E5%B7%A5%E4%BD%9C%E8%BF%9B%E7%A8%8B%E9%87%8D%E8%AF%95%E6%80%8E%E6%A0%B7%E9%81%BF%E5%85%8D%E6%97%A7%E7%BB%93%E6%9E%9C%E8%A6%86%E7%9B%96%E6%96%B0%E7%BB%93%E6%9E%9C%EF%BC%9F)。若一次远端写入结果未知，不能因本地 Promise 被取消就假设远端未生效；要用专属对象键、幂等标识或服务端状态查询来确认。已持久接受的 acct-17 job 也不应仅因最初 HTTP 请求断开就自动取消。作业取消与发布竞争的顺序见[何时选线程、进程或异步 I/O？](#20.%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)，HTTP 服务在 SIGTERM 下如何等待流和工作退出见[Node.js 服务如何排空并关闭？](#24.%20Node.js%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E6%8E%92%E7%A9%BA%E5%B9%B6%E5%85%B3%E9%97%AD%EF%BC%9F)。

**接下来：** 这章跟踪一条流内部的缓冲、收尾和清理；HTTP 请求、worker 和持久队列的并发上限见[如何估算并限制异步工作管线？](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)。

> [!info]- 来源
> - `Writable.write()` 返回 `false` 后停止写到 `'drain'`；`highWaterMark` 是阈值；buffering 对象/字节/字符串单位；每种 stream 状态与背压说明：[Node.js v26.13.1, Stream, Buffering 与 Writable streams](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#buffering)、[`write()`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#writablewritechunk-encoding-callback)、[`drain`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#event-drain)，2026-11-12 核对。
> - `pipeline()` 的 Promise、AbortSignal 销毁流、错误关闭管线；流 API 不包括它们外部的数据库请求：[Node.js v26.13.1, Stream, Promises API](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#streams-promises-api)，2026-11-12 核对。
> - `Readable.from()` 的输入、对象模式和 `end`；Transform 可能零到多个输出块，结束时可用 `_flush()` 生成尾块；Writable `finish` 与底层资源 `close`：[Node.js v26.13.1, Stream](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#streamreadablefromiterable-options)、[`end`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#event-end)、[`finish`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#event-finish)、[`close`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#event-close)、[`_flush()`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#transform_flushcallback)，2026-11-12 核对。
> - gzip 是基于 Node stream 的 Transform；非同步 zlib API 用 Node 内部 threadpool；关闭/结束压缩流完成当前 gzip 成员，不应把中间 `flush()` 与最终完成混为一谈：[Node.js v26.13.1, Zlib, Compressing or decompressing streams](https://nodejs.org/download/release/v26.13.1/docs/api/zlib.html#zlib)、[Threadpool usage and performance considerations](https://nodejs.org/download/release/v26.13.1/docs/api/zlib.html#threadpool-usage-and-performance-considerations)、[Flushing](https://nodejs.org/download/release/v26.13.1/docs/api/zlib.html#flushing)，2026-11-12 核对。
> - `mkdtemp()` 建立唯一临时目录；本地文件流默认的描述符自动关闭、`fs.rm()` 和 `FileHandle.sync()` 的操作系统/设备特定语义：[Node.js v26.13.1, File system, `fs.mkdtemp()`](https://nodejs.org/download/release/v26.13.1/docs/api/fs.html#fspromisesmkdtempprefix-options)、[`fs.createWriteStream()`](https://nodejs.org/download/release/v26.13.1/docs/api/fs.html#fscreatewritestreampath-options)、[`fs.rm()`](https://nodejs.org/download/release/v26.13.1/docs/api/fs.html#fsrmpath-options-callback)、[`filehandle.sync()`](https://nodejs.org/download/release/v26.13.1/docs/api/fs.html#filehandlesync)，2026-11-12 核对。
> - 取消生成器中外部 `cursor.next()` 的完成等待是对本页代码的实际运行观察，不推广到任一数据库驱动；真实驱动取消契约未在本例测试。
## 24. Node.js 服务如何排空并关闭？

**案例接续 acct-17：** 报表服务收到 `SIGTERM` 时，可能正把账户活动报表行流给一个 HTTP 响应，也可能有已经持久接受、由队列拥有的报表作业。两者的所有者不同：请求流可以在请求取消后结束；持久作业不能只因客户端断开而被撤销。本页的小型回放只模拟三条教学报表行直接流向 HTTP 响应，聚焦服务关停；它不冒充真实数据库、worker 或作业队列。持久作业的停止与发布边界会单独对照前两章。

![SIGTERM 后同步关闸并停止接收；并行等待 HTTP 关闭与请求工作结算，内部 deadline 通知取消后仍须等待清理；supervisor 自己的硬截止覆盖整个关停过程，届时进程仍未退出才会被强停](../../engineering-foundations/backend/resources/node-service-shutdown-lifecycle.svg)

### 为什么要先拒绝工作再关闭连接？

关停信号到达后，先在本进程内同步设 `draining = true`，再把 readiness（就绪状态）标为 false。负载均衡器或编排器收到不就绪状态需要时间；因此 handler 仍要在开始新报表或副作用之前检查 draining。尚在 keep-alive 连接上的新请求也可能到达，直接拒绝并回 `503`、`Connection: close`。之后调用 `server.close()` 停止接新连接；Node.js v19 起它也会关闭调用时的空闲连接。已有活动响应可以继续写完。本页回放还在应用 handler 结束后调用 `server.closeIdleConnections()`，主动收掉刚变空闲的 keep-alive 连接，以满足本例的关停时间预算；这不是说每个 Node.js v19+ 服务都必须额外调用它。

HTTP Server 的关闭回调只说明它拥有的普通 HTTP 连接已经收尾，不证明已启动的 handler、数据库游标、worker、文件写入或后台任务都停下。相反，deadline 时 `server.closeAllConnections()` 可以强制关闭 HTTP(S) 连接，却不会自动取消 handler 正在等的查询或 CPU 工作。服务要分别等待 HTTP 关闭与应用任务集合归零；若服务还提供 WebSocket 或 HTTP/2，应由对应协议的 server / session owner 停止接收、关闭会话并确认结束；不能只看普通 HTTP Server 回调。

下面的精简脚本把教学用 `acct-17` 三行 CSV 直接流给当前客户端。生成器、流管线和请求响应的完成/取消关系沿用 [Node.js 流如何传播背压？](#23.%20Node.js%20%E6%B5%81%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%E8%83%8C%E5%8E%8B%EF%BC%9F) 的说明。脚本默认每行延迟 100 ms；本地 deadline 回放用 --slow 改为 600 ms。两者都用可取消 timer 代替数据库查询，不代表真实查询耗时；真实驱动若不支持取消，pending 查询完成前仍不能关闭它的连接池。

> [!example]- 可运行的关停重放
>
> ~~~javascript
> // 保存为 shutdown-demo.cjs；使用 Node.js v26.13.0 运行
> const http = require('node:http');
> const { Readable } = require('node:stream');
> const { pipeline } = require('node:stream/promises');
> const { setTimeout: sleep } = require('node:timers/promises');
>
> const rowDelayMs = process.argv.includes('--slow') ? 600 : 100;
> const rows = [
>   'event-1,acct-17,12',
>   'event-2,acct-17,8',
>   'event-3,acct-17,-2',
> ];
> const inFlight = new Set();
> const requestControllers = new Set();
> let draining = false;
> let shutdownPromise;
>
> function track(promise) {
>   inFlight.add(promise);
>   promise.then(
>     () => inFlight.delete(promise),
>     () => inFlight.delete(promise),
>   );
>   return promise;
> }
>
> async function waitForInFlight() {
>   while (inFlight.size > 0) {
>     await Promise.allSettled([...inFlight]);
>   }
> }
>
> async function* acct17Csv(signal) {
>   try {
>     yield 'id,accountId,amount\n';
>     for (const row of rows) {
>       await sleep(rowDelayMs, undefined, { signal });
>       signal.throwIfAborted();
>       yield row + '\n';
>     }
>   } finally {
>     console.log('report source cleanup complete');
>   }
> }
>
> async function handleRequest(request, response) {
>   if (draining) {
>     response.writeHead(503, { Connection: 'close' });
>     response.end('service draining');
>     return;
>   }
>   if (request.method !== 'GET' || request.url !== '/reports/acct-17.csv') {
>     response.writeHead(404, { Connection: 'close' });
>     response.end('not found');
>     return;
>   }
>
>   const controller = new AbortController();
>   requestControllers.add(controller);
>   const abortOnPrematureClose = () => {
>     if (!response.writableFinished) {
>       controller.abort(new Error('client disconnected'));
>     }
>   };
>   response.once('close', abortOnPrematureClose);
>
>   try {
>     response.writeHead(200, { 'Content-Type': 'text/csv; charset=utf-8' });
>     await pipeline(
>       Readable.from(acct17Csv(controller.signal), { objectMode: false }),
>       response,
>       { signal: controller.signal },
>     );
>   } catch (error) {
>     const cancelledClose = controller.signal.aborted && error.code === 'ERR_STREAM_PREMATURE_CLOSE';
>     if (error.name !== 'AbortError' && !cancelledClose) throw error;
>     console.log('report response stopped:', error.message);
>   } finally {
>     response.off('close', abortOnPrematureClose);
>     requestControllers.delete(controller);
>   }
> }
>
> const server = http.createServer((request, response) => {
>   const task = track(handleRequest(request, response));
>   task.catch(error => {
>     console.error('request failed:', error);
>     process.exitCode = 1;
>     if (!response.destroyed) response.destroy(error);
>   });
> });
>
> function markReadiness(ready) {
>   console.log('ready:', ready);
> }
>
> async function closeOwnedResources() {
>   // 本回放只有可取消 timer 与日志。生产还须逐个等待资源 owner 确认释放成功，不能把 handler Promise settled 当成释放证明。
>   console.log('resource cleanup complete');
> }
>
> const listening = new Promise((resolve, reject) => {
>   const onListening = () => {
>     server.off('error', onListenError);
>     resolve();
>   };
>   const onListenError = error => {
>     server.off('listening', onListening);
>     reject(error);
>   };
>   server.once('listening', onListening);
>   server.once('error', onListenError);
> });
> listening.catch(error => {
>   console.error('server startup failed:', error);
>   process.exitCode = 1;
> }); // 若绑定失败，保留拒绝给 shutdown 使用并记录启动失败。
> server.listen(0, '127.0.0.1', () => {
>   if (!draining) markReadiness(true);
>   console.log('listening:', server.address().port);
> });
>
> function shutdown(signal) {
>   if (shutdownPromise) return shutdownPromise;
>   draining = true;
>   markReadiness(false);
>   console.log('received:', signal);
>
>   const deadline = setTimeout(() => {
>     console.log('deadline: abort in-flight request streams and close HTTP connections');
>     for (const controller of requestControllers) {
>       controller.abort(new Error('shutdown deadline'));
>     }
>     server.closeAllConnections();
>   }, 1_000);
>
>   const closeHttpServer = async () => {
>     await listening;
>     return new Promise((resolve, reject) => {
>       server.close(error => error ? reject(error) : resolve());
>     });
>   };
>
>   shutdownPromise = (async () => {
>     try {
>       const serverClosed = closeHttpServer();
>       const workResults = await Promise.allSettled([waitForInFlight()]);
>       server.closeIdleConnections(); // handler 结束后再关刚转为空闲的 keep-alive 连接。
>       const httpResults = await Promise.allSettled([serverClosed]);
>       const results = [...workResults, ...httpResults];
>       let failed = false;
>       // 这只证明本例的 HTTP 和 handler Promise 已结算，不证明任意资源 owner 已成功释放。
>       // fulfilled 表示两个关停等待都成功返回；handler 本身失败由 task.catch 记录。
>       const lifecycleWaitSucceeded = results.every(result => result.status === 'fulfilled');
>       for (const result of results) {
>         if (result.status === 'rejected') {
>           failed = true;
>           console.error('shutdown lifecycle failed:', result.reason);
>         }
>       }
>       if (!lifecycleWaitSucceeded) {
>         console.error('shutdown wait failed; cannot confirm HTTP closure or application wait, keep dependencies open');
>         process.exitCode = 1;
>         return;
>       }
>       clearTimeout(deadline); // HTTP 和应用等待条件都已结束；依赖清理另有 supervisor 硬截止。
>       try {
>         // 本例没有外部资源。生产应先核对各 owner 的释放结果；失败或未知时保留相关依赖。
>         await closeOwnedResources();
>       } catch (error) {
>         failed = true;
>         console.error('resource cleanup failed:', error);
>       }
>       if (failed) process.exitCode = 1;
>     } finally {
>       clearTimeout(deadline);
>     }
>   })();
>   return shutdownPromise;
> }
>
> function onShutdown(signal) {
>   shutdown(signal).catch(error => {
>     console.error('shutdown failed:', error);
>     process.exitCode = 1;
>   });
> }
>
> process.on('SIGTERM', onShutdown);
> process.on('SIGINT', onShutdown);
> ~~~

**本机回放（Node.js v26.13.0）：** 默认每行 100 ms 时，在首个响应块到达后发送 SIGTERM；客户端仍收到完整三行 CSV，生成器清理、HTTP 关闭和资源清理都在 1 秒 deadline 前完成，进程 exit code 为 0。使用 `--slow`（每行 600 ms）时，客户端只收到表头与 event-1；deadline 回调发出取消并强关 HTTP 连接，连接关闭后生成器执行 `finally`，管线以 `ERR_STREAM_PREMATURE_CLOSE` 结算，`inFlight` 中的 handler 随后全部结算并继续资源清理，进程仍以 0 退出。正常排空时，handler 集合归零后补调 `server.closeIdleConnections()`，HTTP close 回调随之完成；本机移除这次补调的对照中，正文虽已完整，HTTP 收尾仍等到了 1 秒 deadline。另对慢模式在首块后间隔 150 ms 发两次 SIGTERM：两次信号共用同一个 `shutdownPromise`，没有触发默认信号退出；deadline 后生成器与资源清理均有日志，最终 exit 0。


脚本将 HTTP handler 的**完整 Promise**登记到 `inFlight`，包含流结束和 `finally` 中移除请求控制器的步骤。正常写完时，响应结束后 handler Promise 才完成；随后补关刚转为空闲的 keep-alive 连接，并等待 HTTP close 回调。客户端提前断开时，响应 `close` 会触发该请求取消。两项生命周期都已结算后才清理依赖。deadline 到达时，脚本先对请求流发协作取消，再关闭 HTTP(S) 连接；取消可以令本例中的 timer 与生成器停止；deadline 回放里，先通知取消并强关 HTTP 连接，随后生成器运行 `finally`；管线以 `ERR_STREAM_PREMATURE_CLOSE` 结算，`inFlight` 集合归零后才清理依赖。代码仅在本请求 signal 已触发时把它当作预期停止。它不能保证真实数据库、文件系统或第三方 API 已撤销在途操作。`server.closeAllConnections()` 放在 `server.close()` 之后调用，以免在关停期间另有连接进入。

### 哪些完成状态允许关闭资源？

“收到信号”“连接断了”和“任务结束”是不同事实。示例里的 `lifecycleWaitSucceeded` 表示 `server.close()` 回调与 `waitForInFlight()` 两项等待都成功返回。`waitForInFlight()` 等到完整 handler Promise 结算，但不要求业务 handler 本身成功；`task.catch` 会记失败与退出码。本例没有真实数据库池或 worker，所以这个等待结果不能当作生产资源已释放的证据。生产还要等每个资源 owner 确认成功释放；清理失败或状态未知时，不关闭仍可能被使用的那项依赖。

| 资源或副作用 | 等待到什么状态 | 不能据此推出什么 |
| --- | --- | --- |
| HTTP listener 和普通 HTTP(S) 连接 | `server.close()` 的回调；启动 `server.close()` 后，超时强制路径可不等回调就调用 `closeAllConnections()` | 被强制关掉响应，不代表 handler 内的 JS、查询或 worker 已结束；若还提供 WebSocket 或 HTTP/2，须由相应 server / session owner 关闭并确认 |
| 请求内 CSV 流 | `pipeline()` fulfilled 表示流正常结束；reject 表示失败/取消路径已由流管线结算，本例生成器也先完成 `finally` | 部分响应字节不能撤回，也不能证明客户端已经完整读取或保存正文 |
| 数据库游标和连接 | 等 pending `next()` 完成或驱动的取消确认，再关闭游标并释放连接 | Node 的 `AbortSignal` 不会自动变成任意驱动的取消请求 |
| worker 与批次 | 当前消息、写出、尾块或停止确认到达；压缩状态清除，槽按所有权规则归还 | 发出取消信号或关闭 HTTP socket 不等于 worker 已停 |
| 临时文件与发布 | 文件流结束并关闭；若进入发布，则以 `rename` 等提交操作的真实成功/失败结果为准 | 写入 Promise 被本地取消不能证明文件或远端服务没有副作用 |
| 已持久受理的 acct-17 job | 队列授予本次执行的 lease（租约）；job owner 停止接新 job，并让当前 attempt 达到完成状态，或清理后安全归还租约 / 让队列重试 | API 客户端断开不撤销已持久接受的 job |

前两章中的 worker 导出把一个作业固定到 worker，逐批读、压缩和写出；EOF 后还要等压缩器发送全部尾块、写入方关闭临时文件。服务收到关停时，先停止队列继续领取新作业。当前 attempt 可在预算内完成；若策略要求在 deadline 取消，则由同一 job 协调者停止拉取、取消查询并等待查询结束、worker 的停止/收尾确认与已提交写入，再关闭并清理本 attempt 的临时文件，最后安全归还本次执行的租约。它不能把请求连接关闭误记成 job 已取消。

取消与发布正在同一个 job 协调者里竞争时，仍按既定顺序裁决：若 job 还在 `running` 且取消先被接受，不提交文件发布；若先进入 `publishing` 并提交 rename，就等待真实成功或失败，不能让晚到的本地取消覆盖结果。若进程在提交后被硬杀，结果可能未知；重启后按 job ID、专属目标路径和持久化状态核对或幂等重试，不要凭 handler 退出推断“肯定没发布”。客户端已收到部分流响应也不能回滚先前已提交的数据库或对象存储副作用。

### deadline 与 supervisor 如何配合？

示例的 1 秒 deadline 与 timer 延迟只为回放不同分支：默认每行 100 ms 让在途响应有机会正常排空，`--slow` 的每行 600 ms 会进入 deadline 取消分支。它们不是生产 SLA，也不保证真实操作在这一秒内终止。真实服务要为停止接单、协作取消、查询/worker 清理、文件关闭和资源池关闭保留时间。内部 deadline 应早于部署管理器的硬终止时间，并留出根据实际清理时长确定的余量。内部 timer 依赖事件循环运行；若 JavaScript 同步代码长时间阻塞，回调也不能准时执行。最外层 supervisor 自己的硬截止才会强停仍未退出的进程，图中的 SIGKILL 指这个外部动作。

在支持这些信号的 POSIX 部署上，注册 `SIGTERM` 或 `SIGINT` listener 会移除相应默认退出行为；应用要自己走完关停路径，不要在 cleanup 前直接调用 `process.exit()`。脚本用 `process.exitCode` 记录失败，并让已关闭的 handle 自然结束进程。deadline timer 保持引用，避免事件循环空闲时在它执行前退出。若不响应取消的请求仍持有数据库连接，等待会继续；不能为了让进程按时退出而提前关闭正在使用的依赖。最外层 supervisor 到硬截止后可以强制杀进程，但强杀不能替代持久任务恢复与未知副作用的对账。

PM2 对 stop、restart 和 reload 默认先发 `SIGINT`；可改 `PM2_KILL_SIGNAL`。`kill_timeout` 默认 1600 ms，届满后发 `SIGKILL`；生产配置要把应用自己的 drain deadline 和清理余量放在这个截止之前，或同步调整 PM2 配置。若服务还提供 WebSocket 或 HTTP/2，另由对应 server / session owner 停止接收、关闭并确认会话结束；HTTP server 的 `closeAllConnections()` 不会替这些协议连接完成应用清理。

**接下来：** HTTP server 的 connection 生命周期与请求/任务所有权在此收束；账户报表何时算持久完成，以及重试如何查询未知结果，见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info]- 来源
> - `server.close()` 停止接受新连接，并从 Node.js v19 起关闭调用时的空闲连接；`server.closeIdleConnections()` 可在活动 handler 完成后再次关闭转为空闲的 keep-alive 连接；关闭回调与连接结束：[Node.js v26.13.1, HTTP, `server.close()`](https://nodejs.org/download/release/v26.13.1/docs/api/http.html#serverclosecallback)、[`server.closeIdleConnections()`](https://nodejs.org/download/release/v26.13.1/docs/api/http.html#servercloseidleconnections)，2026-11-12 核对。
> - `server.closeAllConnections()` 会关闭现有 HTTP(S) 活动连接，建议在 `server.close()` 后调用以避免竞态；不负责关闭 WebSocket 等其它协议的 socket；HTTP/2 会话也应由自己的 session owner 收尾：[Node.js v26.13.1, HTTP, `server.closeAllConnections()`](https://nodejs.org/download/release/v26.13.1/docs/api/http.html#servercloseallconnections)，2026-11-12 核对。
> - `SIGTERM` / `SIGINT` listener 会移除相应默认 handler；可监听 signal 并自行决定清理何时完成：[Node.js v26.13.1, Process, Signal events](https://nodejs.org/download/release/v26.13.1/docs/api/process.html#signal-events)，2026-11-12 核对。
> - 活动 `Timeout` 默认保持事件循环运行；`unref()` 后在无其他活动时进程可能先退出：[Node.js v26.13.1, Timers, `timeout.unref()`](https://nodejs.org/download/release/v26.13.1/docs/api/timers.html#timeoutunref)，2026-11-12 核对。
> - 带 `AbortSignal` 的 `pipeline()` 会销毁管线流并以 `AbortError` 结束；只有实际接收该 signal 的异步生成器操作才会协作取消：[Node.js v26.13.1, Stream, Promises API](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#streams-promises-api)，2026-11-12 核对。
> - PM2 默认 SIGINT，支持将信号改为 SIGTERM，默认 `kill_timeout` 1.6 秒后发 SIGKILL：[PM2, Graceful Start/Shutdown, Signals flow](https://pm2.keymetrics.io/docs/usage/signals-clean-restart/)，2026-11-12 核对。
> - 持久 job 的逐批确认、EOF 尾块、running/publishing 取消竞争与本地重命名边界：见[何时选线程、进程或异步 I/O？](#20.%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)与[Node.js 如何在事件循环、工作线程与进程之间调度工作？](#21.%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。
## 25. Python 的值、迭代器与资源生命周期如何工作？

**案例：** 一个报表工作进程（worker）读取合成 comma-separated values（CSV，逗号分隔值）文件，把状态为 `ready` 且数量为正的事件加入 `Report("November", source_rows)`。第一条事件的引号字段跨两行；最后一条事件含无效状态。我们要追踪名字指向哪些对象、修改会不会共享、生成器何时交付每行，以及坏记录出现后哪些状态保留、哪些资源关闭。

![报表处理从 CSV 记录到部分结果和资源清理的流程](../../engineering-foundations/backend/resources/python-report-pipeline.svg)

图中的 `for` 循环每次请求生成器的下一个产出时才推进生成器。前几行已经加入 `report.rows` 后，后续坏记录仍可抛出异常；异常离开 `with` 块会关闭文件并清理临时目录，却不会撤销已修改的 Python 对象。

本例的 Python 代码块按页面顺序在同一进程执行，后面的代码沿用前面创建的 `Report` 实例和列表；解析阶段会把 `evt-1`、`evt-3` 加入该列表。

### 创建 Report 时，名字绑定到什么？

Python 中数据由对象表示。每个对象有 identity（身份）、type（类型）和值。身份在对象存续期间不变；`is` 比较是否为同一对象，`id(obj)` 返回代表身份的整数。类型决定对象支持哪些操作以及值的范围；它不像列表内容那样可随意原地修改，但也不能说成绝对不可改变：在 CPython 3.11.13 中，`class A: pass` 和 `class B: pass` 这两个普通类的实例布局兼容。对 `obj = A()` 先保存 `saved_id = id(obj)`，再执行 `obj.__class__ = B`，会得到 `type(obj) is B` 且 `id(obj) == saved_id`。这个受限赋值不会替换对象本身。对象结束生命周期后，另一个对象可能复用同一个 `id()`，所以它不是跨运行或长期保存的业务标识。`==` 比较值是否相等，具体相等规则也可由类型定义。

名字只是命名空间（namespace）中的绑定，执行赋值通常是让名字指向某个已有对象，并不复制对象；多个名称指向同一对象也称 aliasing（别名）。普通类调用通常先由 `__new__` 取得实例，再由 `__init__` 初始化该实例；`__init__` 本身不负责创建新实例。下面的 `Report` 把标题和传入的列表存为实例属性：

~~~python
class Report:
    def __init__(self, title: str, rows: list[dict[str, object]]) -> None:
        self.title = title
        self.rows = rows

source_rows = []
report = Report("November", source_rows)
rows_alias = report.rows
print(report.rows is source_rows, rows_alias is source_rows)
~~~

输出是 `True True`：`report` 指向新建的 `Report` 实例，而 `source_rows`、`report.rows` 和 `rows_alias` 指向同一个列表对象。`self.rows = rows` 只保存对列表的引用，没有复制列表或其中的对象。实例的 `__dict__` 保存这些普通属性绑定；本例暂时没有 descriptor（描述符）截获 `title` 的读写，下一篇会在相同 `Report` 案例中加入这层机制。

### 生成器如何把一条记录交给报表？

可迭代对象（iterable）能提供迭代器；迭代器（iterator）逐次返回值，结束时以 `StopIteration` 表示没有下一值，`for` 会处理这个结束信号。生成器函数包含 `yield`：调用它只返回一个生成器对象，函数体要等到 `for` 循环或 `next()` 请求下一值才继续执行。`list(generator)` 则会立即消费后续产出并存入列表；它会持续推进，直至耗尽或异常中断，不再保留逐条消费的内存优势。生成器让处理方不必先把整个输入读成列表；但已经产生的副作用不会因之后出错而自动回滚。

下面的代码块接在上段之后。生成器检查 CSV 表头、列数、状态和整数数量，把 `tags` 拆成列表，只交付 `status == "ready"` 且 `count > 0` 的事件；合法的 `queued` 事件仍会被过滤掉。`csv.reader.line_num` 表示读过的源文件物理行数；一条引号字段跨多行的 CSV 记录会使它大于记录序号。文本文件使用 `newline=""`，让 CSV 模块按自己的规则处理换行。

~~~python
import csv
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TextIO

def ready_rows(source: TextIO) -> Iterator[dict[str, object]]:
    reader = csv.reader(source)
    try:
        headers = next(reader)
    except StopIteration:
        return

    expected = ["id", "status", "count", "tags", "note"]
    if headers != expected:
        raise ValueError("unexpected CSV header")

    for values in reader:
        line_number = reader.line_num
        if len(values) != len(headers):
            raise ValueError(f"CSV physical line {line_number}: wrong column count")

        fields = dict(zip(headers, values))
        status = fields["status"]
        if status not in {"ready", "queued"}:
            raise ValueError(
                f"CSV physical line {line_number}: unknown status {status!r}"
            )
        try:
            count = int(fields["count"])
        except ValueError as error:
            raise ValueError(
                f"CSV physical line {line_number}: count must be an integer"
            ) from error

        row = {**fields, "count": count, "tags": fields["tags"].split("|")}
        if status == "ready" and count > 0:
            yield row

CSV_TEXT = (
    "id,status,count,tags,note\n"
    'evt-1,ready,3,new|priority,"account\n'
    'export"\n'
    "evt-2,queued,1,backlog,skip\n"
    "evt-3,ready,2,review,year-end\n"
    "evt-4,unknown,1,bad,invalid\n"
)

source = None
path = None
try:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "events.csv"
        path.write_text(CSV_TEXT, encoding="utf-8")
        with path.open(encoding="utf-8", newline="") as source:
            for row in ready_rows(source):
                report.rows.append(row)
except ValueError as error:
    print(f"Rejected input: {error}")

print(source.closed, path.exists())
print([row["id"] for row in report.rows])
print(repr(report.rows[0]["note"]))
~~~

本机以 CPython 3.11.13 执行上述代码块，解析阶段输出：

~~~text
Rejected input: CSV physical line 6: unknown status 'unknown'
True False
['evt-1', 'evt-3']
'account\nexport'
~~~

每次 `for row in ready_rows(source)` 请求生成器的下一个产出，都会让它开始运行或从上次 `yield` 处恢复；控制顺序是外层 `for` 请求 `ready_rows`，生成器再向 `csv.reader` 取一条 CSV 记录。第一次请求先读表头，再取到跨物理行 2–3 的 `evt-1`；`note` 的值是含换行的 `'account\nexport'`，事件满足 `status == "ready" and count > 0`，所以生成器 `yield` 它，循环追加到报表。第二次请求从上次 `yield` 处恢复，先取得合法但状态为 `queued` 的 `evt-2`，条件不成立，生成器继续向 `csv.reader` 取数，再 `yield` 满足条件的 `evt-3`。第三次请求恢复后读到物理行 6 的 `evt-4`，状态 `unknown` 不合法，于是抛出异常而不再产出值。

生成器只借用调用方已打开的 `source`，它不负责打开或关闭流。在本例中，异常从循环传播后，两个上下文管理器按嵌套顺序退出：内层文件上下文关闭文件，外层 `TemporaryDirectory` 删除路径，然后异常才被 `except` 捕获。打印的 `True False` 分别是 `source.closed` 和 `path.exists()`：`source` 这个名称仍指向已关闭的流对象，`path` 仍是一个 `Path` 值，但它所指位置已不存在。外部的 `report` 仍引用原列表，已经追加的两条记录不会随资源退出而撤销。若结果必须全有或全无，应先验证并暂存，再在合适的事务边界提交；`with` 调用退出协议，是否回滚由上下文管理器实现决定；这里的文件和临时目录清理不会回滚列表修改。自定义 context manager 的 `__exit__` 还可以通过返回真值抑制块内异常，或在清理失败时抛出新异常。因此，判断错误能否到达外层 `except`，也要检查退出协议；本例两个管理器在成功清理后让原异常继续传播。

### 改对象和改名字，影响范围有什么不同？

现在 `report.rows` 已含 `evt-1`、`evt-3`。对象图只展开第一条记录：实例的 `rows` 属性、`source_rows` 和 `rows_alias` 三条引用路径指向同一行列表；列表里的事件字典又指向一只标签列表。

![Report 实例、行列表、事件字典与标签列表的对象引用关系](../../engineering-foundations/backend/resources/python-object-aliases.svg)

list 和 dict 是可变对象，原地追加或更新会改变同一对象的值；给名字重新赋值则只改变该名字的绑定。浅拷贝（shallow copy）只创建最外层容器，其成员引用仍可能共享：

~~~python
rows_alias[0]["tags"].append("reviewed")
copied_rows = report.rows.copy()
copied_rows[0]["tags"].append("shared")
print(report.rows[0]["tags"])

rows_alias = []
print(len(report.rows))
~~~

输出依次是 `['new', 'priority', 'reviewed', 'shared']` 和 `2`。第一行通过别名修改原列表中第一条事件的标签。`copy()` 创建另一只行列表，但 `copied_rows[0]` 和 `report.rows[0]` 仍指向同一个事件字典，字典中的 `tags` 也仍是同一列表；所以通过复制列表再修改嵌套标签，原报表也能观察到变化。最后把 `rows_alias` 改绑到新列表，不会替 `report.rows` 重新绑定。若需要独立修改标签，应重建对应的事件字典和 `tags` 列表；只有确实需要隔离整棵对象图时，再考虑 `deepcopy`（深拷贝）。

函数调用也会为形参建立新的局部名称，并让它们引用传入的对象。函数原地修改形参所指的列表，调用方可见；函数把形参改绑到另一只列表，不会改掉调用方的名称。另一个常见共享点是默认值：默认表达式在执行 `def` 时求值一次，后续调用会继续使用同一对象。

~~~python
def unsafe_add(item, items=[]):
    items.append(item)
    return items

print(unsafe_add("first"))
print(unsafe_add("second"))

def add(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

print(add("first"))
print(add("second"))
~~~

前两次 `unsafe_add` 共用默认列表，结果依次是 `['first']` 和 `['first', 'second']`。`add` 在每次未提供列表时新建一只，因此结果分别是 `['first']` 和 `['second']`。如果 `None` 也是有意义的输入，再用独立 sentinel（哨兵值）表示“未提供”。

不可变也要按对象边界理解：字符串不能原地改写；元组不能替换它的成员，但成员若是列表，仍可修改那只列表。`set` 保存不重复元素但没有序列索引；`dict` 将键映射到值，插入顺序从 Python 3.7 起是语言保证（CPython 3.6 中只是实现细节）。这些性质都不意味着名称本身不可重新绑定。

### 类型提示和虚拟环境能保证什么？

type hint（类型提示）中的 `TextIO`、`Iterator` 和返回类型帮助读者、IDE 与静态类型检查器理解预期形状；Python 默认不会因为实际对象不符合注解而拒绝它。示例中的输入验证由表头检查、状态判断和 `int()` 转换执行，而不是由类型注解执行。文件也不应等垃圾回收时才关闭；`with` 语句使用上下文管理器（context manager）在确定的控制流边界执行关闭。

这份示例只用 Python 标准库，可直接保存为文件后运行。虚拟环境（virtual environment）以创建命令所调用的基础 Python 为基准，并隔离项目安装的包；它不会替项目安装一个独立于基础解释器的 Python 版本。创建时选定解释器，再用该环境中的 Python 运行程序与安装依赖，例如：

~~~sh
python3.11 -m venv .venv
.venv/bin/python python-fundamentals-example.py
~~~

项目需要第三方依赖时，也使用同一个环境的解释器运行 `-m pip`，例如 `.venv/bin/python -m pip install httpx`；这样安装位置与程序运行环境一致。上面的 `.venv/bin/` 是 POSIX 环境路径。

本章先用普通实例属性建立 `Report` 对象和列表的状态。下一篇沿用 `November` 报表及其事件数据，把 `title` 改成会验证输入的数据描述符，并说明属性读取、实例字典、绑定方法和多继承如何共同决定结果：[Python 实例属性何时来自对象字典，何时变成描述符或绑定方法？](#26.%20Python%20%E5%AE%9E%E4%BE%8B%E5%B1%9E%E6%80%A7%E4%BD%95%E6%97%B6%E6%9D%A5%E8%87%AA%E5%AF%B9%E8%B1%A1%E5%AD%97%E5%85%B8%EF%BC%8C%E4%BD%95%E6%97%B6%E5%8F%98%E6%88%90%E6%8F%8F%E8%BF%B0%E7%AC%A6%E6%88%96%E7%BB%91%E5%AE%9A%E6%96%B9%E6%B3%95%EF%BC%9F)。异步接口如何让同一类报表读取跨过 I/O 等待，以及资源需要活到什么时候，见[异步 FastAPI 接口为什么仍会阻塞？](#27.%20%E5%BC%82%E6%AD%A5%20FastAPI%20%E6%8E%A5%E5%8F%A3%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BB%8D%E4%BC%9A%E9%98%BB%E5%A1%9E%EF%BC%9F)。

> [!info]- 来源
> - 对象身份、类型、可变性、不可变容器中的可变成员，以及不要依赖对象立即终结：[Python 3.15.2 Language Reference, Data model §3.1](https://docs.python.org/3.15/reference/datamodel.html#objects-values-and-types)，核对于 2026-11-12。受限 `__class__` 赋值须兼容 `__slots__`：[Python 3.15.2 Language Reference, `__slots__`](https://docs.python.org/3.15/reference/datamodel.html#object.__slots__)；固定实现 CPython 3.11.13 的兼容性检查和类型指针替换：[Objects/typeobject.c `compatible_for_assignment` / `object_set_class`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L4715-L4869)。`id()` 在对象生命周期内唯一、恒定，生命周期不重叠的对象可能复用该值：[Python 3.15.2 Built-in Functions, `id`](https://docs.python.org/3.15/library/functions.html#id)；CPython 3.11.13 中它由对象指针转成整数：[Python/bltinmodule.c `builtin_id`](https://github.com/python/cpython/blob/v3.11.13/Python/bltinmodule.c#L1197-L1225)。
> - 类调用通常经 `__new__` 取得实例并由 `__init__` 初始化；名字可别名引用同一对象：[Python 3.15.2 Language Reference, Classes / Basic customization](https://docs.python.org/3.15/reference/datamodel.html#classes)，[Python 3.15.2 Tutorial, Classes §9.1](https://docs.python.org/3.15/tutorial/classes.html#a-word-about-names-and-objects)，核对于 2026-11-12。
> - 字典插入顺序从 3.7 起是语言保证，CPython 3.6 中是实现细节：[Python 3.15.2 Built-in Types, Dictionary](https://docs.python.org/3.15/library/stdtypes.html#dict)，核对于 2026-11-12。
> - 函数默认参数在函数定义时求值：[Python 3.15.2 Tutorial, Default Argument Values](https://docs.python.org/3.15/tutorial/controlflow.html#default-argument-values)，核对于 2026-11-12。
> - 生成器函数、`yield` 与按需迭代：[Python 3.15.2 Language Reference, Yield expressions](https://docs.python.org/3.15/reference/expressions.html#yield-expressions)，核对于 2026-11-12。
> - 多行 CSV 记录与 `reader.line_num` 的物理行计数、打开文件时的 `newline=""`：[Python 3.15.2 `csv` library](https://docs.python.org/3.15/library/csv.html#csv.csvreader.line_num)，本例于 CPython 3.11.13 重放。
> - `with` 语句的进入、退出和异常传播：[Python 3.15.2 Language Reference, The with statement](https://docs.python.org/3.15/reference/compound_stmts.html#the-with-statement)；文件流作为上下文管理器在块退出时关闭：[Python 3.15.2 `io.IOBase`](https://docs.python.org/3.15/library/io.html#io.IOBase)；临时目录上下文退出时清理：[Python 3.15.2 `tempfile.TemporaryDirectory`](https://docs.python.org/3.15/library/tempfile.html#tempfile.TemporaryDirectory) 和固定实现 [CPython 3.11.13 `Lib/tempfile.py`](https://github.com/python/cpython/blob/v3.11.13/Lib/tempfile.py#L857-L949)，本例记录了实际资源状态。
> - Python 运行时默认不强制函数和变量注解：[Python 3.15.2 `typing`](https://docs.python.org/3.15/library/typing.html)，核对于 2026-11-12。
> - 虚拟环境隔离包安装位置，并由创建命令选定基础解释器：[Python 3.15.2 `venv`](https://docs.python.org/3.15/library/venv.html)，核对于 2026-11-12。
## 26. Python 实例属性何时来自对象字典，何时变成描述符或绑定方法？

**承接前篇：** [前篇](#25.%20Python%20%E7%9A%84%E5%80%BC%E3%80%81%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E8%B5%84%E6%BA%90%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E5%A6%82%E4%BD%95%E5%B7%A5%E4%BD%9C%EF%BC%9F)的 CSV worker 接受了 `evt-1` 与 `evt-3`，并沿共享标签列表把第一条记录改为 `['new', 'priority', 'reviewed', 'shared']`。本篇在独立代码中重建这两条记录；现在标题输入改成 `"  November  "`，要求读取得到规范化后的 `November`，空白标题则拒绝。我们还要解释普通类属性、描述符和实例字典同名时由谁响应，以及同一验证方法如何沿多继承顺序协作。

本篇只讨论普通类实例的显式读写，例如 `report.title`、`report.title = value` 和 `getattr(report, name)`。类对象本身的元类查找、特殊语法触发的隐式特殊方法查找，以及代理类的额外规则不属于这条路径。

方法解析顺序（method resolution order，MRO）是从当前类沿基类继续查找属性时使用的顺序。

![读取普通实例属性时从类 MRO、描述符和实例字典得到结果的分支](../../engineering-foundations/backend/resources/python-attribute-lookup.svg)

图的前半展示默认 `__getattribute__` 的查找链；当它以 `AttributeError` 结束，普通点号访问和两参数 `getattr()` 才进入末端的 `__getattr__` 回退。描述符 getter 自己抛出 `AttributeError` 也会进入该回退；若重写的 `__getattribute__` 抛出同一错误，也会走这条外层回退，详见下文。

### 为什么同名实例键不会取代标题验证器？

descriptor（描述符）是其类型定义了 `__get__`、`__set__` 或 `__delete__` 的对象。要让点号访问自动调用它，描述符对象必须作为属性放在类字典中，或被实例类型的某个基类继承；把描述符对象放进实例字典只会得到那个普通对象。

下面的 `NonEmptyText` 将公开的 `title` 管理在实例字典的 `_title` 键里。`__set_name__` 在类创建时收到它所属的类和属性名；`__get__` 在类访问时返回描述符本身，在实例访问时读存储键；`__set__` 把校验交给实例的 `validate_title` 协议，成功后才写入规范化值。

这个实现要求宿主实例有 `__dict__`，并提供 `validate_title`；后面的 `Report` 同时满足这两个前提。

~~~python
class NonEmptyText:
    def __set_name__(self, owner, name):
        self.public_name = name
        self.storage_name = "_" + name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return instance.__dict__[self.storage_name]
        except KeyError:
            raise AttributeError(self.public_name) from None

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError("title must be text")
        normalized = instance.validate_title(value)
        instance.__dict__[self.storage_name] = normalized
~~~

这个描述符定义了 `__get__` 和 `__set__`，所以它是 data descriptor（数据描述符）。读取时，若类 MRO 找到这样的候选，描述符 getter 会先于 `report.__dict__` 执行；赋值时，默认属性设置会先调用它的 `__set__`。因此，即使实例字典里也出现 `title` 键，普通的 `report.title` 仍由描述符决定。

以下类和对象继续使用前篇的 `Report` 与事件数据。`NonEmptyText.__set__` 调用 `report.validate_title`；该函数由类中的普通函数描述符绑定到当前实例，再通过 `super()` 进入审计、去空格和非空检查步骤。

~~~python
events = []

class FieldBase:
    def validate_title(self, value):
        events.append("FieldBase")
        if not value:
            raise ValueError("title must contain non-whitespace text")
        return value

class NormalizeMixin(FieldBase):
    def validate_title(self, value):
        events.append("NormalizeMixin.before")
        result = super().validate_title(value.strip())
        events.append("NormalizeMixin.after")
        return result

class AuditMixin(FieldBase):
    def validate_title(self, value):
        events.append("AuditMixin.before")
        result = super().validate_title(value)
        events.append("AuditMixin.after")
        return result

class Report(AuditMixin, NormalizeMixin):
    title = NonEmptyText()
    category = "monthly"

    def __init__(self, title, rows):
        self.title = title
        self.rows = rows

    def validate_title(self, value):
        events.append("Report.validate_title")
        return super().validate_title(value)

    def __getattr__(self, name):
        events.append(f"__getattr__({name})")
        if name == "row_count":
            return len(self.rows)
        raise AttributeError(name)

    def publish(self):
        return f"Published {self.title} ({len(self.rows)} events)"

source_rows = [
    {
        "id": "evt-1",
        "status": "ready",
        "count": 3,
        "tags": ["new", "priority", "reviewed", "shared"],
        "note": "account\nexport",
    },
    {
        "id": "evt-3",
        "status": "ready",
        "count": 2,
        "tags": ["review"],
        "note": "year-end",
    },
]
report = Report("  November  ", source_rows)
print(Report.title is vars(Report)["title"])
print(vars(Report)["title"].storage_name)
print(report.title, report.__dict__["_title"])
print([row["id"] for row in report.rows])
print(events)
~~~

输出为 `True`、`_title`、`November November`、`['evt-1', 'evt-3']`，校验轨迹为 `Report.validate_title → AuditMixin.before → NormalizeMixin.before → FieldBase → NormalizeMixin.after → AuditMixin.after`。赋值 `self.title = title` 不是直接把标题字符串放进 `report.__dict__`：它触发类上的数据描述符，空格先被去掉，随后 `FieldBase` 检查结果非空，最后才写入 `_title`。直接查看 `vars(Report)["title"]` 会取得描述符对象；`Report.title` 则通过类属性访问调用 `__get__(None, Report)`，本例同样返回它自身。

正常点号访问和直接改字典不是同一操作。下面先把一个同名键直接塞进实例字典，再通过语法赋值空白标题：

~~~python
report.__dict__["title"] = "forged instance value"
print(report.title, report.__dict__["title"], report.__dict__["_title"])

try:
    report.title = "   "
except ValueError as error:
    print(type(error).__name__, str(error))
print(report.title)
~~~

结果是 `November forged instance value November`，接着抛出 `ValueError title must contain non-whitespace text`，最后 `report.title` 仍为 `November`。直接写 `__dict__` 绕开了 `__set__`，但正常读取仍先调用数据描述符；描述符约束的是普通属性访问协议，不是防止任意代码篡改内部状态的安全边界。

### 实例字典、类属性和两种描述符怎样排优先级？

对默认实例读取，Python 先沿 `type(obj).__mro__` 找到第一个定义该名称的类属性候选，再按候选的 descriptor 能力和实例字典决定返回值。关键条件是“数据描述符并且有 `__get__`”：只有这种可读取的数据描述符会在读取时压过同名实例值。

| 类 MRO 找到的候选 | 实例字典有同名键 | `obj.x` 的结果 |
| --- | --- | --- |
| 有 `__get__` 且有 `__set__` 或 `__delete__` 的数据描述符 | 有或没有 | 调用描述符的 `__get__` |
| 定义了 `__get__`、没有 `__set__` / `__delete__` 的非数据描述符 | 有 | 返回实例字典值 |
| 同一个非数据描述符 | 没有 | 调用描述符的 `__get__` |
| 没有 `__get__` 的类候选，包括只定义 `__set__` / `__delete__` 的描述符 | 有 | 返回实例字典值 |
| 没有 `__get__` 的类候选 | 没有 | 返回类候选本身 |
| 没有类候选 | 有 | 返回实例字典值 |
| 没有类候选 | 没有 | 默认查找抛 `AttributeError`，之后才尝试 `__getattr__` |

这张读取表假定普通实例有 `__dict__`；若实例没有字典，查找会略过这一步。有 `__set__` 或 `__delete__` 就属于数据描述符，即使没有 `__get__`；不过，没有 getter 的对象不能在读取时计算属性值，所以它不会压过实例字典，实例字典缺少该键时则直接读到类上的描述符对象。

赋值有自己的分派规则。类候选定义了 `__set__` 时，`obj.x = value` 会调用它；只定义 `__delete__` 的数据描述符也会拦截默认赋值，但由于没有 `__set__`，赋值会抛出 `AttributeError`，已有的同名实例键不会被替换。setter 自己拒绝值时，异常同样向外传播。只有类上没有拦截这次赋值的描述符且实例有 `__dict__` 时，默认赋值才会写入实例字典；没有实例字典也可能无法新增属性。读取优先级表不能代替设置规则。

下面的 `DeleteOnly` 只实现删除协议。即使实例字典已有 `value`，点号赋值也会由类候选拦截并报错，旧值保持不变：

~~~python
class DeleteOnly:
    def __delete__(self, instance):
        pass

class Holder:
    value = DeleteOnly()

holder = Holder()
holder.__dict__["value"] = "kept"
try:
    holder.value = "new"
except AttributeError as error:
    print(type(error).__name__, str(error), holder.__dict__["value"])
~~~

CPython 3.11.13 输出 `AttributeError __set__ kept`。

`@property` 是数据描述符。普通类函数是非数据描述符：`report.publish` 会调用函数的 `__get__`，得到一个绑定方法（bound method），其中 `__self__` 是 `report`、`__func__` 是类字典里的函数。函数只有放在类上、经实例读取时才按这条路径绑定；将普通函数直接存进实例字典，读取会得到原函数，不会自动补上 `self`。因为函数是非数据描述符，实例字典可以遮住它；这也解释了为什么对单个实例做 monkey patch（运行时替换）只影响那个实例。

~~~python
print(report.category)
report.category = "draft"
print(report.category, Report.category)

bound = report.publish
print(bound.__self__ is report, bound.__func__ is vars(Report)["publish"])
print(bound())
report.__dict__["publish"] = "temporary label"
print(report.publish)
del report.__dict__["publish"]
print(report.publish())
~~~

输出先是 `monthly`，之后是 `draft monthly`：普通类值在实例没有同名键时提供默认值，赋值创建实例自己的遮蔽值。方法部分依次输出 `True True`、`Published November (2 events)`、`temporary label` 和恢复后的 `Published November (2 events)`。

普通点号访问和两参数 `getattr(obj, "x")` 的外层分派，会在 `__getattribute__(self, name)` 抛出 `AttributeError` 时调用类上定义的 `__getattr__(self, name)`；这个错误可以来自默认读取，也可以来自重写后的 `__getattribute__`。若没有 `__getattr__`，或回退方法再次抛出 `AttributeError`，错误传给调用方。描述符 `__get__` 抛出 `AttributeError` 也会触发同一回退。`__getattribute__` 为每次显式属性读取提供入口，默认实现是 `object.__getattribute__`，其中包含上述描述符和实例字典顺序。重写它会接管默认路径；若要保留该路径，应在实现里委托给 `object.__getattribute__(self, name)`，并避免用 `self.other` 读取内部状态而递归。

可以从 `row_count` 看出默认回退和直接调用的区别。`report.row_count` 与 `getattr(report, "row_count")` 都在默认查找失败后调用 `Report.__getattr__`；直接调用 `object.__getattribute__` 只做默认查找本身，不会自行调用回退。

~~~python
events.clear()
print(report.row_count, getattr(report, "row_count"))
try:
    object.__getattribute__(report, "row_count")
except AttributeError:
    print("direct object.__getattribute__: AttributeError")
print(events)
~~~

前两次访问都得到 `2`，事件列表只记录两次 `__getattr__(row_count)`；直接调用 `object.__getattribute__` 抛出 `AttributeError`，没有额外调用 `__getattr__`。在属性找到了数据描述符、但 getter 因内部值缺失而抛出 `AttributeError` 时，默认查找也以这个错误结束，外层属性语法再尝试 `__getattr__`，而不是回头读取同名实例字典值。

下面故意只调用 `Report.__new__` 而不运行 `__init__`，让 `_title` 缺失；同时在实例字典放入伪造的同名 `title` 键。描述符 getter 抛出 `AttributeError` 后，点号访问调用 `__getattr__("title")`；回退也抛错，所以最终仍是 `AttributeError`，字典里的伪造值没有被读出。这只用于显露查找分支，正常业务对象仍通过 `Report(...)` 初始化。

~~~python
events.clear()
incomplete = Report.__new__(Report)
incomplete.__dict__["title"] = "forged instance value"
try:
    incomplete.title
except AttributeError as error:
    print(type(error).__name__)
print(events)
~~~

本机输出是 `AttributeError` 和 `['__getattr__(title)']`。本例在 getter 错误发生前确实已经有 `incomplete.__dict__["title"]`；这一步表明该错误会直接转入 `__getattr__`，查找不会返回去读取同名实例字典键。

### 菱形继承中，`super()` 为什么会到达另一个 mixin？

标题描述符调用的是绑定到当前 `Report` 实例的 `validate_title` 方法。零参数 `super()` 会从“当前方法定义的类”在“该实例真实类型的 MRO”中的位置之后继续查找；它不是按当前类定义里的直接父类名称固定跳转。MRO 因此决定这条校验链的下一站。

![Report 的菱形继承结构、C3 线性化结果和 super 调用顺序](../../engineering-foundations/backend/resources/python-super-mro.svg)

`Report(AuditMixin, NormalizeMixin)` 声明审计 mixin 在前，规范化 mixin 在后；两者共同继承 `FieldBase`。C3 线性化保留每个基类已有的顺序，也保留子类声明的直接基类顺序，并让共同的 `FieldBase` 只进入最终 MRO 一次。

可按 C3 规则推导：

~~~text
L(AuditMixin) = [AuditMixin, FieldBase, object]
L(NormalizeMixin) = [NormalizeMixin, FieldBase, object]
L(Report) = [Report] + merge(
    [AuditMixin, FieldBase, object],
    [NormalizeMixin, FieldBase, object],
    [AuditMixin, NormalizeMixin],
)
~~~

每轮从各列表当前首项中，选第一个不出现在任何其他列表剩余尾部的类，将它追加到结果，并从所有以它开头的剩余列表移除首项。先选 `AuditMixin`；从第一张线性化列表和直接基类列表同时移除它后，剩余序列为 `[FieldBase, object]`、`[NormalizeMixin, FieldBase, object]`、`[NormalizeMixin]`。此时 `FieldBase` 虽是第一张表的首项，却出现在第二张表的尾部，暂时不能选。选择 `NormalizeMixin` 后，也从以它开头的两张表同时移除，剩余为 `[FieldBase, object]`、`[FieldBase, object]` 和空表；于是依次选出 `FieldBase` 与 `object`。所以 `Report.__mro__` 是 `[Report, AuditMixin, NormalizeMixin, FieldBase, object]`。若某轮仍有剩余项却选不出合法候选，继承约束相互冲突，类定义会失败并抛出 `TypeError`。

本例的轨迹是 `Report.validate_title → AuditMixin.validate_title → NormalizeMixin.validate_title → FieldBase.validate_title`。`FieldBase` 是校验链终点，没有下一层 `validate_title` 要委托。`AuditMixin` 中的 `super()` 从 `AuditMixin` 在 `Report` 实例 MRO 的位置继续，因此抵达 `NormalizeMixin`，不是其定义时写的 `FieldBase`。每层 mixin 都要遵守共同约定：参数形状兼容，并在需要链条继续时调用 `super()`；省掉一次调用会截断后续步骤。

改变直接基类顺序会改变 MRO，也会改变同一套 `super()` 的执行顺序：

~~~python
print([cls.__name__ for cls in Report.__mro__])

class NormalizeFirst(NormalizeMixin, AuditMixin):
    pass

print([cls.__name__ for cls in NormalizeFirst.__mro__])
events.clear()
print(NormalizeFirst().validate_title("  November  "))
print(events)
~~~

`NormalizeFirst` 的 MRO 是 `[NormalizeFirst, NormalizeMixin, AuditMixin, FieldBase, object]`，同一输入仍规范化为 `November`，轨迹则变为 `NormalizeMixin.before → AuditMixin.before → FieldBase → AuditMixin.after → NormalizeMixin.after`。这段代码直接调用只含两个 mixin 的 `NormalizeFirst`，所以轨迹没有 `Report.validate_title`；它比较的是两个 mixin 的相对顺序。这个相对顺序随直接基类声明变化，而 `super()` 的语义不变。对一个方法是否值得组合多个 mixin，应看这些步骤是否真有可组合的共同契约；若调用顺序难以说明，显式组合对象或直接调用命名步骤更容易阅读。

> [!info]- 来源
> - 描述符的定义、必须作为类属性才自动触发、`__set_name__`、实例读取优先级、函数绑定和 `super` 触发 descriptor binding：[Python 3.15.2 Descriptor Guide](https://docs.python.org/3.15/howto/descriptor.html)，Descriptor Protocol、Invocation from an Instance、Invocation from Super、Automatic Name Notification、Functions and Methods，核对于 2026-11-12。
> - 显式读取由 `__getattribute__` 处理；当它抛出 `AttributeError` 时外层 `__getattr__` 才回退，且 descriptor getter 的错误也可进入回退：[Python 3.15.2 Language Reference, Customizing Attribute Access](https://docs.python.org/3.15/reference/datamodel.html#customizing-attribute-access)，核对于 2026-11-12。
> - 类候选查找、默认实例属性查找：[Python 3.15.2 Language Reference, Custom Classes and Class Instances](https://docs.python.org/3.15/reference/datamodel.html#custom-classes)，核对于 2026-11-12。C3 线性化每轮选择候选首项并移除所有以它为首的列表项：[Python 3.15.2 MRO HOWTO](https://docs.python.org/3.15/howto/mro.html#the-c3-method-resolution-order)，核对于 2026-11-12。
> - 零参数 `super()` 从当前类之后沿实例类型的 MRO 查找；MRO 同时供 `getattr` 和 `super` 使用：[Python 3.15.2 Built-in Functions, `super`](https://docs.python.org/3.15/builtins/functions.html#super)，核对于 2026-11-12。
> - 固定实现 CPython 3.11.13 的数据描述符/实例字典/非数据描述符读取顺序与实例设置顺序：[Objects/object.c `_PyObject_GenericGetAttrWithDict` / `_PyObject_GenericSetAttrWithDict`](https://github.com/python/cpython/blob/v3.11.13/Objects/object.c#L1242-L1438)。默认设置路径见 [`_PyObject_GenericSetAttrWithDict`](https://github.com/python/cpython/blob/v3.11.13/Objects/object.c#L1390-L1425)。只实现 `__delete__` 的类候选也进入 descriptor setter 路径，缺少 `__set__` 时由描述符设置槽抛出错误：[Objects/typeobject.c `slot_tp_descr_set`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L7822-L7839)。
> - 固定实现 CPython 3.11.13 的 `__getattribute__` / `__getattr__` 调度、`super_getattro` 的 MRO 后续查找、以及 C3 合并算法：[Objects/typeobject.c](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L7645-L7710)、[`super_getattro`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L8812-L8883)、[`pmerge` / `mro_implementation`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L1841-L2000)，本例在 CPython 3.11.13 重放。
## 27. 异步 FastAPI 接口为什么仍会阻塞？

**案例：** FastAPI 收到 acct-17 的报表请求，异步数据库驱动分三页读取结果。第 1 页尚未就绪时，报表任务（Task）会挂起；若此时 `/health` 已就绪，同一事件循环（event loop）便可先处理它。第 1 页就绪后，报表任务恢复并继续顺序读取下一页。若路由直接调用同步数据库辅助函数，当前事件循环会一直等到三页同步调用全部返回，期间其他就绪请求只能等待调度。资源还必须活到最后一次使用它的阶段。

![异步等待与直接同步调用对事件循环的影响](../../engineering-foundations/backend/resources/python-async-await-scheduling.svg)

### 从 async def 到运行中的协程，中间发生什么？

调用 async def 函数先得到协程对象（coroutine object）；FastAPI 在请求 Task 中调用路由，再由事件循环驱动这个 Task。Task 是事件循环推进协程的调度单位；同一时刻只运行一个 Task 的同步代码。Task 在等待尚未就绪的 Future（异步结果对象）或输入/输出（I/O）时挂起，事件循环才有机会推进其他就绪任务。数据库返回第 1 页时，等待对象就绪，报表 Task 恢复并拿到结果；它处理这一页后再 await 第 2 页。

await 表示等待一个可等待对象，不保证每次都会切换任务：如果对象已经就绪，当前任务可以直接继续。async def 也不会自动把函数搬到线程。直接调用 time.sleep()、同步数据库驱动或很长的 Python 计算时，当前任务没有把控制权交回事件循环；事件循环要等它返回才能处理其他任务。

按所调用的 API 选择运行边界：

| 写法 | 执行位置与适用边界 |
| --- | --- |
| 在 async def 中 await 原生异步数据库或 HTTP API | I/O 未完成时挂起当前 Task，让事件循环处理其他就绪任务；这是报表分页的主路径。 |
| 在 async def 中直接调用同步辅助函数 | 辅助函数在当前事件循环线程执行；FastAPI 不会拦截你直接调用的普通函数。 |
| 把 FastAPI 路由或依赖本身声明为 def | FastAPI/Starlette 通过 AnyIO 工作线程执行同步代码。线程容量有限，调用超过容量时会等待。 |
| 在异步路由中对短期阻塞 I/O 使用 asyncio.to_thread() | 由 asyncio 默认执行器（executor）的线程执行；它与 AnyIO 的同步路由/依赖限额分开配置。 |
| 把纯 Python 的 CPU 密集工作交给有界进程池或独立工作进程（worker） | 避免长时间占用事件循环，并可用多个进程并行；要承担进程调度、序列化和内存成本。 |

下面用合成的每页等待 40 毫秒演示原生异步读取；它只是模拟 I/O 等待，不是数据库测量。同步分支用每页阻塞 60 毫秒，便于观察事件循环被占住的顺序。

~~~python
import asyncio
import time

from fastapi import Depends, FastAPI

app = FastAPI()

async def fetch_page(account: str, page: int) -> dict[str, object]:
    await asyncio.sleep(0.04)  # 合成等待：模拟异步 I/O
    return {"account": account, "page": page}

def fetch_page_sync(account: str, page: int) -> dict[str, object]:
    time.sleep(0.06)  # 合成阻塞：模拟同步 I/O
    return {"account": account, "page": page}

async def read_pages_async(account: str) -> list[dict[str, object]]:
    rows = []
    for page in range(1, 4):
        rows.append(await fetch_page(account, page))
    return rows

def read_pages_sync(account: str) -> list[dict[str, object]]:
    return [fetch_page_sync(account, page) for page in range(1, 4)]

def load_settings() -> dict[str, str]:
    return {"region": "demo"}

@app.get("/reports/{account}")
async def report(account: str, settings: dict[str, str] = Depends(load_settings)):
    return {"region": settings["region"], "rows": await read_pages_async(account)}

@app.get("/blocking/{account}")
async def blocking_report(account: str):
    # 同步辅助函数直接运行在事件循环线程。
    return {"rows": read_pages_sync(account)}

@app.get("/offloaded/{account}")
async def offloaded_report(account: str):
    return {"rows": await asyncio.to_thread(read_pages_sync, account)}

@app.get("/sync-route/{account}")
def sync_route(account: str):
    # FastAPI 会把它交给 AnyIO worker thread。
    return {"rows": read_pages_sync(account)}

@app.get("/health")
async def health():
    return {"status": "ok"}
~~~

/reports/acct-17 每页等待时都会给事件循环一个处理其他任务的机会；/blocking/acct-17 在路由中直接运行三次同步读取，事件循环要等约 180 毫秒的合成阻塞结束后才能处理 /health。/offloaded 在 asyncio 默认 executor 中运行同一同步函数；/sync-route 则由 FastAPI/Starlette 调度到 AnyIO worker thread。后两条路径都让事件循环继续运行，但它们各自消耗不同的线程容量，卸载不会消除下游数据库或文件操作本身的成本。

/reports 路由还通过 Depends(load_settings) 接收一个普通 def 依赖。FastAPI 主动调用的同步依赖会进 AnyIO worker thread；这和 async 路由里直接调用同步辅助函数是不同的调用边界。

Starlette 文档说明，默认 AnyIO 工作线程限额（worker thread limiter）有 40 个并发令牌（token），FastAPI 的同步依赖和 Starlette 的若干同步操作也会使用这份容量；本机 AnyIO 4.12.1 的默认值复放为 40。它是并发上限，不是需要填满的目标。提高上限会允许更多线程同时执行，可能增加线程和下游资源压力；仍要按每进程的线程与连接预算评估。asyncio 默认 executor 的配置不受这个限额控制。同时应按资源预算限制等待队列，并在入口做准入控制；执行并发上限本身不会限制有多少调用在排队。

对 CPython 3.11，Global Interpreter Lock（全局解释器锁，GIL）意味着多个普通 Python 线程通常不能同时执行 Python 字节码。因此把 CPU 密集的纯 Python 函数放进 asyncio.to_thread() 可以避免直接占住事件循环，却通常不能获得多核并行；选择进程池或独立 worker 更合适。CPython 3.13 起提供可选的 free-threaded（自由线程）构建，3.14 起进入正式支持阶段但仍是可选构建；扩展库可能重新启用 GIL，实际收益和线程安全仍要按所用解释器及依赖验证。

`await fetch_page(...)` 仍在当前请求 Task 中顺序读取各页；await 不会自动创建并发任务。若一个请求要并发查询多个页面，需用 `asyncio.create_task()` 或 Python 3.11 的任务组（TaskGroup）中的 `create_task()` 显式建立子 Task，创建者仍要收集结果并等待结束；TaskGroup 会在退出作用域前等待组内任务完成。不要留下无人管理的后台 Task，也不要让并发 Task 共用同一个 ORM `AsyncSession`；每个 Task 都要有自己的会话。请求或 worker 执行尝试也应各自持有短生命周期会话，数据库连接池的等待与上限见[怎样限定 ORM Session 并排查连接池耗尽？](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)。

### 任务取消时，函数、线程和远端操作分别会怎样？

Task.cancel() 是取消请求：事件循环在下一次调度机会向协程注入 CancelledError。协程可以在 finally 中关闭游标、会话或临时文件；清理后通常应继续传播取消，让调用方按取消处理。若捕获后普通返回，调用方可能观察到正常结果而不是取消；若吞掉 `asyncio.timeout()` 发出的取消，超时作用域也可能正常退出，不抛 TimeoutError。任务组可能因此把子任务当作正常完成，偏离调用方预期的取消控制流。

asyncio.timeout(秒数) 也靠事件循环调度取消。若一个同步函数把事件循环堵住，截止时间到达时取消回调不能运行。用本机 CPython 3.11.13 复放：asyncio.timeout(0.01) 包住 time.sleep(0.05)，代码约 0.05 秒后正常离开，没有抛出 TimeoutError。若阻塞调用返回后，协程仍在 scope 内等待一个尚未就绪的异步操作，事件循环才有机会运行迟到的取消回调；本机复放中紧接着 `await asyncio.sleep(0)` 仍正常退出，而等待正时长的异步操作时才观察到 TimeoutError。因此超时不是中断任意同步函数的机制。

取消等待 `asyncio.to_thread(blocking_call)` 的 Task，会让异步调用方停止等待。如果函数已经在线程中运行，Python 不会强制杀掉该线程；若工作还在 executor 排队而未开始，则可能在执行前被取消。线程仍可能在使用文件、连接或其他资源。释放连接池、关闭共享句柄前，应确认线程已经结束。对 asyncio.to_thread()，可传入 threading.Event 作为停止信号并让函数定期检查；AnyIO worker 则可用 from_thread.check_cancelled() 做协作式检查。

客户端超时或断线也不证明远端副作用已停止：写操作可能没到服务端、可能已回滚，也可能已提交但响应丢失。对于持久报表 job（后台任务），应通过权威状态查询结果，显式请求取消并确认 worker 已停止；不要把一次 HTTP 断线当成 job 终态。完整的重试与状态确认边界见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

### FastAPI 的 yield 依赖应何时释放？

yield 依赖适合把资源打开和清理放在同一生命周期中，例如异步数据库会话或游标。FastAPI 带 yield 的依赖默认使用请求作用域（request scope）：FastAPI 在调用路由前解析依赖时打开，应用发送完响应正文后清理。这里“发送完”指ASGI（异步服务器网关接口）的 `http.response.body` 最终帧已发送，不代表客户端已从网络收齐字节。指定 `Depends(scope="function")` 时，函数作用域（function scope）会在路由函数返回后、响应发送前清理。

这些依赖 scope 参数从 FastAPI 0.121.0 起支持；下面的行为在 FastAPI 0.128.0、Starlette 0.47.2 上核对。

下面从小型 JSON 响应切换到较大的 CSV（逗号分隔值）流，比较资源的最后使用点。

![FastAPI yield 依赖作用域与响应正文的关系](../../engineering-foundations/backend/resources/python-fastapi-yield-lifetimes.svg)

CSV 路由可以先返回 StreamingResponse，再由正文生成器逐块读取数据库游标。如果依赖使用 scope="function"，路由一返回 Store 就已关闭，正文生成器后续读取会失败。让 request scope 覆盖整个应用正文发送；若正文发送结束、流中止或出错，依赖退出逻辑仍须在 finally 中清理资源。反过来，若路由已经读完资源并生成完整 JSON，function scope 可以在应用发送响应前释放它，减少资源占用时间。

下面用另一个独立的最小应用验证这个边界。其中的 `Store` 是合成对象：`close()` 会标记关闭状态，之后的 `read_row()` 明确抛出 `RuntimeError`。这是教学用的资源契约，不代表某个数据库驱动固定使用该异常类型。

~~~python
import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

class Store:
    def __init__(self) -> None:
        self.closed = False

    async def read_row(self) -> bytes:
        await asyncio.sleep(0)
        if self.closed:
            raise RuntimeError("Store is closed")
        return b"acct-17,42\n"

    async def close(self) -> None:
        self.closed = True

async def get_store() -> AsyncIterator[Store]:
    store = Store()
    try:
        yield store
    finally:
        await store.close()

@app.get("/row")
async def read_row(
    store: Annotated[Store, Depends(get_store, scope="function")],
):
    row = await store.read_row()
    return {"row": row.decode().strip()}

@app.get("/stream")
async def stream_rows(
    store: Annotated[Store, Depends(get_store)],
):
    async def body():
        yield b"account,report_id\n"
        yield await store.read_row()

    return StreamingResponse(body(), media_type="text/csv")
~~~

在合成驱动的 ASGI trace 中，/row 的顺序是 `open → read → close → 发送 JSON`；/stream 是 `open → 发送 CSV 表头 → 读取 Store → 发送正文结束 → close`。路由返回 StreamingResponse 时，正文生成器尚未读取行；默认 request scope 让 Store 留到应用发送完最后一帧。这个边界是 ASGI 发送完成，不是客户端实际收齐字节。反过来，把 `/stream` 的依赖改成 `Depends(get_store, scope="function")` 再运行，会得到 `open → close → response.start(200) → CSV 表头 → read 抛 RuntimeError`，不会发送最终正文帧：证明路由函数返回时过早关闭了仍要供生成器读取的资源。

直接流式响应把连接、游标和请求生命周期绑在一起，正文尚未发完时会继续占资源；客户端断开也不是可查询的持久任务结果。若报表要由后台可靠生成并可稍后下载，本仓的报表案例会在同一事务中受理 job、写入 outbox 并占用等待槽，事务提交后返回 202。worker 在自己的 attempt 内重新获取会话和连接，先完成 CSV 私有对象写入，再在任务仍为 `running`、attempt 匹配且未请求取消的条件下提交结果引用与 `succeeded` 终态；这和请求内的 StreamingResponse 是两种生命周期。job 的持久流程见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)。

> [!info]- 来源
> - Python 3.11 async def 返回协程、Task 等待 Future 时挂起以及事件循环一次运行一个 Task：[Coroutines and Tasks](https://docs.python.org/3.11/library/asyncio-task.html#coroutines)，§Coroutines、§Task Object；并发作用域：[§Task Groups](https://docs.python.org/3.11/library/asyncio-task.html#task-groups)。核对于 2026-11-12，相关调度示例于 CPython 3.11.13 重放。
> - SQLAlchemy 2.0 的 `AsyncSession` 不可在并发 Task 间共享：[Using AsyncSession with Concurrent Tasks](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncsession-with-concurrent-tasks)；核对日期：2026-11-12。
> - asyncio.timeout() 通过取消当前 Task 实现截止时间，asyncio.to_thread() 使用独立线程并主要面向阻塞 I/O：[Python 3.11 Coroutines and Tasks](https://docs.python.org/3.11/library/asyncio-task.html#timeouts)，§Timeouts、§Running in Threads；Future 已开始运行后 cancel() 不能终止它：[Python 3.11 concurrent.futures](https://docs.python.org/3.11/library/concurrent.futures.html#concurrent.futures.Future.cancel)。核对于 2026-11-12；超时和已运行线程取消分支于 CPython 3.11.13 本机重放。
> - asyncio.to_thread() 将函数提交到默认线程执行器：[Python 3.11 Event Loop](https://docs.python.org/3.11/library/asyncio-eventloop.html#executing-code-in-thread-or-process-pools)，§Executing code in thread or process pools；纯 Python CPU 工作使用进程池的标准接口也见此节。
> - FastAPI 的同步 path operation 和同步依赖在线程池执行，直接调用的普通 helper 不会被 FastAPI 改变调用方式：[FastAPI Concurrency and async / await](https://fastapi.tiangolo.com/async/)，§Very Technical Details / Path operation functions、Dependencies、Other utility functions；文档及 FastAPI 0.128.0、Starlette 0.47.2、AnyIO 4.12.1 行为核对于 2026-11-12。
> - Starlette 使用 AnyIO 运行同步端点、依赖和内部同步操作；默认 limiter 为 40 tokens：[Starlette Thread Pool](https://starlette.dev/threadpool/#concurrency-limitations)，§Concurrency Limitations。AnyIO limiter 不影响 asyncio 默认 executor：[AnyIO Working with threads](https://anyio.readthedocs.io/en/stable/threads.html)，§Adjusting the default maximum worker thread count；文档及本机 4.12.1 默认 token 数核对于 2026-11-12。
> - Python 不能强杀已运行线程；threading.Event 可用作显式停止信号：[Python 3.11 threading](https://docs.python.org/3.11/library/threading.html#event-objects)，§Event objects。AnyIO worker 也可用 from_thread.check_cancelled() 实现协作式检查：[AnyIO Working with threads](https://anyio.readthedocs.io/en/stable/threads.html)，§Reacting to cancellation in worker threads；两页核对于 2026-11-12。
> - yield 依赖默认 request scope；function scope 在路由返回后、响应发送前退出：[FastAPI Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)，§Early exit and scope。该 scope 功能从 [FastAPI 0.121.0 release notes](https://fastapi.tiangolo.com/release-notes/#01210) 加入；文档及样例于 FastAPI 0.128.0、Starlette 0.47.2 核对于 2026-11-12，生成器退出顺序以本机 ASGI trace 核对。
> - Starlette 0.47.2 的 StreamingResponse 迭代正文并发送分块；断连或发送错误会结束/取消流生成任务，使请求作用域有机会退出：[pinned responses.py](https://github.com/Kludex/starlette/blob/0.47.2/starlette/responses.py#L220-L278)。实现核对于 2026-11-12；正文与依赖顺序在本机 ASGITransport trace 核对，这不是 TCP 断线测试。
> - `http.response.body` 的最终 ASGI 事件用 `more_body=False` 表示应用已发送完响应正文：[ASGI HTTP Response Body](https://asgi.readthedocs.io/en/stable/specs/www.html#response-body-send-event)，§Response Body；核对日期：2026-11-12。客户端是否已收齐字节由网络层决定。
> - CPython 3.11 普通线程受 GIL 限制；free-threaded 构建的可选支持和扩展模块可能重新启用 GIL：[Python support for free threading](https://docs.python.org/3/howto/free-threading-python.html)，§Installation、§The global interpreter lock in free-threaded Python；3.14 的正式支持阶段见 [PEP 779](https://peps.python.org/pep-0779/)，§Abstract。两页核对于 2026-11-12。
## 28. 如何估算并限制异步工作管线？

**案例：** application programming interface (API，应用程序接口) 收到 `acct-17` 的报表导出请求，事务写入 job（任务）、outbox（事务发件箱）和一个共享等待槽后才返回 202。worker（工作进程）有限地读取数据库，生成 Comma-Separated Values (CSV，逗号分隔值) 文件并上传私有结果对象；只有结果引用与 `succeeded` 同时提交，结果才对用户可用。这是“先接受、后台继续、之后可查”的持久路径。直接以 Hypertext Transfer Protocol (HTTP，超文本传输协议) 流式返回 CSV 属于另一种请求内工作：发送正文期间仍占用请求连接和处理资源，断开后的读取不会自动变成可查询 job。

容量不是一个“队列长度”数字。准入速率限制新逻辑 job（任务）的到达，等待槽限制已经承诺但尚未领取的工作量，执行槽限制同时运行的 attempt（一次物理执行尝试）；连接池和对象存储又各有自己的资源预算。队列只能改变工作等在哪里，不能提高下游服务率。

admission control（准入控制）决定新逻辑 job 是否进入系统；backpressure（背压）则把下游已满的信号传回上游，使上游减速、延后或停止提交。HTTP 调用方若不能被动调速，服务就必须在返回 202 之前明确拒绝这次未受理的请求，而不能先承诺接受再丢弃。两者的边界不同：速率限制新 job 的到达，等待槽限制已承诺但未领取的工作量。

本例的 idempotency key (幂等键) 按 `(account_id, principal_id, key)` 唯一，绑定报表 ID、期间和格式等规范化请求的 fingerprint (指纹)。相同范围、同键、同指纹表示重放原意图，返回既有 job；同键异指纹则冲突。准确重放不消耗新 job 的速率令牌或等待槽，但“先查、后扣额”不能解决不同 key 争用最后一个槽。

数据库事务先尝试插入带唯一范围的 job 身份；同键并发败方回滚后读取胜者并核对指纹，同指纹返回原 job，异指纹冲突。只有唯一约束确认新意图胜出，才竞争一条**整条管线共用**的准入额度记录：本例的 7 个/秒令牌、30 枚桶深和 240 个等待槽由所有 API/worker 副本、账户和新 key 共享；不能各实例各自保留一份完整额度。事务先锁这条额度行，按数据库时钟补充令牌，再检查至少一枚令牌及 `waiting_count < 240`，一次更新扣令牌并加等待计数，然后补全 job、参数和 outbox。

两个不同 key 争最后一槽时会在同一额度行上串行，先提交者占槽，后者看到已满后回滚自己的临时 job 身份；令牌、计数、job 和 outbox 同事务提交或一起回滚。令牌不足时在接受前返回 `429 Too Many Requests`，等待槽已满时按暂时过载返回 `503 Service Unavailable`；两种拒绝都不留下 job。若实现为条件原子更新，也必须让令牌和槽检查/递增成为同一事务的唯一胜者操作。每账户限流可以叠加，不能代替这个全管线预算。若额度行在独立外部限流器，数据库回滚不能替它退回令牌，须另建幂等预留/补偿合同。

等待槽的 240 覆盖所有尚未领取轮次，不论 outbox 尚待发布还是 job 已在 broker；它随同一逻辑 job 的位置迁移而不变。领取提交时释放，`queued` 取消与状态终结同事务释放一次，重试重排须重新预留一个槽并写新 outbox。

worker 不能因为 broker 有消息就直接领取：先取得本进程的物理执行槽，再尝试条件领取 job。没有槽时不领取，不无限预取或塞入本地缓冲；这只会推迟领取，不会把已受理 job 判为 `capacity_exhausted`。若条件领取失败，因为重复、已取消或 job 已经终态，worker 归还刚预留的执行槽。领取提交后，job 变为 `running`，attempt（一次物理执行尝试）加一、有界租约写入，逻辑等待槽释放；物理执行槽继续归该 attempt。

fencing（写权栅栏）是恢复器提交接管后拒绝旧 attempt 再提交当前 job 的结果；租约到期本身只让独立恢复器得到竞争资格，不会自动停止旧 attempt。恢复器先处理取消；可重试且未达到上限时，重排事务原子取得新的共享等待槽并写新 outbox；如果这项**已受理 job 的重排**拿不到槽，则提交 `failed` 和 `capacity_exhausted` 错误码。即使恢复器已栅栏旧 attempt，它仍占物理槽，直到该 attempt 实际停止并释放连接、游标或上传句柄。worker 进程可以继续处理其他 job；物理槽归还跟随 attempt 停止，不要求整个进程退出。旧 attempt 停止后的孤儿对象清扫由独立清理任务负责，不必继续占用已归还的 worker 执行槽。

![共享等待槽在领取提交时释放；物理执行槽需等 attempt 停止并释放资源才归还，worker 进程可以复用](../../engineering-foundations/reliability/resources/capacity-slot-ownership.svg)

图中两个槽位属于不同的量纲和所有者。等待槽记未领取的逻辑排队轮次，不随着 outbox 到 broker 的迁移而变；物理执行槽记仍在运行且占有处理器时间、连接、游标或上传句柄的 attempt。worker 结束一次业务操作后可以持久决定重排；该 job 可先占新等待槽，而旧 attempt 的物理槽要等它真正停止并释放资源才归还。worker 进程通常留在池中继续工作。租约恢复可能在旧 attempt 停顿时提交新排队轮次，之后新 worker 可另占一个物理槽；若两次 attempt 短暂重叠，必须分别计算和占用两个槽。

### 用平均在途量估算，不要把平均值当峰值保证

Little's law（利特尔定律）给出稳定系统的长期平均关系：

~~~text
平均系统内任务数 L = 平均有效到达率 λ × 平均系统停留时间 W
~~~

三个量必须属于同一个边界和同一种任务。若系统只算 worker 的执行，`W` 用平均 attempt 执行时间；若系统包括等待，`W` 也包含队列时间。`λ` 是该边界实际接纳并进入系统的平均速率，不是已被拒绝的原始 HTTP 请求速率。公式使用长期稳定状态下的有限均值；若无界到达持续超过服务能力而队列一直增长，就不能借这个公式假设一个有限的稳态等待量。

例如某个稳定服务平均接纳 40 个请求/秒，每个请求从进入到离开该服务平均 0.2 秒，那么服务内平均有 `40 × 0.2 = 8` 个在途请求。Little 定律是平均量恒等关系；它不预测突发峰值、等待时间的 p95/p99，也不单独证明一个容量上限安全。到达批次、服务时间长尾、失败重试、拒绝策略和下游瓶颈仍须另行分析。若边界是等待队列，queue depth（队列深度）说明有多少工作在等，queue age（队列年龄）说明最老的工作等了多久；二者揭示不同故障。

### 合成账户报表要预留多少执行槽？

以下是用于演算的显式合成输入，既不是生产测量，也不是服务目标或默认推荐值。

| 输入 | 教学假设 |
| --- | ---: |
| 新幂等键产生的平均提交速率 / 十分钟峰值提交速率 | 5 / 20 个新 job 每秒 |
| 单个请求正文 | 8 KiB |
| API 提交事务借用数据库连接 | 10 ms/job |
| 每份报表的顺序索引读取 | 12 次；每次借连接 20 ms |
| 单个 worker attempt 平均处理时间 | 6 s |
| 平均结果对象 / 每个 job 元数据 | 128 KiB / 2 KiB |
| 结果对象保留期 / 终态及幂等元数据保留期 | 7 天 / 终态后 14 天 |

先只计算每个新 job 一个 attempt，假定六秒平均处理时间已包括生成与上传；重试、租约接管重叠、失败清理与下载另计。若五个新 job/s 实际被接纳并稳定处理，且每个只用一次平均六秒的 attempt，平均有 `5 × 6 = 30` 个在执行的 attempt。峰值时若希望持续处理每秒 20 个新 job，且每个只需一个 attempt，则容量需求为 `20 × 6 = 120` 个平均并发 attempt；这是跟上输入的规划需求，不是当前 worker 的实际执行率。每个 worker 副本有两个进程、每进程八个 attempt 槽，共四个副本时只有 `4 × 2 × 8 = 64` 个物理执行槽，理想上限 `64 / 6 ≈ 10.67 attempt/s`，因此在该负载下不能形成稳定的 20/s 执行流，等待会增长或新 job 被拒绝。

若 64 槽都持续有工作，按六秒平均服务时间折算的理想平均服务率是 `64 / 6 ≈ 10.67 attempt/s`。这是忽略调度空隙和所有额外工作的上界型估算，不是压测吞吐。规划时先把平均利用率假设为 70%，可算出 `64 × 0.70 / 6 ≈ 7.47 attempt/s`。于是本例将新 job 的准入目标暂设为每秒 7 个：若平均每个新 job 只运行一次 attempt，则占槽 `7 × 6 = 42` 个，即 `42 / 64 ≈ 65.6%`。70% 目标相当于每秒 `44.8` 个 attempt 槽秒；以 7 个新 job/s 均摊，最多约 `44.8 ÷ (7 × 6) ≈ 1.067` 个六秒 attempt/job 才不超过该规划预算。70% 和 7/s 是待负载测试验证的起点。重试、租约接管重叠、处理时间长尾和运维任务都会改变实际服务率。

这里要分清三种控制：

| 控制量 | 合成上限 | 解决的问题 | 不能推出什么 |
| --- | ---: | --- | --- |
| token bucket（令牌桶）新 job 速率 | 补充 7 个/秒 | 平滑长期新工作到达 | 不保证下游一定及时完成 |
| token bucket 瞬时 burst（突发） | 最多 30 个新 job | 允许短时成批提交 | 不提供无限等待区 |
| 共享未领取等待槽 | 最多 240 个逻辑排队轮次 | 限制已承诺但尚未执行的工作量 | 不限制正在执行 attempt 的物理资源 |
| worker 执行槽 | 64 个 attempt 槽 | 限制并发计算与实时资源 | 不限制 queued/outbox backlog |

这些门槛要共同生效。假设账户十分钟都以 20 个**新幂等键**每秒提交，共有 `20 × 600 = 12,000` 个新逻辑意图。若令牌桶开始时有 30 个令牌、此后以 7/s 补充，则令牌桶单独最多放行 `7 × 600 + 30 = 4,230` 个；在等待槽和其他限额均未先行拒绝的条件下，至少 `12,000 − 4,230 = 7,770` 个新任务不会受理。真实队列故障、worker 停机或重排可能更早占满 240 槽。相同幂等键重放不属于这些新意图，不再耗一枚令牌或一个等待槽；但每次重放仍占用 API 的认证、网络和服务处理资源。

等待槽数量限制了承诺了多少尚未领取的工作，不直接设定队列可等待多久。举例：开始时无积压且令牌桶已满、上游有足够的新 key、其他额度都不冲突、worker 连续 30 秒不能领取，也没有重试重排；令牌桶可让 `30 + 7 × 30 = 240` 个新 job 进入，正好填满 240 个等待槽，之后即使仍有速率令牌也必须拒绝。已有积压或其他重排会让等待槽更早占满；若 worker 停领超过 30 秒，填满后后续符合速率条件的新 job 会持续被拒绝，直到有槽释放。240 是本案例的等待工作量边界，不代表最长等待 30 秒；容量应按业务可接受的排队 service-level objective (SLO，服务等级目标) 和实测服务/恢复速度校准，队列年龄持续上升时要降速或拒绝。

本例每个 job 固定最多三次 attempt（含首次），即最多两次重试；这是为说明有界恢复而设的案例策略，不是队列或框架默认值。worker 遇到可重试暂时错误并结束当前工作后，与租约到期后取得竞争资格的恢复器，都要按当前 job/attempt 条件决定下一步：取消优先；永久错误或达到三次上限写终态；其余只有成功取得等待槽时，才同事务写 `queued`、退避后的 `available_at` 和新的 `pending` outbox。relay 必须在到期时可靠唤醒；过早到达的重复投递仍受数据库可领取时间条件约束，未确认到期唤醒已持久安排时不能提前 ACK。槽不足则持久写 `failed/capacity_exhausted`；达到上限则持久写 `failed/attempts_exhausted`。旧投递只带 job ID，即使来自上一轮也可以唤醒并竞争当前 queued 轮次；数据库条件让一轮最多被领取一次，它不能自行增加 attempt。租约到期只让恢复器有资格竞争，恢复事务提交才 fence 旧 attempt。fence 后，旧 attempt 仍占原物理执行槽，直到该 attempt 停止并释放连接、游标、上传等资源；三次上限限制启动总数，有限读取/上传截止时间和可观察的停止路径才限制物理重叠持续多久。相关提交、ACK 与租约条件见[怎样设计一个可持久查询的账户报表？](#%E5%B7%A5%E4%BD%9C%E8%BF%9B%E7%A8%8B%E9%87%8D%E8%AF%95%E6%80%8E%E6%A0%B7%E9%81%BF%E5%85%8D%E6%97%A7%E7%BB%93%E6%9E%9C%E8%A6%86%E7%9B%96%E6%96%B0%E7%BB%93%E6%9E%9C%EF%BC%9F)和[报表任务的发布确认、消费者确认与业务完成各证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 进程内连接池怎样叠加成数据库总预算？

SQLAlchemy 的连接池由进程内 Engine（引擎对象）持有；扩容应用进程会复制连接上限。本例假定 API 和 worker 各有四个副本、每副本两个进程，每个进程一个同步 `QueuePool`，设置 `pool_size=8` 与 `max_overflow=2`。该池最多允许每进程十条并发连接；超出常驻池容量的连接在归还时关闭，空闲池最多保留八条。若使用异步 Engine，则使用 `AsyncAdaptedQueuePool`；SQLite 内存数据库也有不同默认池行为，所以其他数据库、池实现或进程模型都要重算。

| 连接使用者 | 配置最大值计算 | 连接数上限 |
| --- | ---: | ---: |
| API：4 个副本，每副本 2 个进程 | `4 × 2 × (8 + 2)` | 80 |
| worker：4 个副本，每副本 2 个进程 | `4 × 2 × (8 + 2)` | 80 |
| 其他共用数据库的服务 | 本例预留 | 40 |
| 应用配置总上限 | `80 + 80 + 40` | 200 |
| 教学用数据库连接预算 | 本例假设 | 240 |
| 配置上限之外的余量 | `240 − 200` | 40 |

这是池可同时借出的配置上限，不代表数据库此刻有 200 条活跃查询；连接池会按需打开连接，也可能保留已打开的空闲连接。此预算还必须核对迁移程序、运维连接及数据库自身保留额度；教学用的 240 已把其他共享服务列为 40，但不等于任意数据库都能把 240 条分配给应用。

按每页借连接 20 ms，单个 report attempt 的读取是 `12 × 0.020 = 0.24` 连接秒；新 job 提交事务另占 `0.010` 连接秒。连接池平均借用量要用各自边界内**实际**速率计算：`0.24 × λ_attempt + 0.010 × λ_accepted_job`，其中 `λ_attempt` 是实际执行 attempt/s，`λ_accepted_job` 是实际接受的新 job/s。若本例稳定地处理 5 个新 job/s、每个一个 attempt，则约为 `5 × 0.24 + 5 × 0.010 = 1.25` 条平均连接。若 workers 实际达到规划的 7 attempts/s 且 API 同时接受 7 jobs/s，则预测约 `7 × 0.24 + 7 × 0.010 = 1.75` 条；这是按规划速率估算，不是测量。峰值 20 jobs/s 若要稳定处理且每个只跑一个 attempt，需要约 `4.8` 条读取连接和 `0.2` 条提交连接，共 5 条；但当前 64 槽无法稳定达到这个 worker 速率，所以这组 20/s 数字是假设扩容后的需求，不是当前系统的平均实际借用量。重试会让 attempt 速率高于新 job 速率。以上均不含长事务、慢查询、池等待或上传期间误持连接；池上限仍须按各进程的并发配置求和。

### 结果存储和请求字节量会涨到多少？

若每个请求正文都读完整，5 个请求/s 的平均入口正文约为 `5 × 8 KiB = 40 KiB/s`；20 个请求/s 的十分钟峰值约为 `20 × 8 KiB = 160 KiB/s`，累计 `20 × 600 × 8 KiB = 93.75 MiB`。这是按**到达的 HTTP 请求**算的入口量，不是新 job 的接纳率：速率令牌只约束创建 job，已读完才拒绝的请求、幂等重放和同 key 冲突仍耗用网络及解析资源；若服务在读正文前拒绝，实际正文流量会更低。这里未计 HTTP 头、Transport Layer Security (TLS，传输层安全协议)、重传或响应字节。

若长期每秒有五个 job 成功完成、每份结果 128 KiB 且保留七天，结果对象约占：

~~~text
128 KiB × 5 个/s × 604,800 s ÷ 1,048,576 KiB/GiB
= 369.140625 GiB ≈ 369 GiB
~~~

这是仅含对象正文的平均体量，不含副本、元数据、版本、压缩差异或删除延迟。另按稳态每秒 5 个 job 转为终态（成功、失败或取消）计算，每个 2 KiB 终态与幂等记录保留在终态后 14 天，元数据约占：

~~~text
2 KiB × 5 个/s × 1,209,600 s ÷ 1,048,576 KiB/GiB
= 11.5356 GiB ≈ 11.54 GiB
~~~

这项估算不含索引；示例中的 2 KiB 已包含每个 job 一条持久记录（其状态原位更新为终态）和幂等元数据，失败 job 也包含在每秒 5 个终态 job 的假设里，不应再把失败重复加成一条 job 记录。若系统把 attempt 历史或诊断事件另存为行，它们和清理滞后会增加额外空间。若每秒 7 份都成功完成，平均结果写入约 `7 × 128 KiB = 896 KiB/s = 0.875 MiB/s`；本例 30 个突发任务全部成功会写入 `30 × 128 KiB = 3.75 MiB`。64 槽按六秒平均服务时间的理想完成率 10.67 attempts/s，在每个 attempt 都成功且产出平均结果的条件下，对应约 `1.33 MiB/s`；这是理想完成量，不是观测写入率，对象存储限速和数据库提交也会降低实际值。下载流量是读取负载，应另外估算，不能和生成带宽混为一谈。

### 如何确认最先到达的瓶颈？

峰值输入是 20 个新 job/s；若都被接纳并想稳定完成、每个只需一个六秒 attempt，就需要平均 120 个并发 attempt。当前 64 槽在理想条件下最多支撑约 10.67 attempts/s，实际吞吐还会受调度、失败重试和下游影响，所以 120 是需求量，不是当前 worker 的实测并发或吞吐。若新 job 准入目标设为 7/s 且每个 job 平均一次六秒 attempt，规划平均并发是 42 槽；这是假设值，不是 SLO 或容量保证。与 200 条应用连接配置上限对比只能帮助排查哪项预算可能先紧，不能排除单进程池等待、数据库处理器/输入输出/锁或对象存储瓶颈。

用代表性的请求大小、12 页读取扇出和结果体量逐步加压，再分别尝试 20/s 十分钟峰值、30 个突发、240 槽满、慢查询、对象上传变慢、重试、worker 丢失和租约重叠。每个场景记录 API 受理延迟、排队等待时长、执行时长、结果下载时长以及 p50、p95、p99（第 50、95、99 百分位）时延；六秒只是假设的平均 attempt 时长，不是 p95 目标。观察 token 放行与拒绝、等待槽占用、最老 outbox / queued / broker age、活跃与被栅栏但仍存活的 attempt、数据库连接池借出与 checkout（借出连接）等待、structured query language (SQL，结构化查询语言) 查询耗时、对象体量、重试、取消和终态码。若 broker 深度下降而数据库 queued 年龄继续上升，工作只是换了积压位置。再按用户实际 SLO 决定调整准入、资源或查询计划，而不是只扩队列。

API 在新 job 还未接受时因共享速率令牌不足而拒绝，或因等待槽已满而拒绝；案例可分别按限流返回 `429 Too Many Requests`、按暂时过载返回 `503 Service Unavailable`。这些是受理边界的拒绝，不能伪装成已经接受的 job 失败。调用方按同一幂等键重试受理结果未知的提交。已经受理的 job 若重试或租约恢复时预留不到共享等待槽，才持久为 `failed/capacity_exhausted`；attempt 耗尽则是 `failed/attempts_exhausted`。worker 本地物理槽不足只推迟领取，不把 queued job 改为容量失败。HTTP 流式路径则由请求自己的截止时间、连接和流背压决定能持续发送多久，不应把异步队列的等待槽公式挪过去。

**接下来：** [持久报表任务状态与恢复](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)说明 job、等待槽、attempt 和结果如何同数据库状态交接；[队列确认页](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)展开 prefetch、发布确认与消费者 ACK；[数据访问与连接池](#11.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%AE%9A%E5%AF%B9%E8%B1%A1%E5%85%B3%E7%B3%BB%E6%98%A0%E5%B0%84%E4%BC%9A%E8%AF%9D%E5%B9%B6%E6%8E%92%E6%9F%A5%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F)解释每进程 object-relational mapping (ORM，对象关系映射) 连接池与 Session 的使用边界；[可观测性、SLO 与事件响应](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)说明阶段信号怎样支持饱和判断。

> [!info]- 来源
> - Little 定律及其有限均值、严格平稳条件：[Little, “A Proof for the Queuing Formula: L = λW,” Operations Research 9(3), 1961](https://pubsonline.informs.org/doi/abs/10.1287/opre.9.3.383)，DOI `10.1287/opre.9.3.383`；核对于 2026-11-12。文中只把它用于均值与单位一致的演算，不据此推导尾部或安全容量。
> - `QueuePool` 同时连接上限 `pool_size + max_overflow`、常驻连接数、异步池与 SQLite 特例：[SQLAlchemy 2.1.8, Connection Pooling](https://docs.sqlalchemy.org/en/21/core/pooling.html)，当前版本与官网文档核对于 2026-11-12。示例明确配置两个值，不依赖默认值。
> - 服务级目标与用户可见可靠性：[Google SRE Workbook, Implementing SLOs](https://sre.google/workbook/implementing-slos/)，核对于 2026-11-12；压测方案和 70% 利用率是本合成案例的工程假设。
> - 异步请求已接受但尚未完成的 HTTP 语义：[RFC 9110 §15.3.3](https://datatracker.ietf.org/doc/html/rfc9110#section-15.3.3) 定义 202 Accepted；受理事务先提交才返回，是本案例附加的持久性合同。令牌桶的 `rT+b` 关系见 [RFC 2216 §2](https://datatracker.ietf.org/doc/html/rfc2216#section-2)；该 RFC 描述数据流量上界，本例把它改作“每个新逻辑 job 一枚令牌”的准入模型。
> - 过量请求与临时不可用的 HTTP 状态码：[RFC 6585 §4](https://datatracker.ietf.org/doc/html/rfc6585#section-4) 定义 429 Too Many Requests；[RFC 9110 §15.6.4](https://datatracker.ietf.org/doc/html/rfc9110#section-15.6.4) 定义 503 Service Unavailable。本文把速率令牌耗尽映射为前者、等待槽全满映射为后者，是示例 API 的状态映射，不是必须的数据库或队列实现。
> - 等待队列在持续过载时会增加等待时间并占用资源：[Google SRE Book, Queue Management](https://sre.google/sre-book/addressing-cascading-failures/#queue-management)，核对于 2026-11-12。该来源解释队列与过载，不给出本例 240 的 SLO；这个数量须由本服务允许的等待时长和负载测试选择。
> - 同 key 新意图的唯一胜者可依赖数据库唯一约束；[PostgreSQL 18, 63.5 Index Uniqueness Checks](https://www.postgresql.org/docs/18/index-unique-checks.html) 说明未提交冲突行可能让插入方等待并复查。不同 key 争最后一槽则靠所有受理者共用的额度行：[PostgreSQL 18, 13.2.1 Read Committed](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-READ-COMMITTED) 说明并发 `UPDATE` 等待已锁行后会在更新版本上重新检查条件。本文不指定 PostgreSQL 为唯一实现；事务数据库若不能提供等效的唯一性仲裁和原子条件更新/行锁，不可照搬该额度行设计。
> - 本页所有负载、预算、速率、保留期及对象大小均为教学设定；百分比和容量运算由这些显式假设重算，不是线上观察结果。
## 29. Web 服务如何限制拒绝服务的影响？

denial of service (DoS，拒绝服务) 会用流量、连接或昂贵请求耗尽服务资源，让正常请求得不到响应；distributed denial-of-service (DDoS，分布式拒绝服务) 则由多个来源同时施压。能否缓解，取决于哪项资源先到上限，以及攻击流量到达了哪一层：如果上游链路已被占满，应用里的限流代码就收不到请求。

本例的报表对外提供 application programming interface (应用程序接口，API)，以 Hypertext Transfer Protocol (超文本传输协议，HTTP) 接收读取请求。边缘代理可以组合 Content Delivery Network (内容分发网络，CDN) 和 Web Application Firewall (Web 应用防火墙，WAF) 等服务；这些组件只在请求实际经过它们时才能发挥作用。

**合成案例。** `user-17` 有权读取 `tenant-a` 的报表 `42`。请求 `GET /reports/42?days=7` 只做短范围读取，按本例估算为 1 个工作点；`days=365` 会做长范围汇总，估算为 4 点。工作点只是本例的相对成本单位，不等于处理器秒或查询数。正常流量从 Internet Service Provider (互联网服务提供商，ISP) 经接入链路到边缘代理、报表 API 和数据库；上游清洗不是默认路径，只有 ISP 在应急时改路到清洗服务，清洗后的流量才继续到边缘。接入链路容量设为 1 Gbit/s；拟采用的 API 全局工作预算为突发 80 点、持续 40 点/秒，同时最多运行 12 个长汇总、等待队列最多 6 项。这些数值只供推演，没有对真实服务做过负载测试，不能直接当容量建议。

![请求经过的层次、各层可观察信号和可执行的减压位置](../../engineering-foundations/security/resources/web-availability-and-ddos-protection-boundaries.svg)

### 过载发生在哪一层，就在哪一层减压

先把链路利用率、边缘请求、API 工作量和数据库等待放在同一时间线上，再选择该层能执行的动作。单独看到流量升高或客户端失败，不能判断应用已经收到请求，也不能证明某个来源地址就是攻击者。

| 阶段与同时观察到的信号 | 解释与处理 |
| --- | --- |
| **平常流量。** 链路约 300 Mbit/s（容量的 30%）；边缘约 200 个 HTTP 请求/秒，其中进入报表 API 的短读取约 20 个/秒，即约 20 点/秒；API 与数据库等待稳定 | 这是本例基线，不是其他服务的正常值。这里的 200 个/秒是边缘总量，不是报表 API 的计费输入；20 点/秒低于拟采用的 40 点/秒全局持续预算。保留按链路、边缘、路由和数据库资源分层的时间序列。 |
| **网络洪泛。** 上游清洗尚未启用时，ISP 在其网络入口观测到约 1.4 Gbit/s 原始流量；服务接入接口容量为 1 Gbit/s，接口遥测显示占用 100% 且丢包上升；外部探针失败，API 请求数和数据库负载没有相应上升 | 1.4 Gbit/s 是清洗前 ISP 侧观测值，不是接入接口实际吞吐。接口饱和和丢包由接口遥测另行证实。通知 ISP/托管商按预案启用上游清洗并改路；应用限额和扩容碰不到未到达应用的流量。 |
| **应用洪泛。** 上游清洗和改路已生效；接入接口观测约 620 Mbit/s（容量的 62%），丢包回落，独立探针可到达边缘。应用侧工作预算和运行/等待上限启用前，边缘把每秒 250 个来自多个已认证主体且通过报表授权的长范围 HTTP 请求转给 API；数据库连接等待上升 | 此时有链路余量，过载转到应用和依赖。每次 4 点，入站工作约 1,000 点/秒，是拟采用的 40 点/秒全局持续预算的 25 倍；在昂贵查询前实施工作预算，并分别限制运行数与等待数。 |
| **降载后。** 链路和 API 错误下降；数据库等待、并发占用和队列年龄逐步回落；合法探针恢复 | 不因一次成功响应就撤掉规则。先用独立用户路径、容量信号和授权负例复验，再逐步撤销临时缓解。 |

这些观测是合成案例的输入，不是抓包、服务日志或压测结果。实践中要和该服务自身的正常基线、区域、路由和资源上限对照；合法突发也可能产生高请求数，攻击源还可能分散或伪装。把不同层的指标与外部用户探针并看，才能区分“流量没到 API”“请求到了但成本太高”和“依赖已排队”。

每种防护只能作用于它实际收到的流量：

| 层次 | 可用信号和控制 | 不能据此保证什么 |
| --- | --- | --- |
| ISP、托管商、上游网络 | 链路的比特率、包率、丢包及路由状态；预先约定上游清洗、封禁特定协议或流量改路 | 上游没提供清洗或改路时，源站应用无法恢复已被塞满的接入链路；清洗也须避免把合法用户一起丢弃。 |
| 边缘代理、CDN、WAF | 连接数、加密握手、请求大小、解析耗时和 HTTP 路由；限制头部/正文大小与超时，挡已识别的模式，缓存适合共享的公开表示 | Network Address Translation (网络地址转换，NAT) 会让多个合法用户共用一个地址，分布式来源也能绕开单来源地址阈值；规则看不到全部业务授权与查询成本。若请求可直连源站，也会绕过前置边缘。 |
| API 与业务逻辑 | 已认证主体、租户、路由、输入范围、估算工作量和响应延迟；按作用域限额，先授权再检查成本，在昂贵报表查询前限制并发 | 只按请求数计费会把一次廉价读取和一次长范围聚合算成同等工作；错误的用户范围或过低额度会误伤正常用户。 |
| 数据库、缓存、worker（工作进程）与队列 | 活跃连接和池等待、处理器使用率、队列长度及最老任务年龄；限制查询、并发、等待队列、执行时长和返回量 | 无界增加队列只会把过载延后，最终消耗内存、连接或存储并拉长恢复时间；应用降级也不能撤销已占满的上游网络。 |

边缘的 WAF 适合在它能看到请求的地方挡掉已知恶意模式或异常频率；它不是租户授权器，也未必能识别格式合法、却会触发昂贵查询的请求。不同边缘服务可检查的请求部分和超限处理方式也不同；例如 AWS WAF 可按请求部分大小匹配并阻止超限内容，但正文检查上限取决于前置服务；批量检查全部头部另有字节数与头部数量上限，单个头部检查不受这组批量限制。须明确配置超限时的规则行为，不能假设它检查了完整请求。CDN 可以吸收部分请求并从边缘返回重复的公开内容；租户私有报表不能作为未隔离的共享缓存对象返回。若架构依赖 CDN 作为唯一路径，还要限制源站只接受可信边缘转发的请求，否则攻击者可能绕过 CDN 直达源站。

应用在代理后看到的 `Forwarded` 或 `X-Forwarded-For` 字段，也不能直接当成可信客户端身份。RFC 7239 指出，转发链上任何节点（包括客户端）都可能修改 `Forwarded`；只有确认直连来源是可信代理、并让代理重写或正确维护字段后，才可据此使用来源地址。NAT 会让多个合法用户共用一个地址，僵尸网络又能分散来源，因此来源地址适合做早期信号或限额维度之一，不应是唯一额度键。

### 速率限制和工作上限怎样一起计算？

rate limit（速率限制）约束某个计数范围在一段时间内进入多少请求或工作点；quota（配额）约束较长周期内的总量；concurrency limit（并发上限）约束同一时刻运行多少操作；有界队列则限制已接受但尚未开始的工作。它们对应不同资源，不能互相替代。API 还要限制查询跨度、单次执行时间和结果大小，避免一个请求把资源占用拉得无限长。

本段单独演示账户令牌桶和“等令牌”的教学计算，不是主案例中的工作队列。假设一个账户的令牌桶初始有 8 点，每秒补充 4 点：20 个短读取同时到达且不开队列时，最多 8 个立即通过，其他 12 个拒绝；若这个教学示例另设最多 4 个请求等待令牌、下游有空槽且没有其他流量，令牌可每 0.25 秒再放行一个，到 `t=1` 秒边界时累计最多放行 `8 + 4 × 1 = 12` 点，仍有 8 个被拒绝。长汇总一次扣 4 点，因此单次突发最多放行 2 个；不是 8 个。桶满时，长度为 `T` 的窗口内最多可供给 `burst + rate × T` 点。该令牌预算上限不保证服务实际完成同样多的工作。

额度还要选对作用域。假设三个 API 进程各自维护一份同样的本地桶，每份都有 8 点突发、每秒补 4 点；各份桶在一秒内合计可供给 `3 × (8 + 4 × 1) = 36` 点。20 个单位成本请求在同一时刻按 `7、7、6` 分到三个进程，每份本地桶都能通过这一批，所以整个服务瞬间放行 20 点；按本例的单一账户策略，共享桶此刻原本只应突发放行 8 点。若预期是单一账户在一秒内最多消耗 12 点，就需要共享状态或分配总和不超过该额度的分片预算。共享计数会带来网络延迟和依赖可用性；选择前要明确计数近似到什么程度可接受。

每用户/租户的额度保护公平使用，全服务工作预算保护数据库总容量，二者叠加。若 250 个长汇总每秒到达，入站工作约 `250 × 4 = 1,000` 点/秒；当全局预算每秒补 40 点且全部分给这类请求时，稳态最多接受 `40 ÷ 4 = 10` 个/秒，其他业务工作会使实际上限更低，突发额度只能暂时延后拒绝。本例的主队列只存已通过身份和资源授权、已扣账户与全局工作预算、但暂时等运行槽的长汇总。受理时要原子地确认两级预算都有足够令牌，并预留一个运行位置**或**一个等待位置；前者可用就立即运行，运行槽已满但 6 个等待位尚有空位就入队。只有预算不足，或运行位和等待位都不可用时才快速拒绝；不要要求运行位与等待位同时空闲。若所有位置都空且各相关主体额度充足，80 点突发预算理论可支付 20 个长汇总，但 12 个运行位与 6 个等待位最多只收 18 个，共扣 72 点；位置先于令牌成为约束。运行上限 12 与队列上限 6 合计最多持有 18 个长汇总，不表示它们都能及时完成。

限流键要随认证阶段变化：未登录请求可先按连接、网络段和廉价端点策略限制；认证后再组合主体、租户、路由与估算成本。先做正文大小、语法等低成本检查，再认证与授权、估算已经验证过的请求成本，最后在昂贵查询前申请预算和执行槽。滥用防护不能把登录锁定做成攻击者可远程触发的封禁服务，也不能信任客户端自报的租户、权重或任意转发头。

图形人机验证可以为某些高滥用功能增加一道摩擦，例如限制自动化提交；它不能阻止填满上游链路的流量，也不能取代请求大小、连接、速率和工作量上限。OWASP 的 DoS 指引明确指出，人机谜题并不能防止 DoS 攻击。针对自动化滥用可以组合挑战、账户信誉和专用业务规则，但这只是应用层的一类控制。

正常业务的容量估算、数据库连接预算和异步任务准入见[如何估算并限制异步工作管线？](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)。本页的工作预算是在攻击者能分散请求时保持边界，不代表服务已测得的可持续吞吐量。

### 限额触发时如何让客户端和服务一起恢复？

当单个调用主体或其合同额度超限时，API 可以返回 `429 Too Many Requests（请求过多）`，并可用 `Retry-After` 告诉调用方何时再试；RFC 6585 也提醒，攻击期间为每个请求都生成 `429` 本身会消耗资源，服务不必对每个请求都如此响应，也可以在攻击时丢弃连接。若服务整体暂时无法处理，可以返回 `503 Service Unavailable（服务不可用）`，RFC 9110 允许附 `Retry-After` 建议等待时间。状态码表示当前响应的结果，不会自行清空排队工作或保证之后可用。

客户端应尊重等待提示和自身截止时间，并用有上限、带随机抖动的指数退避，避免许多客户端在同一秒重试形成第二波流量。不要让每一层代理和应用都自动重试同一失败，否则下游实际接收到的请求会倍增。对会产生副作用的 `POST`，按[请求超时后的结果确认与安全重试契约](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)核实幂等条件后再重放。对于会启动异步导出的写请求，只有持久接受后才返回本例合同中的 `202`；容量不足时应在承诺前拒绝，具体受理事务见容量页。

过载时的 load shedding（负载削减）是停止接纳暂时无法处理的新工作，先保住仍能可靠提供的路径。例如，本例可暂停 365 天汇总，给短范围读取保留容量；若产品允许，也可从按租户隔离并经授权的缓存提供带时效说明的旧快照。不能因为想“快速响应”就从共享 CDN 返回其他租户的报表；读缓存仍要走正确身份和授权边界。配置 WAF 规则、验证码或 CDN 单独无法确保 API 与数据库会恢复。

缓解动作至少要在以下证据同时改善后，才逐步撤掉临时规则：

1. ISP/托管商确认清洗路由已生效；清洗后的接入接口低于本案例的 1 Gbit/s 容量，丢包回落，来自独立网络的探针能稳定到达边缘。仅凭清洗后的 620 Mbit/s 不能判断原始洪泛已经结束；停用清洗或改回原路由前，还要看 ISP 侧清洗前流量和提供商的安全回切判断，切换中继续观察接口丢包。
2. 边缘请求数和回源率回落；源站拒绝非可信代理直连的检查通过；对公开静态资源的缓存命中增加时，没有把私有报表送入共享缓存。
3. API 的长汇总并发不超过 12、队列不超过 6 且队列年龄下降；数据库池等待与查询延迟回到基线附近。缓解时限额拒绝可能先上升；要同时看合法用户成功率、被拒工作和依赖负载，不能只看 API 错误下降。
4. 用 `user-17` 请求 `tenant-a` 的短范围报表，核对内容正确；用无权访问该租户的 `user-guest` 重复探测，仍按 API 合同拒绝。按本例策略消耗尽单主体令牌后应得到限额响应，而不是继续启动重查询。
5. 若 365 天汇总曾暂停，先给 `user-17` 小流量放开一次合法长汇总，核验结果、查询耗时、数据库等待、并发和队列；稳定后再逐步恢复正常长汇总准入，并持续观察这些依赖信号。短读取通过不能证明长查询已经恢复。
6. 客户端收到 `Retry-After` 后确实等待；临时应用/边缘限制分步放宽时，重复同一组短读、长汇总和无权探针，观察合法成功率、拒绝率、链路和数据库信号。若任一条件回退，就恢复刚放宽的策略并重新定位瓶颈；常驻工作预算和并发/队列上限仍按测得容量保留。

这里的判据是合成案例的恢复清单，不是对线上服务的实测。应急结束后保存开始/结束时刻、受影响路由、各层信号、提供商和边缘动作、拒绝/误伤情况与恢复探针结果，再据此调整常驻额度与预案。攻击路径记录和事后响应步骤可参考[如何从报表服务信号定位发布后的故障？](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)；本页不把一次 HTTP 成功当作全服务恢复的证明。

> [!info]- 来源
> - DoS/DDoS 多层攻击面、资源密集型输入、限速、ISP 与过滤服务边界，以及 CAPTCHA（图形人机验证）的功能滥用局限：[OWASP Denial of Service Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html)，Fundamentals、Analyzing DoS attack surfaces、Application attacks、Input validation、Rate limiting、ISP-Level remediations、Global-Level remediations；核对于 2026-11-13。
> - 流量基线、攻击指标、联系 ISP/托管商、上游过滤/CDN 与事后分析：[CISA、FBI、MS-ISAC, Understanding and Responding to Distributed Denial-of-Service Attacks](https://www.cisa.gov/sites/default/files/2024-03/understanding-and-responding-to-distributed-denial-of-service-attacks_508c.pdf)，2024-03，What Steps Before、How to Know、How to Respond、After an Attack；核对于 2026-11-13。具体步骤须按组织的上游服务与应急约定裁剪。
> - `429 Too Many Requests` 和攻击期间不必对每个请求都生成 `429`：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，§4、§7.2，2012-04；临时过载 `503` 与 `Retry-After`：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§10.2.3、§15.6.4，2022-06。
> - 过载时拒绝多余工作、限制连接负载与保护关键路径：[Google SRE Book, Handling Overload](https://sre.google/sre-book/handling-overload/)，Customer Quotas and Throttling、Criticality、Load from Connections、Conclusions；该书《Site Reliability Engineering: How Google Runs Production Systems》由 Google Research 记录为 O’Reilly 2016 年出版 ([书目记录](https://research.google/pubs/site-reliability-engineering-how-google-runs-production-systems/))。其中的实现经验不作为所有服务的固定配额。
> - 随机指数退避、限制重试次数，以及避免多层重试放大：[Google SRE Book, Addressing Cascading Failures—Retries](https://sre.google/sre-book/addressing-cascading-failures/#retries)，同属 2016 年版 SRE 书。
> - 令牌桶在时间窗 `T` 内的 `burst + rate × T` 供给上限：[IETF RFC 1363, A Proposed Flow Specification](https://www.rfc-editor.org/rfc/rfc1363.html)，Definition of Individual Fields 下的 Token Bucket Rate 和 Token Bucket Size，1992-09。这里引用其令牌桶模型说明算式，不表示该 1992 年提案是现代 API 限流的部署标准。
> - CDN 只应是实际请求路径的入口，并需保护源站免于被绕过：[AWS Best Practices for DDoS Resiliency, Protecting your origin (BP1, BP5)](https://docs.aws.amazon.com/whitepapers/latest/aws-best-practices-ddos-resiliency/protecting-your-origin-bp1-bp5.html)，核对于 2026-11-13；所列 CloudFront/VPC origin 配置是 AWS 的具体实现例，不是跨供应商要求。
> - 按请求正文/头部大小拦截超限内容及其检查字节范围：[AWS WAF, Oversize web request components](https://docs.aws.amazon.com/waf/latest/developerguide/waf-oversize-request-components.html)，核对于 2026-11-13。正文检查上限取决于前置 AWS 服务；批量头部检查另有大小/数量上限，单头检查不受该批量限制。允许超限内容通过时，WAF 未必检查完整组件；这是 AWS 配置例，不是所有边缘服务的统一行为。
> - 私有响应不得在共享缓存间复用的缓存指令：[IETF RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html)，§5.2.2.7，2022-06。应用是否另设授权隔离缓存仍属应用合同。
> - 代理转发地址头可能被链中节点或客户端修改：[IETF RFC 7239](https://www.rfc-editor.org/rfc/rfc7239.html)，§8.1，2014-06；nginx 的可信代理配置示例：[ngx_http_realip_module](https://nginx.org/en/docs/http/ngx_http_realip_module.html)，`set_real_ip_from` 与 `real_ip_header`，核对于 2026-11-13。
## 30. 怎样用最小反例定位报表授权回归？

报表平台工程师收到跨租户访问回归：`tenant-a` 读取自己的报表 42 应返回 200；已认证的 `tenant-b` 猜中同一个全局编号时只能得到 404。定位时先把这条需求改写成可观察的输入和输出，再提出能被反例推翻的根因假设。若 B 收到 200，就沿可信主体、Application Programming Interface (应用程序接口，API)路由参数、实际取数方式、返回对象归属及响应映射逐段核对，不能仅凭状态码或预设“数据库一定发了查询”猜根因。完整路由的可运行回归测试见[怎样用测试边界验证一次报表服务改动？](#31.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E6%B5%8B%E8%AF%95%E8%BE%B9%E7%95%8C%E9%AA%8C%E8%AF%81%E4%B8%80%E6%AC%A1%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E6%94%B9%E5%8A%A8%EF%BC%9F)；本页会比较其中用到的 Structured Query Language (结构化查询语言，SQL)条件。

![已认证的 tenant-b 请求同一报表；仅当 Session.get 和显式查询这两种实现本次都实际发出 SELECT 时，图才比较只按全局 report_id 会命中 tenant-a 的行并泄露 200，以及同时约束 tenant-b 和 report 42 后无匹配并按本例隐藏策略返回 404](../../engineering-foundations/architecture/resources/reading-debugging-report-scope.svg)

图只比较两种实现本次都实际发出 SELECT 时的路径：红列的 `Session.get()` 按全局主键读取，绿列的显式查询按租户与编号过滤。`Session.get()` 若从本会话 identity map (身份映射表)直接返回未完全过期的对象，就不会进入图示的 SQL 路径；此时应核对调用键、返回对象归属以及该对象是否进入响应。只有确认实际取得 A 的对象且响应映射使用了该对象，才能把漏掉的授权条件与越权 200 连起来。若查询条件和绑定值正确、结果为空，但响应仍含 A 的数据，就继续追查旁路缓存、备用读取或序列化分支。响应码提示结果，不单独证明故障位置。

### 先把症状变成可证伪假设

先固定这个合成模型：`report_id` 是全局主键，`tenant_id` 是资源所有者；表中有 `(tenant-a, 42, ready)`。假设一次重构把原有的租户范围查询：

~~~python
report = session.scalar(
    select(Report).where(
        Report.report_id == report_id,
        Report.tenant_id == tenant_id,
    )
)
~~~

替换成按主键取对象：

~~~python
report = session.get(Report, report_id)
~~~

SQLAlchemy 的 `Session.get()` 按映射对象的主键身份取对象：使用默认选项时，如果对象已在当前 Session 的 identity map (身份映射表)中且未完全过期，它可能直接返回而不发 SELECT；若对象不在 identity map 中或已完全过期，才会按主键查询。显式设置 `populate_existing=True` 也会强制查询。两种读取路径都不会自动加上当前主体的租户授权条件。因为本例把 `report_id` 设为全局主键，`session.get(Report, 42)` 是合法主键读取，但不是所有权检查。若实际表用复合主键，应把相应键元组交给 `get`；仍要另行验证主体是否有权访问该资源。

原测试只以 A 建立并读取自己的报表，所以在这次重构前后都可能通过；它证明了所有者能读，却没有区分授权边界。先列出该路由应满足的结果：

| 主体 | 输入 | 预期结果 |
|---|---|---|
| `tenant-a` | `GET /api/reports/42` | 200，返回自己的报表 42 |
| `tenant-b` | 同一请求，主体已由可信认证接缝给出 | 按本例隐藏策略返回通用 404；正文不含 A 的归属或报表数据，且与请求不存在的 43 相同 |
| 无有效主体 | 同一请求 | 401，由本例的认证入口拒绝，并带适用的 `WWW-Authenticate` 认证质询 |

最小反例只有两件东西：数据库里那条属于 A 的 42，以及一次可信主体 B 对相同路由的读取。要验证本例隐藏存在性的策略，还需比较 B 请求已存在的 A/42 与确实不存在的 43，确认状态和通用正文相同；只看 404 状态码不能证明正文不含 A 的归属或数据。然后按实测结果缩小调查范围：

| B 的观察 | 它能说明什么 | 接下来核对什么 |
|---|---|---|
| 得到 200 | 保护条件可能丢失，但还不能单凭状态码定根因 | 确认当前主体、实际入口、取数调用及结果归属、缓存命中和响应映射 |
| 得到 404 | 状态码符合预期，但仍需确认响应没有带出 A 的数据 | 检查测试是否走到同一入口、确实使用 B、装入 A/42 数据，以及响应对象归属和正文；若要验证隐藏存在性，再与不存在的 43 比较 |

若 B 得到 200，先追踪这次实际取数：认证依赖是否给出 B，路由是否把 `tenant-b` 与 42 传下去，读取调用究竟返回了什么，响应是否真的采用了该对象。若发出了 SQL，就核对最终谓词和绑定值；若 `Session.get()` 从 identity map 直接返回，就核对调用键和对象归属。只有实际取得 A 的行或对象并确认它进入 200 响应，才能证实这条授权回归。若 SQL 正确限定租户且查无可见行，但响应仍含 A 的数据，继续追踪旁路缓存、备用读取或序列化分支；不要把反例结果本身当作根因证据。

### 沿调用路径找出丢失的条件

从公开入口向数据读取方向追踪同一个请求：

1. 确认请求到达哪条公开路由，是否经过认证依赖。
2. 核对依赖返回的主体来自已验证会话或令牌，而非任意客户端字段。
3. 查看路由是否把 `report_id` 和可信主体的 `tenant_id` 都传给数据层。
4. 检查实际取数方式和参数；若执行查询，再核对最终 SQL 或 object-relational mapping (对象关系映射，ORM)条件与绑定值。确认返回对象归属，以及 cache (缓存)是否绕过同一授权范围。
5. 追到错误映射和序列化，确认“查无当前主体可见行”没有被备用分支改成成功响应。

在这个例子中，路由仍然拿到了 `tenant_id`，但 `session.get` 只按全局主键身份取记录，没有用这个租户值。修正数据库查询时，要把报表编号与可信租户值一起作为条件：

~~~python
report = session.scalar(
    select(Report).where(
        Report.report_id == report_id,
        Report.tenant_id == tenant_id,
    )
)
~~~

对实际代码还要核对 ORM 生成的查询或条件构造，确认两个绑定值进入最终查询，而不是只在调用者局部变量中存在。若通过 identity map 直接拿到对象，则确认查询分支没有执行，并按同一主体范围验证对象归属。若成功响应 cache 键只含 `report_id`，修好数据库查询仍可能被缓存命中绕开；缓存返回之前也必须执行同一主体范围检查。逐次授权规则、查询与缓存边界见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

修完后重放同一入口和输入：A 仍为 200；B 对 A/42 与不存在的 43 都得到通用 404，正文不含 A 的归属或报表数据。匿名请求按本例入口策略为 401；真实认证方案还必须返回并测试适用的 `WWW-Authenticate` 质询。再检查相邻参数校验、错误映射和缓存路径，确保修正没有改变不相关响应或留下另一条绕行路径。真实路由、SQLite 查询及测试夹具的完整执行例子由[测试边界页](#31.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E6%B5%8B%E8%AF%95%E8%BE%B9%E7%95%8C%E9%AA%8C%E8%AF%81%E4%B8%80%E6%AC%A1%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E6%94%B9%E5%8A%A8%EF%BC%9F)承担；该测试页明确了 SQLite 和 TestClient 不能代表生产数据库或真实网络的范围。

### 独立阅读实现与测试

先从需求列出拒绝条件，再分别阅读实现和测试。实现侧要看改动后的公开路由、调用者、认证依赖、实际读取 (无论 SQL 查询还是身份映射表返回)、事务、缓存和响应分支；测试侧要确认输入主体可信且归属不同、测试经过被修改的入口、fixture (测试夹具)接上预期数据库，断言检查了不能发生的成功响应。模型或生成式改动的实现和测试可能共用一个遗漏假设，因此测试全绿并不表示漏掉的授权条件已经被检查。

对这次回归，要能把四项证据接起来：主体 A/B 的实际输入、HTTP 状态与正文、改动前后的查询条件、以及断言失败/恢复的回归测试。若把租户谓词删掉后，所有者测试通过而 B 的 404 断言失败，就证明测试能区分这两种实现。数据库约束、消息代理重投或部署装配需要额外结论时，先核实测试是否使用了目标数据库、真实消息代理或部署路径；模拟会话、本地重复调用和健康探针只覆盖各自接缝。测试层如何匹配具体失败边界见[怎样用测试边界验证一次报表服务改动？](#31.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E6%B5%8B%E8%AF%95%E8%BE%B9%E7%95%8C%E9%AA%8C%E8%AF%81%E4%B8%80%E6%AC%A1%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E6%94%B9%E5%8A%A8%EF%BC%9F)。

> [!example] 修复前后复验同一反例
> - **输入：** 数据库只有 A 持有的全局 `report_id=42`；认证依赖为请求给出可信主体 B。
> - **修复前 (重构之后)：** `session.get(Report, 42)` 可能从 identity map 返回 A/42，也可能按全局主键查询。确认实际返回的对象属于 A，且该对象进入 B 的 200 响应，才定位到这条越权路径；是否发出 SQL 要以本次执行为准。
> - **修复：** 用 `report_id=42` 和可信主体的租户值 `tenant-b` 同时过滤。
> - **修复后：** A 仍读到自己的行并得到 200；B 对已有的 A/42 与不存在的 43 都得到相同通用 404，正文不含 A 的归属或报表数据；匿名请求按本例策略得到 401，真实认证实现还要带适用的质询。
>
> 这些输出只覆盖所测路由与缓存状态。后台导出、其他查询入口和缓存各自有独立访问路径，应按相应数据边界核对。

在共享分支保留聚焦修复，再用[Git 怎样把通过验收的报表改动变成可追溯提交？](#32.%20Git%20%E6%80%8E%E6%A0%B7%E6%8A%8A%E9%80%9A%E8%BF%87%E9%AA%8C%E6%94%B6%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%94%B9%E5%8A%A8%E5%8F%98%E6%88%90%E5%8F%AF%E8%BF%BD%E6%BA%AF%E6%8F%90%E4%BA%A4%EF%BC%9F)记录源码快照。评审应独立看实际差异、需求边界和测试覆盖；具体审批与合并门槛由仓库政策决定。

> [!info]- 来源
> - SQLAlchemy 2.0 官方 [Session.get API](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.get)：若主键对象在身份映射表且未完全过期，默认调用可不发 SQL；过期对象会刷新，`populate_existing=True` 会强制查询；复合主键可用元组或字典表示。核对于 2026-11-12；实际包版本为 2.0.44。
> - IETF [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) §§15.5.2、15.5.4–15.5.5：401 必须含适用 `WWW-Authenticate` 质询；服务可用 404 隐藏当前禁止访问的资源，但正文是否披露归属仍需由响应与测试保证。核对于 2026-11-12。
> - GitHub 官方 [Reviewing proposed changes in a pull request](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request) 与[Giving reviews](https://docs.github.com/en/pull-requests/concepts/giving-reviews)：支持阅读文件差异、对具体改动评论和提交审查；代码根因与修复结论来自本页合成例的查询和测试证据。核对于 2026-11-12。
> - 租户授权的完整规则与缓存边界由[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)承担；本文只追踪一次范围条件回归。
## 31. 怎样用测试边界验证一次报表服务改动？

报表平台的合成案例有两条需要验证的契约：`tenant-a` 读取自己的报表 42 得到 200；已认证的 `tenant-b` 猜中同一个全局 ID 时得到 404。重复处理同一个导出任务时，数据库只能提交一次有效状态转换，已完成任务保留第一次写入的结果键。后面的 SQLite 例子只检查数据库行，不写入或读取对象存储；它不证明结果对象存在，也不证明物理上传只发生一次。测试要把这些失败条件变成可观察的断言，不能只让实现和它自己生成的成功路径测试一起通过。

测试边界由“哪种失败可能发生”决定。用 Application Programming Interface (应用程序接口，API) 集成和数据库集成时，分别把真实路由、测试选定的身份接缝和选定数据库纳入测试；只有要证明 broker (消息代理) 的发布、重投或确认，才需要对应的消息代理测试；只有问题可能由部署装配引起，才需要近生产端到端旅程。本文用 SQLite 演示路由与 Structured Query Language (结构化查询语言，SQL) 的本地证据，不把它扩展成 PostgreSQL、消息代理或生产身份系统的证据。

### 先把风险与可证明的边界对应起来

从需要守住的业务条件出发，挑一个包含实际故障边界的最小环境，并先写清输入和可观察结果。下表是互补的检查位置，不是每个改动都要依次跑完的固定测试层级：只有较低边界不能证明目标属性时，才再引入更完整的环境。

| 要排除的失败 | 测试边界 | 能看到的证据 | 仍不能据此声称 |
|---|---|---|---|
| 租户 A/B 的纯访问规则判断颠倒 | 单元测试 | 给定可信主体和资源归属，规则返回允许或拒绝 | 实际路由一定调用了这条规则 |
| 路由忘记传租户条件、状态码或响应字段错误 | API 集成 | 实际路由、所选身份接缝 (本例直接定义测试接缝)、参数校验、数据库查询、序列化和错误映射一起工作 | 真实网络、生产身份提供方或生产数据库方言正常 |
| 唯一约束、回滚或条件更新的实际数据库行为错误 | 数据库集成 | 选定数据库执行真实表结构和 SQL | 另一种数据库有相同类型、锁或并发行为 |
| 新响应不兼容已发布客户端 | 契约测试 | 当前响应与已发布 schema (结构定义) 或代表性旧客户端比较 | 只检查本次生成的 OpenAPI 就兼容旧客户端 |
| 消息发布、重复投递或 acknowledgment (消费者确认，ACK)路径丢失、重做 | 消息代理集成 | 选定消息代理及其路由、持久性和确认设置下的实际交接 | 在本地把 worker (工作进程)函数调用两次就等于代理完成了重投 |
| 只有服务装配后出现的故障 | 近生产端到端 | 受控的身份、API、数据库、队列和工作进程旅程 | 一个健康探针就证明用户旅程正确 |

前端组件和浏览器边界另见[前端测试怎样证明报表排序、历史恢复和发布产物正确？](../../frontend/testing/frontend-testing.md)。本篇重点放在服务路由、持久化和消息交付。

### 用实际路由重放跨租户反例

测试用 FastAPI 的 dependency injection (依赖注入)把测试主体交给同一个路由。完整示例直接定义 `tenant_from_test_header` 测试接缝，用 `X-Tenant-ID` 让两种主体走同一入口；它不是生产认证实现。已有 FastAPI 路由可在测试中覆盖认证依赖，同时保留真实路由；生产身份仍必须来自已验证的登录上下文，不能信任客户端任填的租户头。示意表把 `report_id` 设为全局主键、`tenant_id` 设为所有者；若实际 schema 使用复合主键，测试要按真实键改写。

关键查询同时约束当前租户和报表 ID。下面展示查询和可观察断言；完整 FastAPI、SQLite 与 pytest 夹具放在折叠示例中。

~~~python
row = connection.execute(
    text("""
        SELECT report_id, state FROM reports
        WHERE tenant_id = :tenant_id AND report_id = :report_id
    """),
    {"tenant_id": tenant_id, "report_id": report_id},
).mappings().first()

owner = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-a"})
other = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-b"})
missing = client.get("/api/reports/43", headers={"X-Tenant-ID": "tenant-b"})
assert owner.status_code == 200
assert owner.json() == {"report_id": 42, "state": "ready"}
assert other.status_code == 404
assert missing.status_code == 404
assert other.json() == missing.json() == {"detail": "report not found"}
~~~

`TestClient` 在进程内调用 FastAPI 应用，不建立真实 HTTP socket (套接字)；SQLAlchemy 仍把参数化查询交给 SQLite 执行。所有者查到自己的行得到 200，另一租户查无可见行得到通用 404。本例把生产身份边界设为 Bearer 认证，测试依赖用 `X-Tenant-ID` 注入已认证主体；未注入主体时，它模拟认证层返回 401 和 `WWW-Authenticate: Bearer realm="reports"`。测试会检查这个质询头，真实令牌的校验由认证层自己的测试负责。

> [!example]- 完整 FastAPI + SQLite 测试夹具与 pytest 检查
> 每个测试由默认的 function scope (函数作用域)fixture (测试夹具)建立独立内存数据库和应用。`StaticPool` 让本例各次串行访问复用同一 SQLite 连接，使测试客户端调用的路由读到已准备的数据；它不支持并发事务，不能把这组设置用于并发测试。
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
>             raise HTTPException(
>                 status_code=401,
>                 detail="authentication required",
>                 headers={"WWW-Authenticate": 'Bearer realm="reports"'},
>             )
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
>     missing = client.get("/api/reports/43", headers={"X-Tenant-ID": "tenant-b"})
>     anonymous = client.get("/api/reports/42")
>     malformed = client.get(
>         "/api/reports/not-a-number", headers={"X-Tenant-ID": "tenant-a"}
>     )
>
>     assert owner.status_code == 200
>     assert owner.json() == {"report_id": 42, "state": "ready"}
>     assert other.status_code == 404
>     assert missing.status_code == 404
>     assert other.json() == missing.json() == {"detail": "report not found"}
>     assert anonymous.status_code == 401
>     assert anonymous.headers["www-authenticate"] == 'Bearer realm="reports"'
>     assert malformed.status_code == 422
>
>
> def test_openapi_declares_scope_error_responses(client):
>     operation = client.get("/openapi.json").json()["paths"][
>         "/api/reports/{report_id}"
>     ]["get"]
>     assert {"200", "401", "404", "422"} <= set(operation["responses"])
> ~~~
>
> 保存为 `test_report_scope.py` 后运行 `python -m pytest -q test_report_scope.py`。OpenAPI 检查只说明本应用当前声明哪些响应码；若要保证旧客户端兼容，仍须与已发布 schema 或代表性旧客户端比较。

本例路由没有声明 `response_model`；本机运行生成的 200 OpenAPI 响应 schema 是 `{}`，因此没有把 `state` 标成必需字段。上面的 OpenAPI 用例只检查响应码，不能证明删掉 `state` 会被 schema 拦住。所有者的精确 JSON 断言会在本例中发现该字段被删，但要验证已发布客户端兼容性，仍要用标明必需字段的已发布 schema 或固定旧客户端响应契约来检查。

本例把 404 作为隐藏资源的策略：B 请求 A 实际拥有的 42，与 B 请求表中不存在的 43，必须得到相同状态和通用正文；断言同时确认正文不含 A 的租户归属或报表状态。只看状态码不能证明响应没有泄露。若查询退回只按全局主键 `report_id` 读取，`tenant-a` 的原所有者测试仍会通过，但 `tenant-b` 会得到 200，新增的跨租户输入才会暴露漏掉的租户谓词。示例的 `session.get(Report, 42)` 同样只按全局主键取行，不等于它验证了当前主体的权限；实际表若使用复合主键，读取参数和反例都应依真实键定义调整。

认证得到可信主体之后，仍要对具体报表和动作逐次授权；测试头不改变这一生产边界。授权模型和缓存命中也要保留当前租户范围，见[如何逐次授权租户内的报表资源？](#5.%20%E5%A6%82%E4%BD%95%E9%80%90%E6%AC%A1%E6%8E%88%E6%9D%83%E7%A7%9F%E6%88%B7%E5%86%85%E7%9A%84%E6%8A%A5%E8%A1%A8%E8%B5%84%E6%BA%90%EF%BC%9F)。

参数校验、认证和旧客户端兼容也分别验收：带可信测试主体的 `GET /api/reports/not-a-number` 由整数路径参数校验返回 422；无主体请求按本例策略得到 401。用例同时检查 401 的 `Bearer realm="reports"` 质询；若真实服务采用另一种认证方案，质询及对应断言也须与该方案一致。

#### 用数据库检查重复提交与重复处理

入口重放同一 `(tenant_id, request_key)` 且参数相同的提交时，应用应返回第一次创建的 `job_id`；同键但参数不同，则按 API 契约拒绝。消费者对该 `job_id` 重复收到任务时，条件更新应只允许一次从 `pending` 到 `done` 的状态转换。下面的 SQLite 片段分别展示这两个数据库行为：`jobs` 的任务由首条插入创建，`work` 的行由脚本独立预置，并非从 `jobs` 自动生成；冲突插入只检查唯一键是否保留原 `job_id`，并不实现应用层读取后返回原任务的逻辑。

固定本次 `job_id = "job-demo-731"`，结果键为 `private/reports/job-demo-731.csv`。提交表 `jobs` 初始为空；消费表 `work` 已单独预置该任务，状态是 `pending`、计数为 0、结果键为空。逐步读取数据库就能观察下面的区别：

| 操作 | 数据库返回的信号 | 操作后保留的状态 |
|---|---|---|
| 首次插入 `(tenant-a, export-42, job-demo-731)` | 影响 1 行 | `jobs` 保存该完整任务行 |
| 同一租户和请求键，换成候选任务 `job-duplicate` 再插入 | `SQLITE_CONSTRAINT_PRIMARYKEY`；脚本调用 `rollback()` 结束本次事务 | 原任务行仍在，不能被替换或多出一行 |
| 首次处理 `job-demo-731`，只更新 `status='pending'` 的行 | 影响 1 行 | `work` 变为 `done`、计数 1、写入上述结果键 |
| 再次处理同一任务，沿用相同条件 | 影响 0 行 | 已完成的任务行与第一次写入的结果键不变 |

冲突测试还要断言异常类型和完整原行。只数“一行”会让 `INSERT OR REPLACE` 偷换 `job_id` 后仍通过；只捕获任意 `IntegrityError` 又会把非空约束失败误当成重复主键。消费侧检查的是本地条件更新，不能据此判断消息代理已经重投或确认。

> [!example]- 用标准库 SQLite 重放唯一键和条件更新
> 这段独立示例只执行本地数据库约束；它没有连接消息代理，也没有并发工作进程。
>
> ~~~python
> import sqlite3
>
> db = sqlite3.connect(":memory:")
> job_id = "job-demo-731"
> result_key = f"private/reports/{job_id}.csv"
> db.executescript("""
> CREATE TABLE jobs (
>     tenant_id TEXT NOT NULL,
>     request_key TEXT NOT NULL,
>     job_id TEXT NOT NULL,
>     PRIMARY KEY (tenant_id, request_key)
> );
> CREATE TABLE work (
>     job_id TEXT PRIMARY KEY,
>     status TEXT NOT NULL,
>     processed_count INTEGER NOT NULL,
>     result_key TEXT
> );
> """)
> db.execute(
>     "INSERT INTO work VALUES (?, 'pending', 0, NULL)",
>     (job_id,),
> )
> db.commit()
>
> first_insert = db.execute(
>     "INSERT INTO jobs VALUES (?, ?, ?)",
>     ("tenant-a", "export-42", job_id),
> ).rowcount
> db.commit()
> try:
>     db.execute(
>         "INSERT INTO jobs VALUES (?, ?, ?)",
>         ("tenant-a", "export-42", "job-duplicate"),
>     )
> except sqlite3.IntegrityError as error:
>     error_name = error.sqlite_errorname
>     db.rollback()
>     assert error_name == "SQLITE_CONSTRAINT_PRIMARYKEY", error_name
> else:
>     db.rollback()
>     raise AssertionError("duplicate key did not raise primary-key conflict")
>
> jobs = db.execute(
>     "SELECT tenant_id, request_key, job_id FROM jobs"
> ).fetchall()
> assert jobs == [("tenant-a", "export-42", job_id)]
>
> first_update = db.execute(
>     "UPDATE work SET status='done', processed_count=processed_count+1, "
>     "result_key=? WHERE job_id=? AND status='pending'",
>     (result_key, job_id),
> ).rowcount
> db.commit()
> second_update = db.execute(
>     "UPDATE work SET status='done', processed_count=processed_count+1, "
>     "result_key=? WHERE job_id=? AND status='pending'",
>     (result_key, job_id),
> ).rowcount
> db.commit()
>
> inserted_rows = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
> final_work = db.execute("SELECT * FROM work").fetchone()
> assert (first_insert, inserted_rows) == (1, 1)
> assert (first_update, second_update) == (1, 0)
> assert final_work == (job_id, "done", 1, result_key)
> print(first_insert, inserted_rows)
> print(first_update, second_update, final_work)
> ~~~
>
> 预期输出为 `1 1` 和 `1 0 ('job-demo-731', 'done', 1, 'private/reports/job-demo-731.csv')`。这只证明数据库最终保留一个对象键引用，不代表真的上传过对象或测试了消息代理；SQLite 的内存连接和唯一约束细节见来源，也不要用这条串行轨迹宣称多个数据库进程下的争用已测过。

如果重复任务还会付款、发邮件或通知其他服务，本地条件更新不会回滚已经发生的远端副作用。transactional outbox (事务发件箱)把业务行与待发送意图一同持久化，relay (转发进程)恢复后仍可能再次发送；外部动作还要使用对端认可的幂等键，或通过权威记录确认并修复重复。仅有 outbox 不足以防止远端重复付款。超时后的未知结果与安全重试见[请求超时后如何确认结果并安全重试？](#14.%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)；账户报表任务与 outbox 的完整交接见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)；publisher confirm (发布者确认)和 consumer acknowledgement (消费者确认)的范围见[报表任务的发布确认、消费者确认与业务完成各证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 从测试证据接到可发布的变更

测试结果应能追溯到变更、代码、测试输入和实际产物。Continuous Integration (持续集成，CI)先固定源码提交，再用该快照构建镜像；发布流程应验证并晋级同一份通过检查的镜像，不能把“源码上的测试通过”说成另一次重新构建的镜像也已验证。变更交付的完整路径见[如何晋级并回滚已验证的报表服务产物？](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)。

> [!info]- 来源与运行边界
> - FastAPI 官方 [Testing](https://fastapi.tiangolo.com/tutorial/testing/) 与 [TestClient 参考](https://fastapi.tiangolo.com/reference/testclient/)：说明客户端测试如何调用应用；TestClient 不建立实际 HTTP 套接字，核对于 2026-11-12。
> - FastAPI 官方 [Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)：可用 `app.dependency_overrides` 替换认证依赖同时保留真实路由；本例则在路由定义处直接接入测试身份，核对于 2026-11-12。
> - FastAPI 官方 [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)：响应模型会生成对应的 OpenAPI schema 并校验返回值；本例没有 `response_model`，所以运行得到的 200 schema 为 `{}`，核对于 2026-11-12。
> - pytest 官方 [Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)：fixture 注入和生命周期；本例使用默认的 function scope，核对于 2026-11-12。
> - SQLAlchemy 2.0 官方 [SQLite 方言：内存库、多线程与 StaticPool](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads-or-coroutines)：内存数据库与连接绑定；StaticPool 只适合完全串行访问，核对于 2026-11-12。
> - SQLite 官方 [CREATE TABLE](https://www.sqlite.org/lang_createtable.html)：主键和唯一约束；这里只演算本地 SQLite 实际行为，核对于 2026-11-12。
> - SQLite 官方 [ON CONFLICT](https://sqlite.org/lang_conflict.html) 与 [Result and Error Codes](https://www.sqlite.org/rescode.html)：`IGNORE` 可静默跳过冲突，`REPLACE` 可删除原冲突行；扩展约束码可区分主键与非空约束失败，核对于 2026-11-12。
> - IETF [RFC 6750 §3](https://www.rfc-editor.org/rfc/rfc6750.html#section-3)：Bearer 质询的认证参数；本例用 `realm="reports"` 标识保护空间。
> - IETF [RFC 9110 §15.5.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.2)：生成 401 时必须包含适用于资源的 `WWW-Authenticate`；本例模拟 Bearer 认证边界的质询并在测试中断言该头，核对于 2026-11-12。
> - AWS Prescriptive Guidance [Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)：outbox 的本地原子写入不消除重复消息，消费者还要能幂等处理，核对于 2026-11-12。
> - RabbitMQ 4.4 官方 [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)：发布确认与消费者 ACK 属于不同交接边界；本文不声称本例执行了 RabbitMQ，核对于 2026-11-12。
> - 实际运行版本：Python 3.11.13、FastAPI 0.128.0、Starlette 0.47.2、HTTPX 0.28.1、SQLAlchemy 2.0.44、pytest 9.0.2、SQLite 3.51.0。版本仅描述这次本地复现环境，不代表最新版本或 PostgreSQL、broker 集成结果。
## 32. Git 怎样把通过验收的报表改动变成可追溯提交？

修复 report 42 的租户条件并通过相关检查后，Git 能把已审查的源码快照变成可复查的提交。这个提交给构建系统提供固定输入，但它还不是部署产物：之后要记录由它构建出的镜像摘要，并验证、晋级那份镜像。Git 命令改变工作区、暂存区、提交或引用；它不撤销数据库迁移、已发布镜像或生产副作用。

branch（分支）是指向提交的可移动引用；working tree（工作区）保存文件，index（暂存区）保存下一次提交的快照，commit（提交）固定一棵树及父提交。本章采用普通分支工作方式：`HEAD` 指向当前分支，分支指向当前提交；成功创建提交后，分支移动到新提交。区分这几层，才能选择正确的恢复动作。

创建分支只建立一个指向提交的引用，`git switch -c <name>` 也不会把未提交的工作区或暂存区改动保存成快照。要在切换任务前保护这类改动，应先提交，或用 `git stash` 保存，再核对恢复后的状态。仅执行 `git add` 不会把改动保存成独立的提交或 stash。

下面只追踪同一个文件的三个版本：`v0` 是原内容，`v1` 加上租户限定，`v2` 又补了错误处理。表中每格是该层保存的文件内容，并非提交号。

| 执行到哪一步 | Working tree | Index | HEAD 提交中的文件 |
| --- | --- | --- | --- |
| 编辑为 `v1` | `v1` | `v0` | `v0` |
| 执行 `git add` | `v1` | `v1` | `v0` |
| 再编辑为 `v2`，没有再次 add | `v2` | `v1` | `v0` |
| 执行 `git commit` | `v2` | `v1` | `v1` |

`git add` 复制的是执行当时的内容。之后继续编辑，index 不会跟着变化；所以最后一步只提交了租户限定，错误处理仍是未暂存改动。`git diff` 对照工作区与 index，`git diff --cached` 对照 index 与 HEAD。提交前分别看两份差异，才能知道哪些改动会进入这次提交。测试通常读取 working tree；在 `v2` 上通过测试，不能据此认定只含 `v1` 的提交也通过。验收时要让被测内容与准备提交的快照一致；若工作区混有其他改动，可在隔离目录验证待提交快照。


### 把一个小修复明确放进暂存区

在示意仓库中，改动只包含 `src/reports.py` 的租户限定查询和 `tests/test_report_scope.py` 的非所有者断言。先查看仓库是否混有其他任务，再查看准确的差异：

~~~bash
git status --short
git diff -- src/reports.py tests/test_report_scope.py
~~~

逐文件暂存用于选择此次修复的路径；它会保留 index 中已经存在的其他暂存改动，也会收录所选文件当前的全部修改。因此必须检查完整的 `git diff --cached`：只应出现属于本次修复的文件与代码块，包含既有暂存内容的情况也一样。

~~~bash
git add src/reports.py tests/test_report_scope.py
git diff --cached
git diff --cached --check
git status --short
~~~

`git diff --cached --check` 检查差异中的空白错误和冲突标记。先对准备提交的同一份内容完成项目测试，再创建提交；若使用提交后的 CI 验收，则核对实际通过检查的提交 ID，之后才晋级产物。

~~~bash
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
| 多人已经基于该分支继续提交 | 先协调，通常不改写共享提交 | 其他人的分支仍基于旧提交；改写后的提交 ID 不同，需要重新整合两条历史 |
| 仓库需要保留合并节点 | 需要整合时使用 `merge --no-ff` | 普通 merge 在可快进时只移动分支；`--no-ff` 会为这次合并创建节点 |

例如仅有自己未推送的 `fix/report-tenant-scope` 分支，可以按团队约定 `git rebase origin/main`。也可以用 `git merge origin/main` 整合；如果当前提交是远端提交的祖先，它可以 fast-forward（快进），直接移动分支而不新增合并提交。若团队要求这次整合保留合并节点，可用 `git merge --no-ff origin/main`；如果双方已经无须整合，则不会凭空生成合并节点。merge 和 rebase 都可能产生冲突；不要用某种分支模型替代仓库现行策略。

发生冲突时，先看带冲突标记的源文件及 `git diff --cc`。在 report42 的例子里，必须保留当前主体与报表 ID 两个条件，再解决与远端其他调整的真实冲突。检查解决冲突后的文件，运行相应测试，再暂存并继续当前操作。下面这段针对正在进行的 rebase：

~~~bash
git add src/reports.py
git rebase --continue
~~~

若正在进行的是 merge，解决并暂存冲突后用 `git merge --continue` 完成合并；先看 `git status` 确认当前操作。

示例从干净工作区开始。合并未完成前可 `git merge --abort` 尝试重建合并前状态；如果开始合并时已有未提交改动，Git 在某些情况下无法完整恢复它们。变基未完成前可 `git rebase --abort`。不要把未理解的冲突整块接受为 ours 或 theirs。

### stash 与 cherry-pick 解决不同问题

临时切走时，`git stash push -m "report scope in progress"` 保存已跟踪文件的工作区和暂存区状态；默认不含未跟踪文件，需要时加 `-u`。`git stash apply` 默认重新应用改动但不保证恢复原先暂存状态；需要尽量恢复 index（暂存区）时用 `git stash apply --index`。`apply` 保留记录，`pop` 在应用成功后移除记录。应用后检查状态和冲突，不要把 stash 当成备份；重要工作还应保存在提交或其他持久位置。

`git cherry-pick <commit>`（挑选提交）把指定提交所引入的改动应用到当前分支，并创建一个新的提交。它适合把已审查的报表修复移到维护分支，但新提交 ID 不同，应记录实际运行的检查和部署构建对应的目标提交。

### 按变化所在层恢复

若只是暂存了不想提交的修改，用 `git restore --staged <path>` 将该路径的 index 内容恢复为 HEAD 中的版本，工作区内容保留。若只丢弃工作区的未暂存编辑，用 `git restore <path>` 将工作区该路径恢复为 index 中的版本；该路径内容会被覆盖。对已经提交的共享修复，用 `git revert <commit>` 添加一个反向提交，保留原提交供历史审计。普通提交可直接指定；撤销 merge commit 时须选择主线父提交，例如 `git revert -m 1 <merge-commit>`，并先检查这个反向差异以及后续合并会受什么影响。回滚共享历史时通常用 revert，不要直接把远端分支强制指回旧位置。

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

CI 可以在开发分支、PR 或共享分支上运行。发布流程应记录实际用于构建的提交；若仓库要求通过 PR 和状态检查后再发布，就把这些检查作为晋级条件。容器摘要和晋级过程见[Docker 如何把该提交构建成固定镜像？](#33.%20Docker%20%E5%A6%82%E4%BD%95%E6%8A%8A%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E7%9A%84%E6%BA%90%E7%A0%81%E6%9E%84%E5%BB%BA%E6%88%90%E5%8F%AF%E8%BF%90%E8%A1%8C%E9%95%9C%E5%83%8F%EF%BC%9F)与[如何晋级已验证的报表服务产物？](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)。

> [!info]- 来源
> - Git 官方手册：[status](https://git-scm.com/docs/git-status)、[diff](https://git-scm.com/docs/git-diff)、[add](https://git-scm.com/docs/git-add)、[commit](https://git-scm.com/docs/git-commit)，checked 2026-11-06：工作区、index 和提交差异。
> - Git 官方手册：[fetch](https://git-scm.com/docs/git-fetch)、[pull](https://git-scm.com/docs/git-pull)、[merge](https://git-scm.com/docs/git-merge)、[rebase](https://git-scm.com/docs/git-rebase)，checked 2026-11-06：远端跟踪、整合和历史重放。
> - Git 官方手册：[reset](https://git-scm.com/docs/git-reset)、[restore](https://git-scm.com/docs/git-restore)、[revert](https://git-scm.com/docs/git-revert)、[reflog](https://git-scm.com/docs/git-reflog)、[stash](https://git-scm.com/docs/git-stash)、[cherry-pick](https://git-scm.com/docs/git-cherry-pick)，checked 2026-11-06：各命令的状态影响和恢复范围；本机 Git 2.56.0。
## 33. Docker 如何把报表服务的源码构建成可运行镜像？

**案例背景。** Git commit（提交）`c4f2a91` 修复了报表 42 对 `tenant-a` 的读取授权。本章承接这份已检查的源码和依赖锁文件，说明怎样构建容器镜像、在本地 Compose 中组合 API、worker 与数据库，并观察镜像和容器状态。CI 发布时还要把本次 registry（镜像仓库）摘要交给部署流程；预发布、生产晋级和切流见[如何晋级并回滚已验证的报表服务产物？](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)。

报表服务的 application programming interface（应用程序接口，API）与异步 worker（工作进程）从同一份源码构建，但承担不同进程职责。Dockerfile（镜像构建文件）把受控源码、依赖与基础镜像变成 container image（容器镜像）：镜像以只读层保存程序及默认配置。container（容器）启动时，运行时在镜像上叠加该容器自己的可写层，再组合进程命令和运行配置；容器删除后，可写层中的改动也丢失，需跨容器保留的数据库文件应写入 volume（数据卷）。镜像不保存某个环境的数据库密码。image digest（镜像摘要）标识具体镜像内容；tag（可变标签）只是会移动的名字。Docker Compose 负责把容器接成服务、network（网络）与数据卷。

![同一受控提交分别进入本地 --load 检查和 CI --push 发布。两条路径各自生成摘要；只有 registry 路径经 imagetools inspect 核验后，才把远端摘要引用交给 Compose。](../../engineering-foundations/infrastructure/resources/docker-build-and-image.svg)

本地 `--load` 将镜像载入本机，供后续启动容器检查；CI 的 `--push` 把另一轮构建输出发布到 registry。两次构建即使来自同一提交，也不能假定得到相同摘要。下面分别跟踪这两条路径，最后把 CI 验证过的远端摘要交给运行环境。

### 按运行所需文件分层构建

一次 build（构建）从 build context（构建上下文）开始：Docker CLI（命令行客户端）将指定的文件集合交给 builder（构建器）。`.dockerignore` 在发送前按相对构建根目录的路径模式排除无关或私密文件；它不会代替 Git 的忽略规则，也不会把上下文之外的文件传进去。需要匹配任意层级的文件时用 `**/`，单写 `*.log` 等规则不等于递归匹配。通常先复制依赖锁定文件再复制源码，使源码变更不必重装依赖。BuildKit 根据指令及其输入复用 build cache（构建缓存）；某层输入改变时，该步骤及后续步骤需重做。缓存既不代表外部依赖仍最新，也不自动让构建可复现：基础镜像 tag、依赖索引或下载内容、平台和构建工具都可能变化，因此相同源码的独立重建仍可能生成不同镜像。

下面用官方 `python:3.15-slim` 镜像说明结构。实际应用先确认框架、依赖和 native extension（原生扩展）支持该解释器，再在每个 `FROM` 固定审核过的基础镜像 digest。`requirements.lock` 应覆盖直接和传递依赖、精确版本与 SHA-256；`pip --require-hashes` 会逐项校验下载内容。若没有适用 wheel（预构建安装包）而需从源码编译，构建阶段除 compiler（编译器）和 header（头文件）外，还要审核并控制包的 build backend（构建后端）及 build-time dependencies（构建依赖）；pip 会为源码包另建隔离构建环境，运行时依赖锁文件本身不锁定该环境。运行阶段只保留所需共享库。

~~~dockerfile
# syntax=docker/dockerfile:1
FROM python:3.15-slim AS deps
WORKDIR /build
COPY requirements.lock .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --prefix=/install --require-hashes -r requirements.lock

FROM python:3.15-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=deps /install /usr/local
COPY --chown=10001:10001 app ./app
USER 10001:10001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
~~~

两个 stage（构建阶段）都应使用已审核的基础镜像摘要：单平台固定对应平台 manifest digest；多平台可固定已核验的基础镜像 index digest，由每个 stage 按目标架构选择相同的平台 manifest。代码使用 tag 让结构容易读，生产 Dockerfile/构建参数还需以真实摘要固定它。`COPY --from=deps` 只带入运行依赖，非 root `USER` 降低应用进程的权限；应用若需要写文件，应明确把输出目录放到受控挂载点，不能依赖容器可写层跨替换保留。示例 Uvicorn 在容器内监听 `0.0.0.0:8080`，让容器网络接口可以接收映射流量；宿主机端仍可只发布到 `127.0.0.1:8080`。若应用只绑定容器内的 `127.0.0.1`，宿主机端口映射不能替它改变监听地址。`CMD` 是默认启动命令。Dockerfile 的 `RUN` 在构建时执行并把构建结果交给后续步骤；`CMD` 和 `ENTRYPOINT` 在容器启动时定义进程。使用 exec form（JSON 数组形式）可让应用作为 PID 1（容器内首进程）收到停止信号。若镜像定义了 `ENTRYPOINT`，Compose `command` 会替换 `CMD` 或追加到 exec-form `ENTRYPOINT`，不会自动改写 `ENTRYPOINT`；若 Compose `entrypoint` 非空，则镜像默认 `CMD` 被忽略。

`.dockerignore` 至少要排除版本库、虚拟环境、缓存、本机日志、真实 `.env` 与 secret（密钥）文件，例如：

~~~text
.git/
**/.git/
.venv/
**/.venv/
__pycache__/
**/__pycache__/
*.py[cod]
**/*.py[cod]
*.log
**/*.log
.env
.env.*
**/.env
**/.env.*
secrets/
**/secrets/
~~~

若私有依赖源需要认证，BuildKit secret mount（构建密钥临时挂载）只在某条 `RUN` 期间暴露文件，例如 `RUN --mount=type=secret,id=pip_config,target=/etc/pip.conf ...`，调用构建时用 `--secret id=pip_config,src=/安全路径/pip.conf`。不要把 token 写进 `ARG`、`ENV`、COPY 文件或 shell 命令参数；不要让 verbose 日志打印认证配置。secret mount 的挂载本身不会把密钥写入镜像层；`RUN` 中的命令仍可能把它复制到产物、输出到日志或发送到网络，builder 和依赖源也必须受信。

下面的 shell 示例假设运行环境提供 Bash、Docker Buildx 和 `jq`，构建上下文内有 `app/` 与 `requirements.lock`。本地单平台验证可以把结果载入本机 Docker Engine：

> [!example]- 本地构建：本次 metadata、inspect 与 history
>
> ~~~bash
> set -euo pipefail
> metadata_file="$(mktemp "${TMPDIR:-/tmp}/report-api-build.XXXXXX")"
> trap 'rm -f "$metadata_file"' EXIT
>
> docker buildx build \
>   --load \
>   --metadata-file "$metadata_file" \
>   --tag report-api:c4f2a91 \
>   .
> digest="$(
>   jq -er '
>     ."containerimage.digest"
>     | select(type == "string" and test("^sha256:[0-9a-f]{64}$"))
>   ' "$metadata_file"
> )"
> printf 'Local build digest: %s\n' "$digest"
> docker image inspect report-api:c4f2a91
> docker image history report-api:c4f2a91
> ~~~

示例从源码根 `.` 构建；执行前应确认 checkout（检出）正是 `c4f2a91`，工作区干净且根目录就是预期上下文。临时 metadata 避免 build 失败后误读上次摘要，`set -e` 使构建失败即停止，`jq -e` 要求本次输出有格式正确的 digest，并明确打印本地构建摘要。标签 `report-api:c4f2a91` 只是本地别名；tag 不会验证源码是否确为该提交。`docker image inspect` 查看本机镜像配置和已知摘要，`history` 查看构建层线索；历史不是镜像文件的完整审计，也不证明 registry 中的产物。`--load` 是 `--output=type=docker` 的 CLI 简写；本例只请求一个平台。多平台本地载入受 builder 和 Engine image store 约束。当前 Buildx 可在探测到目标 Engine 支持 OCI importer 时选择可导入多平台的路径；classic store 不支持本地多平台 index，containerd store 支持，但仍需确认当前 builder 与输出组合。不要把本机 metadata digest 当作 registry 已收到镜像的证明。

本地检查和发布是两条不同输出。生产候选由 CI 从同一经检查的 commit 干净检出后，通过 `--push` 单独构建并发布；以下脚本读取的 metadata 属于这次 push，不能拿前一段 `--load` 的摘要代替：

> [!example]- CI 发布：核验 registry 摘要后交给运行环境
>
> ~~~bash
> set -euo pipefail
> metadata_file="$(mktemp "${TMPDIR:-/tmp}/report-api-push.XXXXXX")"
> trap 'rm -f "$metadata_file"' EXIT
>
> docker buildx build \
>   --push \
>   --metadata-file "$metadata_file" \
>   --tag registry.example.com/team/report-api:c4f2a91 \
>   .
> digest="$(
>   jq -er '
>     ."containerimage.digest"
>     | select(type == "string" and test("^sha256:[0-9a-f]{64}$"))
>   ' "$metadata_file"
> )"
> registry_ref="registry.example.com/team/report-api@$digest"
> docker buildx imagetools inspect "$registry_ref"
> printf 'REPORT_IMAGE=%s\n' "$registry_ref"
> ~~~

CI 只在 `imagetools inspect` 通过后把打印出的完整 `registry@sha256:…` 值作为后续 Compose job 的 `REPORT_IMAGE`。Compose 插值中的 `${REPORT_IMAGE:?…}` 仅拒绝空值，不校验它一定是 digest；调用方要传入这次 push 核验的完整引用。多平台构建要从远端清单检查每个生产架构的 manifest digest；index 里还可能有 provenance 等非运行平台附件，不能把任意子项当成可启动的架构镜像。预发布和生产晋级同一已核验的 registry 摘要，不分别重建。

registry digest 固定镜像 manifest 或多平台 index 的内容，但不说明由哪个源码提交构成。构建记录应把确切 commit（提交）、依赖锁文件、基础镜像摘要、Buildx/BuildKit 版本、平台、构建参数、continuous integration（持续集成，CI）检查和 provenance（构建来源证明）连接起来。跨 `linux/amd64` 与 `linux/arm64` 晋级时，index digest 证明所包含的描述项映射，不证明每个平台子镜像已运行。应在对应生产平台的预发布目标运行并验收将部署的每个子摘要，或限制生产目标为预发布实际运行的平台；检查时区分平台镜像 manifest 与 provenance 等附件。

### 容器、服务网络与数据存留是不同状态

下图采用本地 Compose 的默认 bridge/NAT 配置。API、worker 和 PostgreSQL 通过服务网络互通；HTTP 暴露在宿主机端口，数据库文件写入命名卷。API 与 worker 共用前图核验过的 registry 引用，生产路由和密钥存储则由相应运行平台配置：

![本地 Compose 默认 bridge/NAT 拓扑：浏览器访问宿主机回环端口 127.0.0.1:8080，再转发到监听 0.0.0.0:8080 的 API；API 和 worker 使用同一份 registry digest，经 db:5432 连接 PostgreSQL，数据库文件保存在命名卷。](../../engineering-foundations/infrastructure/resources/docker-compose-runtime-topology.svg)

下面的 Compose Specification（Compose 规范）片段要求外部提供 `REPORT_IMAGE`，其值应是前面 `--push` 和远端 `imagetools inspect` 已核验的 `registry.example.com/team/report-api@sha256:…` 实际摘要，而非本地 `--load` 摘要。`${REPORT_IMAGE:?…}` 只检查非空；CI 或传值的人必须保证它是该次 push 的不可变引用。API 与 worker 使用同一镜像身份，后者只替换默认命令；Compose 片段本身不创建应用角色或执行结构迁移。

若只做本机开发，可把服务的 `image` 设为前面已载入的 `report-api:c4f2a91` 并设置 `pull_policy: never`，使用本机已有镜像；另选 `build: .` 则从当前目录重新构建。这两种开发配置都不作为 registry 发布的证据，下例继续沿用 CI 交付的摘要。

> [!example]- Compose 配置：共享镜像、独立身份与命名卷
>
> ~~~yaml
> services:
>   api:
>     image: "${REPORT_IMAGE:?set REPORT_IMAGE to an immutable image digest}"
>     ports:
>       - "127.0.0.1:8080:8080"
>     environment:
>       DATABASE_HOST: db
>       DATABASE_NAME: reports
>       DATABASE_USER: report_app
>       DATABASE_PASSWORD_FILE: /run/secrets/app_db_password
>     secrets:
>       - app_db_password
>     depends_on:
>       db:
>         condition: service_healthy
>
>   worker:
>     image: "${REPORT_IMAGE:?set REPORT_IMAGE to an immutable image digest}"
>     command: ["python", "-m", "app.worker"]
>     environment:
>       DATABASE_HOST: db
>       DATABASE_NAME: reports
>       DATABASE_USER: report_app
>       DATABASE_PASSWORD_FILE: /run/secrets/app_db_password
>     secrets:
>       - app_db_password
>     depends_on:
>       db:
>         condition: service_healthy
>
>   db:
>     image: postgres:18
>     environment:
>       POSTGRES_DB: reports
>       POSTGRES_PASSWORD_FILE: /run/secrets/db_admin_password
>     secrets:
>       - db_admin_password
>     volumes:
>       - report-data:/var/lib/postgresql
>     healthcheck:
>       test:
>         - CMD-SHELL
>         - >-
>           pg_isready -h 127.0.0.1 -p 5432
>           -U "$${POSTGRES_USER:-postgres}"
>           -d "$${POSTGRES_DB:-postgres}"
>       interval: 5s
>       timeout: 3s
>       retries: 5
>
> secrets:
>   app_db_password:
>     file: ./secrets/app_db_password.txt
>   db_admin_password:
>     file: ./secrets/db_admin_password.txt
>
> volumes:
>   report-data:
> ~~~

新建空卷时，先确认 `REPORT_IMAGE` 指向本次 push 后已核验的 registry digest，再执行 `docker compose up -d db` 单独启动数据库。`POSTGRES_DB: reports` 让官方镜像在初始化这个空数据目录时创建 `reports`；默认管理用户是具备高权限的 `postgres`，不要把 `POSTGRES_USER` 改成 `report_app`。数据库的 TCP healthcheck 变为 healthy 后，运行项目提供的受控 bootstrap/migration（引导和迁移）任务：任务通过获准的 secret access 读取数据库管理员密码和 `app_db_password`，创建使用应用密码的 `report_app`，只授予 `reports` 中应用需要的权限并完成 schema migration（结构迁移）。成功后再执行 `docker compose up -d api worker`。这段 Compose 没有定义具体迁移任务；它必须在 API 和 worker 之前成功完成，不能由 `depends_on` 的数据库健康检查代替。现有卷不会因环境变量更新而自动补建数据库或修改凭据，启动服务前应核对其实际状态。

healthcheck 用 `pg_isready -h 127.0.0.1 -p 5432` 明确探测正式 TCP 监听端口；不带 `-h` 时会走 Unix socket，而官方 Postgres 镜像初始化期间会启动只供本地脚本用的临时服务器，可能让 socket 检查在正式 TCP 服务前过早通过。健康检查中的 `-U`/`-d` 提供连接请求信息，不是身份验证，也不证明角色、密码或迁移正确。`depends_on: condition: service_healthy` 只等待这个 TCP 健康状态；若把 API/worker 和 db 一起启动，它不等待独立的引导任务，因此要先完成上述初始化，再启动应用服务。

Compose 自动创建项目的 default bridge network（默认桥接网络），服务可以通过 service name（服务名）互相发现。API 与 worker 都连到 `db:5432`，那是数据库容器端口；只有要从宿主机或外部进入的 API 映射了 host port（宿主机端口）8080。API 进程在容器内监听 `0.0.0.0:8080`，Compose 的 `127.0.0.1:8080:8080` 只把宿主机回环地址映射到这个容器端口。若省略宿主机 IP，默认会绑定所有宿主机接口，应视作对其他可路由主机开放。Docker Engine 28.0.0 起，localhost 发布在默认 bridge/NAT 路径的预期行为是只由 Docker 主机访问；更早版本有同一 L2 网络的其他主机可访问 localhost 发布端口的例外。特殊 network mode（网络模式）、direct routing（直接路由）和宿主机路由/防火墙仍可能改变边界，按实际 Engine 与网络设置核实。无论端口是否开放，服务名可达都不代表数据库身份通过，也不代替应用认证或租户授权。

容器通过 `db` 发现对端，不要保存容器 IP：Compose 重建服务时会分配新 IP，但服务名不变；已有连接会断开，客户端应重新解析并连接。`depends_on: condition: service_healthy` 只在 Compose 启动依赖方时等待数据库 TCP 健康检查，不会在之后数据库故障时接管恢复；`pg_isready` 说明 TCP 服务在接入，不证明应用凭据有效、迁移完成或业务查询正确。端口映射只建立转发关系，也不证明 API 进程健康。

Compose `secrets` 显式把相应凭据文件挂给获准服务；本例以 Linux 容器为前提。本地 `file:` secret 通过 bind mount 提供，`uid`、`gid`、`mode` 覆盖会被忽略，应按实际宿主文件权限确保容器的 `USER 10001` 能读取。这里 `db_admin_password` 供官方 Postgres 镜像初始化管理员；`app_db_password` 是独立的最小权限应用账号密钥，API/worker 代码必须自行读取 `DATABASE_PASSWORD_FILE`。官方镜像中的 `POSTGRES_PASSWORD_FILE` 只在空数据目录首次初始化时设置管理员密码；后来改宿主 secret 文件不会修改数据库里已存在的密码。轮换必须先在数据库中更新账号，再让应用切到匹配的 secret。Compose 本地 secret 方便开发，不等同于加密的生产 secret store；不要把 `secrets/` 加入版本控制。

PostgreSQL 官方镜像自 major version（主版本）18 起采用版本专属数据路径，PostgreSQL 18 的默认 `PGDATA` 是 `/var/lib/postgresql/18/docker`，volume 应挂在父目录 `/var/lib/postgresql`；官方示例中的下一个大版本会将路径中的 `18` 换成其主版本号。17 及更早镜像的数据路径是 `/var/lib/postgresql/data`，此时应挂载该实际数据目录，单纯改成父目录可能不能持久化旧数据。切换 PostgreSQL 主版本不能靠更改 image tag 自动迁移现有数据库：18 的目录布局变化也要求先检查/调整旧卷结构；主版本升级须按官方升级路径备份并用支持的升级流程转换。本文用 PostgreSQL 18 说明该目录约定。即便 `postgres:18` 是主版本 tag，它也会移动到新的 18.x 镜像；生产记录并固定实际摘要、及时更新补丁。

容器可写层随容器移除而丢失；named volume（命名数据卷）由 Docker 管理，容器替换后可重新挂载；anonymous volume（匿名数据卷）没有稳定项目名称，新容器通常不会自动挂载同一个卷。bind mount（绑定挂载）直接映射宿主路径，适合开发时共享源码，不适合作为生产数据库备份方案。卷只解决容器替换后的文件存留，不保证异机备份、时间点恢复、加密、访问控制或数据正确；仍须独立备份和恢复演练。普通 `docker compose down` 移除容器与网络但保留命名卷，`docker compose down -v` 会删除 Compose 文件声明的项目命名卷及附着的匿名卷，连同其中的数据。

### 从构建状态检查到运行状态观察

检查时分清镜像、容器与 Compose 项目：

| 命令 | 查看的对象 | 能回答的问题 | 不能单独证明 |
|---|---|---|---|
| `docker image ls` | 本机镜像和 tag | 镜像是否已载入、本地有哪些名字 | 容器运行中或 registry 有同一内容 |
| `docker image inspect report-api:c4f2a91` | 本机镜像配置 | 平台、启动命令、环境、image ID（配置对象标识）和已知 RepoDigests（仓库摘要引用） | 当前 registry 发布状态或来源可信 |
| `docker ps -a` | 本机容器 | 容器是否运行、退出或停止 | 应用业务健康 |
| `docker compose ps` / `docker compose ps -a` | Compose 服务容器 | 默认只列运行中服务；`-a` 也列已停止容器 | 未配置 healthcheck（健康检查）时的就绪，或用户结果 |
| `docker compose logs api worker` | 两服务的标准输出/错误 | 启动错误和应用日志 | 端到端追踪、租户授权和完整指标 |
| `docker compose exec api /bin/sh` | 正在运行的 API 容器 | 查看进程环境或执行诊断命令 | 容器必有 shell；distroless/精简镜像可能没有 |
| `docker image history report-api:c4f2a91` | 本地镜像层记录 | 哪些构建步骤留下层线索 | 完整文件审计或密钥从未进入层 |

`docker compose up -d` 和 `docker run -d` 的 detached mode（分离运行模式）只让命令在后台返回；它不是独立进程监督器，也不自动确保健康检查、重启策略和告警已配置。容器的 `running`、`healthy` 和应用业务正确是不同判断：只有定义了 healthcheck 才有 Docker 健康状态；存活探针也不能证明 report 42 的租户授权。预发布后再到生产逐步放量的门禁和用户结果见[如何晋级并回滚已验证的报表服务产物？](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)。运行时停止 API 与 worker、释放在途任务的职责见[报表 API 与异步 worker 应由什么运行时承接？](#34.%20%E6%8A%A5%E8%A1%A8%20API%20%E4%B8%8E%E5%BC%82%E6%AD%A5%20worker%20%E5%BA%94%E7%94%B1%E4%BB%80%E4%B9%88%E8%BF%90%E8%A1%8C%E6%97%B6%E6%89%BF%E6%8E%A5%EF%BC%9F)。

镜像与容器的日常操作可以按对象生命周期读：`docker pull redis:7` 把可变 tag 拉到本机；生产若要求固定版本，应使用 registry digest。`docker run --name cache -d redis:7` 从镜像创建并启动一个新容器；`docker ps -a` 也能看到已停止容器。`docker stop cache` 向容器主进程发送配置的停止信号，宽限时间后再强制终止；`docker start cache` 重新启动同一个容器及其写层，不会从新版镜像重建它。`docker rm cache` 移除已停止容器；`docker rm -f cache` 会对运行中容器的主进程发送 `SIGKILL` 并移除它，没有 `docker stop` 的优雅停止宽限期；在途任务可能被中断，容器写层也随之丢失。单独的 volume 是否还在，取决于卷类型和删除操作。`docker image rm redis:7` 移除该本地镜像引用，其他标签或正在使用它的容器可能仍使层保留。

手动推送时，`docker login registry.example.com` 登录仓库，`docker tag` 给本地内容添加仓库名和标签，`docker push` 才把镜像发布到远端。登录会存储凭据，推送会写入 registry。生产发布应由受控 CI 身份完成，记录 registry 返回的摘要并按摘要部署，不把可变 tag 当作验收结果。

> [!info]- 来源
> - 镜像、容器与 Dockerfile：[What is an image?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/)、[What is a container?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)、[Dockerfile reference](https://docs.docker.com/reference/dockerfile/) 与[多阶段构建](https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/)，checked 2026-11-12；CMD、ENTRYPOINT、exec/shell form、USER 与镜像/容器关系按 Docker 当前文档核实。
> - 上下文、cache、密钥和摘要：[build context patterns](https://docs.docker.com/build/concepts/context/#syntax)、[build best practices](https://docs.docker.com/build/building/best-practices/)、[cache optimization](https://docs.docker.com/build/cache/optimize/)、[Build secrets](https://docs.docker.com/build/building/secrets/)、[buildx build](https://docs.docker.com/reference/cli/docker/buildx/build/)、[Buildx exporter selection source](https://github.com/docker/buildx/blob/v0.39.0/build/opt.go#L494-L538)、[imagetools inspect](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/)、[Build attestations](https://docs.docker.com/build/metadata/attestations/)、[Docker Engine containerd image store](https://docs.docker.com/engine/storage/containerd)、[Docker Desktop containerd image store](https://docs.docker.com/desktop/features/containerd/) 与[image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/)，checked 2026-11-12；涵盖 `.dockerignore` 递归模式、cache mount、`--load` CLI shorthand、`--push`、metadata、registry 核验、index 附件、digest 与受 builder/store 影响的多平台载入边界。
> - Python 依赖校验：[pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/) 与 [pip install `--require-hashes`](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-require-hashes) 与 [pip build system](https://pip.pypa.io/en/stable/reference/build-system/)，checked 2026-11-12；哈希模式要求逐项锁定直接和传递依赖并为发行包提供哈希，源码包的隔离构建环境另有 build-time dependencies。
> - Compose 文件和服务：[Compose Specification](https://docs.docker.com/reference/compose-file/)、[Compose history](https://docs.docker.com/compose/intro/history/)、[services reference](https://docs.docker.com/reference/compose-file/services/)、[Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/)、[startup order](https://docs.docker.com/compose/how-tos/startup-order/) 和[variable interpolation](https://docs.docker.com/reference/compose-file/interpolation/)，checked 2026-11-12；旧顶层 `version` 字段已过时；当日 Docker Docs 支持的 Compose CLI 为 v2 与 v5，均采用 Compose Specification。`command`、`entrypoint`、`depends_on` 和健康检查取决于服务配置。
> - 网络、端口和卷：[Compose networking](https://docs.docker.com/compose/how-tos/networking/)、[port publishing](https://docs.docker.com/engine/network/port-publishing/)、[volumes](https://docs.docker.com/engine/storage/volumes/)、[bind mounts](https://docs.docker.com/engine/storage/bind-mounts/) 与 [`docker compose down`](https://docs.docker.com/reference/cli/docker/compose/down/)，checked 2026-11-12；localhost 端口边界按 Engine 版本、网络模式和路由说明。
> - 本地 secret 与 Postgres 初始化：[Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/)、[official Postgres image initialization scripts](https://github.com/docker-library/docs/blob/master/postgres/README.md#initialization-scripts)、[official image entrypoint](https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh)、[environment variables](https://hub.docker.com/_/postgres#environment-variables)、[PostgreSQL 18 `pg_isready`](https://www.postgresql.org/docs/18/app-pg-isready.html) 与[PGDATA](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)，checked 2026-11-12；Compose `file:` secrets 由具体实现挂载；`pg_isready` 检查服务器是否接受连接，不验证角色认证或迁移；Postgres 初始化环境变量不会修改非空数据目录中的已有账号。
> - 版本选择：[Python 3.15.2](https://www.python.org/downloads/release/python-3152/)、[official Python image `slim` layer](https://hub.docker.com/layers/library/python/slim/)；[PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/) 与 [PostgreSQL 19 RC 1 schedule](https://www.postgresql.org/about/news/postgresql-19-rc-1-released-3409/)，checked 2026-11-12。Python 3.15.2 已发布，Docker Hub 的 `python:3.15-slim` 对应其官方镜像；PostgreSQL 19 的 general availability（正式可用，GA）当时仍计划在 2026-11-19，本文用 PostgreSQL 18 说明已发布版本的目录边界。
> - 操作与观察：[docker run](https://docs.docker.com/reference/cli/docker/container/run/)、[docker stop](https://docs.docker.com/reference/cli/docker/container/stop/)、[`docker rm --force`](https://docs.docker.com/reference/cli/docker/container/rm/#force)、[docker image rm](https://docs.docker.com/reference/cli/docker/image/rm/)、[docker image history](https://docs.docker.com/reference/cli/docker/image/history/)、[docker compose ps](https://docs.docker.com/reference/cli/docker/compose/ps/)、[docker compose logs](https://docs.docker.com/reference/cli/docker/compose/logs/)、[docker compose exec](https://docs.docker.com/reference/cli/docker/compose/exec/)、[docker login](https://docs.docker.com/reference/cli/docker/login/)、[docker tag](https://docs.docker.com/reference/cli/docker/image/tag/) 和[docker push](https://docs.docker.com/reference/cli/docker/image/push/)，checked 2026-11-12；强制移除运行中容器会发送 `SIGKILL`，不等同于先执行 `docker stop` 的宽限终止。
## 34. 报表 API 与异步 worker 应由什么运行时承接？

上一章从已检查的源码提交 `c4f2a91` 构建镜像，并将经过远端清单核验的 registry（镜像仓库）摘要交给后续环境。本章直接承接该摘要作为 application programming interface（应用程序接口，API）与 worker（工作进程）的运行产物；二者可以用不同启动命令运行，不重新构建。outbox relay（事务发件箱转发进程）是另一独立进程；只有实际镜像包含它的执行入口时才可复用该摘要，否则须交接 relay 自己经过核验的镜像摘要。本章说明这些运行角色怎样分别配置网络、身份、容量与停止行为。API 经 Hypertext Transfer Protocol Secure（超文本传输安全协议，HTTPS）入口提供服务；生产预发布、授权冒烟和逐步切流由[如何晋级并回滚已验证的报表服务产物？](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)继续说明。

合成例中，tenant-a 读取 report 42 应得到 200 和预期内容，tenant-b 猜中同一报表 ID 应得到 404。acct-17 的调用者先通过当前身份认证，并被确认属于该账户且有 `report:export` 权限；`report:read` 只允许读取，不能替代导出授权。通过授权后，API 使用 idempotency key（幂等键）`report-demo-208`，在同一个数据库事务中写入 job（任务）`job-demo-731`、transactional outbox（事务发件箱，outbox）意图，并预留一个等待槽。新任务只有在事务提交后才返回 `202 Accepted`（已受理）、稳定 job ID 和 Uniform Resource Locator（统一资源定位符，URL）形式的状态查询地址；202 只表示任务意图已受理，不表示报表已经完成或最终必然成功。每次重复请求也先重新授权，同一账户、主体和规范化请求的幂等键重放会返回原 job，不再预留新槽，同键对应不同报表参数则冲突。之后查询状态或下载结果时仍按当前调用者重新授权；排队期间 worker 也要在读取报表前复核发起人当前的导出权限。

等待槽是数据库维护的排队准入额度：每个未领取的排队轮次占一个，接管重排时重新预留，领取时释放；它不是 broker（消息代理）的 prefetch（预取）或锁。relay（转发进程）读取待发意图并发布到 queue（队列）；worker（工作进程）领取任务、计算结果、写入私有对象，成功时在持久提交对象引用和任务状态后才发送 consumer acknowledgement（消费者确认，ACK）。只读请求的授权结果与导出任务的成功或失败是两种不同的用户结果。本文的账号、ID 和数据均为教学用合成值。

job、outbox 和等待槽在同一数据库事务提交，但该事务不包含 broker 写入。relay 只有在所选 broker 的发布确认、路由和持久性条件都满足后，才把对应 outbox 意图记为 `published`；这个状态只表示发送端完成发布步骤，不表示 worker 已处理或 job 已成功。broker 可在 relay 更新 outbox 行之前就投递消息，worker 也可能先完成领取，所以 `published` 不是 worker 可见消息的前置状态。若 broker 已接收消息而 relay 在更新数据库前崩溃，重试可能再次发布。队列只携带稳定 job ID，worker 仍要从数据库条件领取当前 attempt（尝试）；重复消息不能仅凭消息本身启动并行 attempt。发布者确认、消费者 ACK 和业务 job 终态是三个不同边界；本例的状态细节见[怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)与[报表任务的发布确认、消费者确认与业务完成各证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

![浏览器经可选 content delivery network（内容分发网络，CDN）访问 API；下载时 API 授权并签发短期 URL，浏览器须能到达 Amazon Simple Storage Service（Amazon S3）HTTPS 端点且对象策略允许该请求。](../../engineering-foundations/infrastructure/resources/runtime-network-and-identities.svg)

图中的 API 入口与异步任务由不同进程承接。CDN 可选：不使用时浏览器直接到 load balancer（负载均衡器）入口。应用的公共入口只提供 HTTPS（超文本传输安全协议）；下载是另一条直达对象端点的 HTTPS 路径：只有任务结果和对象引用已持久、API 按当前用户授权后，API 才签发短期 URL，浏览器随后直接向 Amazon S3 请求对象，不经过 API 数据路径。私有 bucket（存储桶）仍须允许浏览器所在网络到达 S3 端点，并在 bucket 和访问控制策略中允许该签名请求；若策略只允许来自指定 Virtual Private Cloud（虚拟私有云，VPC）endpoint（端点）的请求，未经过该端点的浏览器即使拿到正确签名也会被拒绝。对象访问 URL 是持有者即可使用的 bearer token（持有者令牌），不能当成可公开缓存的普通地址。

### 网络路径和身份策略分开

网络路由、防火墙或安全组决定“谁能连到哪个地址”；工作负载身份和资源策略决定“该服务主体能对哪个资源做什么”；API 的业务授权再决定“当前用户能否读取 tenant-a 的 report 42、是否能导出 acct-17 的数据”。三者不能互相替代。HTTPS 加密浏览器到应用入口之间的传输，却不会替代 API 对当前主体的授权；Hypertext Transfer Protocol（超文本传输协议，HTTP）请求如何从浏览器到达响应见[浏览器请求如何到达 HTTP 响应？](#2.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F)。常见拓扑只公开应用的 HTTPS 入口；API 只接受负载均衡器送来的应用请求；数据库只允许 API、worker、outbox relay 和数据库租约恢复器各自的私有网络身份进入，例如为恢复器单独配置安全组或等效网络规则。恢复器再使用独立的数据库主体（例如 `runtime_recovery`），不借用 worker 或 relay 的凭据。浏览器直达 S3 的签名下载是独立的 HTTPS 端点，端点可达与对象授权都必须成立。各服务的数据库网络白名单仍要配合最小 SQL 权限：relay 只操作 outbox 发布意图；恢复器只读取扫描和争用所需的 job 标识、状态、attempt、lease 截止时间与取消标志，并以条件事务接管匹配 job、原子预留等待槽、写入 recovery outbox 或持久化终态。该主体不能读取报表内容，也不获准发布 broker 消息或代替 API 做用户授权。

| 请求或进程 | 网络上需要到达 | 身份与数据权限边界 |
|---|---|---|
| 浏览器只读 API 请求 | 公共入口 → 可选 CDN → 负载均衡器 → 私有 API | API 从真实会话或令牌取得当前主体，再逐请求检查租户与报表权限；客户端自填租户头不能代替身份 |
| API | 数据库；签名 URL 可在本地基于凭据生成，不需代理对象文件 | 按租户/账户范围读取报表、成员关系、授权和 job 状态；写 job/outbox/等待槽；签名者只获准读取对应结果对象 |
| outbox relay | 数据库 + broker | 只读/认领 pending outbox 并更新同一发布意图；只向获准队列发布，不能用它承载用户授权 |
| worker | 数据库 + broker + 私有对象存储 | 按 job 的租户/账户范围读取报表输入和当前授权；条件领取并更新该 job/attempt；对象写入限制到报表前缀；先持久业务结果，再按所选 broker 契约 ACK |
| 数据库租约恢复器 | 独立私有网络身份直连数据库；重排意图由 outbox relay 另行发布 | 独立数据库主体只读扫描与竞争所需的 job 标识、状态、attempt、lease 截止时间和取消标志；条件更新接管或终态，重排时原子预留等待槽并插入 pending outbox；不读报表数据、无 broker 发布权，也不替用户授权 |
| 浏览器下载 | 持有 URL 后直达浏览器可达的对象 HTTPS 端点；本例不经 API | URL 只授予被签名的对象操作且有效时间受限；bucket 与对象资源策略仍须允许这条来源路径；浏览器不取得 worker 的云角色 |

![API 在受理事务提交后返回 202；图中只画 worker 成功分支：取得执行槽并条件领取，写入 attempt 独立对象键和数据库终态后向 broker ACK；其他 ACK 分支见正文。](../../engineering-foundations/infrastructure/resources/runtime-outbox-worker-path.svg)

worker 的数据库账号或数据库角色要有与任务相符的限定读取权：按 job 的租户/账户读取报表参数与数据，并读取该账户当前成员关系及 `report:export` 授权状态；状态写入仍限于被条件领取的 job/attempt。API 同样需要按范围读取报表与授权数据，并读取可查询的 job 状态；它只写受理事务所需的 job、outbox 和等待槽。若把这些读取放到受限查询服务，API 与 worker 对该服务的身份、数据范围和失败语义也要单独定义。队列消息只携带稳定 job ID，worker 在读输入前复核发起主体当前仍有导出权限；若已撤销，就持久写入 `failed` 终态及有界错误码 `authorization_revoked`，不读取报表。消息 ID、worker task role 或“已经提交过请求”都不能代替这项用户授权。

worker 的 Amazon Web Services（AWS）task role（任务角色）只需写指定报表对象前缀；身份与访问管理（Identity and Access Management，IAM）策略还应限定目标 bucket、对象前缀和可执行动作。签发下载 URL 的 API task role 还需对目标对象有 `GetObject` 权限。S3 按签发 URL 的主体权限判断请求；该 URL 可在有效期内重复使用，实际有效期不超过所选临时凭据的到期时间，相关凭据被撤销、删除或停用也会使其失效。应用撤销用户业务权限不会自动撤销已经签发的 URL。浏览器端还要能到达被签名的对象 HTTPS endpoint（端点），策略也要允许该请求上下文；“对象私有”表示未授权请求不能读取，不表示浏览器无法连接服务。仅允许某个 VPC endpoint 的 bucket policy 会拒绝未经过该 endpoint 的浏览器请求。若浏览器网络不能直达 S3，可经应用代理或配置私有源站的 CDN 提供下载；CloudFront 等 CDN 还需单独设置签名访问、私有源站和缓存策略，确保用户不能绕过 CDN 直接访问源对象。不能照搬公共静态文件缓存规则，签名 URL 与 CDN URL 的签名方式也不是一回事。

#### `job-demo-731` 的领取、恢复和 ACK

job 处于 `queued` 时占一个数据库等待槽。worker 先取得本进程一个真实可用的执行槽，再用条件事务尝试领取；领取成功后把 job 变成 `running`、写入 attempt 代次与 lease（租约）截止时间，并释放这轮等待槽。物理执行槽要保持占用，直到该 attempt 实际停止并释放进程资源；数据库租约到期或 job 状态改写都不会让仍在运行的进程自动空出 CPU、内存或连接。没有执行槽时不能先领取再把工作塞进无界的进程内队列，也不能 ACK 掉唯一的恢复信号；应暂停消费或按 broker 契约延后处理，并限制 prefetch 和本地缓冲。

假设 worker-A 已领取 attempt 1 后失联且没有 ACK。broker 重投的消息仍只是 job ID；消费者先读权威 job 行，看到 `running/attempt 1` 就不能单靠重复消息再启动计算。独立的数据库恢复器扫描已过 lease 截止的 running job。到期只让恢复器有资格争取接管，不会单独撤销 worker-A 的提交权：A 的完成事务只在状态、当前 attempt 匹配且 `cancel_requested=false` 时才可成功；恢复器也用状态、attempt 和取消标志做条件竞争，先提交者决定状态。若 A 先提交成功，恢复器重读后看到终态，不再重排。若恢复器先提交且发现 `cancel_requested=true`，就直接写入 `cancelled`，不争用新等待槽；若仍可重试，它把匹配的 attempt 改回 `queued`、重新预留等待槽并写入新的 outbox 意图。只有这次接管提交成功后，job 状态/attempt 谓词才会 fence（隔离）旧 attempt；A 随后完成时条件更新影响零行。若重排时没有等待槽可预留，则持久写入 `capacity_exhausted` 终态，不无限重发。

新的 worker 仍须先有自己的物理执行槽，才可条件领取 attempt 2。每个 attempt 写独立对象键，例如 `private-reports/acct-17/job-demo-731/attempt-2.csv`；attempt 1 即使在接管提交后还活着，也不能覆盖 attempt 2 的对象。worker 先将对象写入私有存储，再以“job 仍为 running、attempt 仍匹配且未请求取消”为条件，在数据库提交对象引用和成功终态，随后才 ACK。若上传成功但条件数据库提交失败，对象没有权威引用，是可清理的孤儿；只有旧 attempt 已被接管或 job 已终结、数据库确认无引用、上传时限上界和额外安全宽限都已过，才回收对象，避免删除仍可能被合法提交引用的结果。

ACK 的依据取决于数据库已持久化的结果：成功或业务失败/取消终态提交后可 ACK；准备重试时，要先持久提交新的 `queued` 状态、等待槽和 outbox 意图，再 ACK 旧投递。若 DB 已提交终态而 ACK 丢失，重投只需重读 job 并 ACK，不重做计算。若看到 job 仍 `running`，只有确认有独立且持久的租约恢复器负责它时才可 ACK 重复投递；否则应保留或延后这条恢复信号。取消一个排队 job 也要在条件终态事务中只释放一次等待槽。

预取但尚未开始的投递也必须有归还路径。broker 对暂停、取消和关闭的具体保证不同；例如 RabbitMQ 4.4 中 `basic.cancel` 只阻止后续分发，不会丢弃或重排已经发出但未确认的投递。本例通过关闭 channel（通道），自动将其中仍未确认的投递归还队列；保留通道时，也可用 `basic.reject` 或 `basic.nack` 并设 `requeue=true` 显式重排相应投递。这条 RabbitMQ 行为不能外推为所有 broker 的通用规则；上线前要按实际客户端和 broker 的取消、关闭、重投语义设置预取与停机流程。

本地 Compose 能验证服务发现和容器间网络，但不能证明运行时身份、生产入口或租户授权正确。相同镜像摘要进入预发布后，仍要使用正常认证路径，经已配置入口以两个独立身份复放 tenant-a → 200 / 预期内容与 tenant-b → 404，并从追踪确认两次请求都命中被验收的本轮摘要；发起导出还需单独验证 acct-17 的账户成员关系和 `report:export` 授权，持有 `report:read` 不足以通过该门禁。入口和业务结果的发布门禁见[生产入口的就绪、授权冒烟与渐进放量](#%E5%B0%86%E7%8E%AF%E5%A2%83%E9%97%A8%E7%A6%81%E3%80%81%E5%90%AF%E5%8A%A8%E6%A3%80%E6%9F%A5%E5%92%8C%E6%B8%90%E8%BF%9B%E6%94%BE%E9%87%8F%E6%8E%A5%E8%B5%B7%E6%9D%A5)。

### 托管平台管理什么，应用仍拥有哪部分

| 层 | 平台通常负责 | 应用团队仍负责 |
|---|---|---|
| 计算 | 按服务方案提供主机维护、调度和运行环境 | 镜像/包、启动退出、资源上限、扩缩容策略、健康规则 |
| 数据库 | 所选配置包含的基础设施、补丁、备份或故障切换 | schema 和迁移、查询/连接行为、权限授予、保留期、恢复演练 |
| 对象存储 | 服务可用性及文档承诺的持久性机制 | 私有命名、保留/生命周期、上传上限、谁能拿 signed URL 及其过期/撤权策略 |
| 队列 | 在服务合同和配置限制内存储和投递消息 | 幂等处理、重试退避、毒消息处理、队列年龄和dead-letter queue（死信队列，DLQ）恢复 |

“托管”减少平台运维，但不会替工作负载选择安全配置。托管数据库不会修复缺索引查询或连接风暴；托管队列也不会使非幂等 worker 在重试时安全。


### 按任务时长、并发和停止行为选择运行时

运行时选择不是按“云上”或“无服务器”作标签，而要看工作何时开始、最长会运行多久、并发怎样到达、能否安全重试、需要哪些连接和状态，以及平台停止进程时能否完成当前交接。

| 运行形态 | 适合的约束 | 必须核对的边界 |
|---|---|---|
| function service（函数托管服务） | 由事件触发、每次工作有明确上限，且供应商重试、并发和执行上下文能匹配业务 | 单次上限、冷启动、并发和配额、网络与连接池、触发及重试语义；需要持久进度时要用平台支持的状态编排，而不把内存当跨调用状态 |
| managed container service（托管容器服务） | HTTP 服务或队列消费者需要长期进程、明确的并发上限、连接生命周期和停止钩子 | 健康检查如何影响流量、扩容是否足以及时、停止宽限期是否覆盖排空、多个副本如何共享外部数据库/队列而不共享进程内状态 |
| virtual machine（虚拟机，VM） | 依赖主机级配置、守护进程、内核能力或遗留运行环境 | 团队需要安排主机补丁、容量与故障替换；若使用的是托管 VM 产品，应按其服务合同重新划定平台和应用责任 |

按峰值与稳态负载、最低常驻容量、启动延迟容忍度、长连接、并行度、数据库连接预算、单次执行限制和团队运维能力比较。serverless（无服务器计算）仍有状态、网络、配额和费用边界；“自动扩展”不会自动给数据库增加连接容量，也不保证尖峰请求立即获得新实例。队列到达率、处理时长和下游连接预算怎样共同限制准入与并行度，见[如何估算并限制异步工作管线？](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F)。

目前 AWS Lambda 文档将默认函数调用、Lambda Managed Instances 和 durable functions（持久函数）区分：默认单次调用最长 15 分钟，Managed Instances 的异步或事件源映射调用可到 90 分钟，持久函数可用检查点跨多次调用并让异步执行最长到一年。它们的状态、并发和恢复语义不同，不能用“函数最长多久”概括所有产品模式。默认执行环境可能复用全局对象和 `/tmp`，可做可丢弃缓存或连接复用；环境会被回收，不能把它当跨运行持久数据，未完成后台回调也不能依赖将来继续执行。

在报表例中，HTTP API 要持续接收读请求；worker 则常驻等待队列，再访问数据库和对象存储，且在停止时要完成当前任务或安全交还 delivery（消息投递）。因此可将 API、outbox relay 与 worker 作为分开的可扩缩容服务运行；API 与 worker 可沿用 Docker 交付的同一镜像摘要并设置不同启动命令、网络和身份。relay 是否能复用该摘要取决于镜像是否包含其执行入口；若是独立构建，就要交接 relay 自己经过核验的摘要。API 与 worker 要单独配置并发和容量；relay 也独立控制，避免把它错误地包进 API 健康状态或 worker 的消息暂停开关。只有当导出任务可被拆成明确有界的事件步骤，且平台触发、重试、最大时长和连接约束都适合时，才把计算阶段拆成函数。已归档的[托管函数取舍笔记](../../archive/front-end/Deprecated_Interview_Notes/hosted-functions-tradeoffs.md)保留了旧代 Cloud Run 的历史比较；当前产品限制应以相应平台的现行文档为准。

容量规划要同时核算逻辑等待槽、worker 物理执行槽和每个进程的连接池。一个教学部署若有 4 个 worker 副本、每副本 2 个进程、每进程 8 个 attempt 执行槽，则有 `4 × 2 × 8 = 64` 个物理执行槽；worker 不能靠增加 prefetch 把这 64 个槽伪装成更多并行能力。若 API 和 worker 也各按 4 副本 × 2 进程运行、每进程连接池上限为 `8 + 2`，两组分别最多占 80 个数据库连接。容量例把其他共用服务预留 40 个，配置上限为 200；在假设预算 240 下只余 40。relay、数据库恢复器、迁移工具若未纳入这 40，就必须另列预算。扩 worker 副本会同时扩执行槽和连接池上限，不能只看队列排空时间。

进程收到停止信号后，各服务应立即在自己的控制面开始关闭，不等待入口传播或其他服务先结束：

- **API：**进程收到通知即关闭本地业务门闩，拒绝开始新业务操作，并开始排空已在途请求；同时让 readiness probe（就绪探针）返回未就绪，让平台异步更新常规路由目标。路由摘除传播期间仍可能有请求抵达，所以本地门闩不能依赖探针传播；已开始的请求须在宽限期内完成或按应用契约安全中止。然后关闭数据库连接池、线程、临时文件与 telemetry exporter（遥测导出器）。
- **worker：**独立停止领取新的 delivery（消息投递），并对运行中 attempt 与已预取但未启动的投递分别处理。运行中的 attempt 能在截止前完成时，先持久提交业务结果再 ACK；否则不 ACK，让 broker 重新投递，数据库恢复器按租约规则接管。尚未启动的投递要按 broker 的关闭/归还契约重排。readiness probe 不会替 worker 暂停队列。
- **outbox relay：**停止认领新的 pending 意图；宽限期内等待已开始的发布达到可判定结果。只有选定 broker 的确认、路由和持久性合同都满足，且数据库 `published` 更新成功，才标记该意图完成。缺少确认或数据库更新未提交时不伪记成功；若实现了认领租约则释放认领或等待租约过期，由新 relay 重试。重复发布同一稳定 job ID 是允许的，worker 的持久条件领取负责安全去重。监控最老 pending outbox 年龄，避免 relay 停摆时队列深度仍看起来正常。

![API 收到通知即关本地门闩而不等路由传播；worker 独立停收，归还未启动预取，运行中任务完成后先持久提交再 ACK，否则不 ACK，由 broker 重投与租约恢复器接手。](../../engineering-foundations/infrastructure/resources/runtime-api-and-worker-shutdown.svg)

Kubernetes 与 ECS 的平台摘流顺序不能合并成一条通用时间线。Kubernetes v1.37 的 Pod 删除会让控制面评估 EndpointSlice（端点切片）的同时，由 kubelet 在节点上开始容器优雅停止；终止中的 endpoint（端点）可暂时留在 EndpointSlice 中，但标为 `ready: false`，不是物理删除。默认 Service 代理通常忽略 terminating（正在终止）endpoint，不过若所有可用端点都在终止，可能向同时 `serving` 和 `terminating` 的端点路由；配置 `publishNotReadyAddresses` 的 Service 则会把 `ready` 设为 true。readiness 失败可从普通 Service 目标中摘除 Pod，liveness probe（存活探针）或 startup probe（启动探针）失败可触发重启；Deployment 的 `restartPolicy` 只允许 `Always`。探针的状态传播与 Pod 本地终止是不同动作，不能当作唯一停止流程。

Amazon Elastic Container Service（Amazon ECS）只有在 service task 配置了负载均衡目标组时，任务才会先在 `DEACTIVATING` 注销目标，然后进入 `STOPPING` 并通知 Linux 容器停止。容器定义字段拼写是 `stopTimeout`；超时后 ECS 发 `SIGKILL`，正常停止信号默认是 `SIGTERM`。Fargate 未设置时默认 30 秒、最大 120 秒；ECS on EC2 未设置时使用 agent 的 `ECS_CONTAINER_STOP_TIMEOUT`，都未配置则默认 30 秒。宽限期须覆盖停止拉取、排空、提交或归还、清理；不能把 ECS 的先注销顺序套到 Kubernetes，也不能假设只把 readiness 设 false 就已完成平台摘流。可复用的 Node.js 服务状态与停机顺序见[Node.js 服务如何排空并关闭？](#24.%20Node.js%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E6%8E%92%E7%A9%BA%E5%B9%B6%E5%85%B3%E9%97%AD%EF%BC%9F)，消息结果与 ACK 边界见[报表任务的发布确认、消费者确认与业务完成各证明什么？](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

### worker 凭据怎样注入、轮换并撤销？

先区分三类授权。本节从报表服务的 AWS 工作负载身份，切换到另一个独立 sender/receiver 工作负载，用一个合成 Webhook（回调通知）协议说明共享密钥轮换；它不是报表导出 worker 的职责或凭据。300 秒的签名新鲜度窗口与 `createdAt + 30 天` 投递截止时间都是该合成协议的教学常数，不是 Webhook 通用标准，也不是所有提供方的默认值。协议载荷、身份映射、重试和时间规则见[合成 Webhook 接收方如何验证并可靠受理？](#17.%20Webhook%EF%BC%88%E5%9B%9E%E8%B0%83%E9%80%9A%E7%9F%A5%EF%BC%89%E6%8E%A5%E6%94%B6%E6%96%B9%E5%A6%82%E4%BD%95%E9%AA%8C%E8%AF%81%E5%B9%B6%E5%8F%AF%E9%9D%A0%E5%8F%97%E7%90%86%EF%BC%9F)。

| 凭据 | 谁获授权、用来做什么 | 谁有权读取或验证 | 撤销边界 |
|---|---|---|---|
| task role（任务角色）临时凭据 | 一个运行任务调用 AWS API，例如 worker 向报表前缀写对象 | 该 ECS task 中的应用容器通过容器凭据提供程序取得 | IAM 角色、目标资源策略或 task 凭据失效；不能替用户授予报表访问权 |
| Webhook HMAC（基于哈希的消息认证码）密钥 | 独立的 Webhook sender（发送端）对消息签名、receiver（接收端）验证对应来源 | 同一端点/来源的两端必须持有同一个共享密钥。ECS 启动注入时由 task execution role（任务执行角色）授权 ECS agent 读取指定 Secret ARN；task role（任务角色）只控制应用代码的运行期 AWS API 权限，不是此注入授权的来源 | 接收端停用 keyId、部署移除旧值，并停止旧 sender/receiver 进程 |
| 用户 OAuth 2.0 grant（用户授权） | 某用户允许应用访问特定下游资源和权限范围 | 只在绑定的用户/租户/受众/scope 上下文中使用 | 用户撤权、授权到期或 provider 撤销语义；不应影响其他用户的 grant |

以 ECS 为一个具体例子，容器镜像只包含代码，task definition（任务定义）引用 Secrets Manager 中的 Secret Amazon Resource Name（Amazon 资源名称，ARN），不写密钥值。task execution role（任务执行角色）授予 ECS agent 启动任务时读取对应 Secret ARN 的 `secretsmanager:GetSecretValue` 权限；若使用客户自管 AWS Key Management Service（AWS KMS，密钥管理服务）key 解密，还需要该 key 上的 `kms:Decrypt`。这项权限供 ECS agent 在启动阶段取值并注入，不直接提供给应用代码；应用自己的 task role（任务角色）只控制运行期 AWS API 动作。sender 和 receiver 可各自引用一份只含本工作负载配置的 Secret，并使用分开的 execution role 与 task role：execution role 限制 agent 能取哪些 ARN，task role 限制应用运行期能做什么。两端 Secret 中代表同一来源的 HMAC key 值仍须相同；分角色不能把共享密钥变成单向能力。

本例明确选用相互独立的 Linux Fargate task。Fargate 在 task 间提供隔离边界，但同一个 task 内多个容器共享该 task 的权限，不应把互不信任的应用放进同一 task。ECS on EC2 中同一宿主机上的并置 task 与宿主机访问边界不同；ECS 官方明确说明容器本身不是安全边界，严格隔离应按当前 launch type 配置和平台文档复核。task role 提供短期工作负载凭据；ECS 将凭据 URI 交给容器，支持的 AWS software development kit（软件开发工具包，SDK）标准 credential provider 可自动取得并更新凭据。应用不应把临时凭据复制成长期静态密钥。

HMAC 是共享密钥消息认证码：同一 endpoint/source 的 sender 和 receiver 必须用相同 keyId 对应的同一个密钥值。持有该密钥的任一方都能计算有效签名，因此 sender/receiver 分成独立进程、execution role 与 task role 有助于限制其他 Secret 和业务动作的暴露面，却不能在密码学上保证 receiver 只能验证、不能签名。若业务要求签名权与验证权真正分离，应选用非对称签名方案。本例将 sender 的 `keyId` 与 key、receiver 的整张验证映射分别存成完整 JSON Secret；两端配置中同一 `keyId` 对应的密钥值必须一致，Secret JSON 整体内容并不相同。

接收服务把整份允许的 keyId→密钥映射 Secret 注入单一环境变量 `WEBHOOK_VERIFY_KEYS_JSON`；sender 则把整份 `{"keyId":"…","key":"…"}` 配置 Secret 注入单一环境变量 `WEBHOOK_SIGNING_CONFIG_JSON`，由应用从同一份 JSON 解析 ID 与密钥。这样不会在分别注入两个值期间遇到 `AWSCURRENT` 移动，形成新 key 配旧 keyId。task execution role 只读取对应工作负载的 Secret ARN；应用 task role 不承担读取这次启动注入 Secret 的工作。ECS `valueFrom` 也允许引用完整 secret、JSON key、version-stage 或 VersionId；没有指定 stage/VersionId 时默认读取 `AWSCURRENT`，两种版本选择不能同时指定。本例跟随 `AWSCURRENT`，但每个进程只取一个完整 JSON Secret 值。对 Linux Fargate，注入特定 JSON key 或版本要求平台版本 1.4.0 或更高；注入完整 secret 至少需要 1.3.0。Secret 在 task 启动时注入，移动 staging label 不会更新在运行任务中的环境变量；必须启动新 task 或强制服务滚动部署。若固定 VersionId，则先发布引用新版本的 task definition revision，再替换 task。容器内应用、日志和调试工具都可能读环境变量，因此不要 dump 环境、在异常里回显配置，也不要把密钥放进镜像层、版本库、命令参数、前端 bundle、请求日志或模型 prompt/checkpoint。

正常轮换按“接收端先兼容、发送端再切换、接收端最后移除旧键”进行。本合成 Webhook outbox 保存未签名正文，sender 每次新投递才签名：

1. 生成新 keyId 和新密钥；将 receiver 的完整配置 JSON 更新为含旧、新两项的 `WEBHOOK_VERIFY_KEYS_JSON`，移动该 Secret 的 `AWSCURRENT` 并强制部署 receiver task。若 task definition 固定 VersionId，就发布引用新版本的 revision；确认旧 receiver task 已退出。
2. 将 sender 的完整 `WEBHOOK_SIGNING_CONFIG_JSON` Secret 更新为同一条新 keyId/key 配置，移动 `AWSCURRENT` 并替换 sender task；应用从单个注入值解析两项。新尝试使用新密钥重签相同 eventId 与原始正文。等待旧 sender task 全部退出，并从持久投递记录取得所有旧签名时间戳的最大值 `Tmax`。按本协议的本地验签时钟规则，只有每个仍可能接收旧请求的 receiver 自己的时钟都已严格晚于 `Tmax + 300 秒`、且任何已通过新鲜度检查的在途验证都已结束，旧键才不会再被接受；此判定使用 receiver 自己的时钟，不要再把同一时钟偏差加一次。若由轮换协调器的可信时钟统一判定，则需在 `Tmax + 300 秒` 上额外覆盖一次已测得的最大 receiver 时钟落后量，并等待在途验证结束。不能只从部署新 sender 的时刻等 300 秒，因为旧实例可能之后仍发送过旧签名。
3. 将接收端映射改为仅新键并强制替换 receiver task；若固定 VersionId，也更新 task definition revision。确认旧 receiver 进程全部退出后，旧密钥才不再驻留于进程。过期 Secrets Manager 版本再按保留策略清理。
4. 若实现预先排队的是已签名请求，而不是未签名正文，就须在旧签名失效前重新签名，或等这些旧签名全部失效后再移除旧键。

移动 `AWSCURRENT` 本身不会改变 sender/receiver 已运行环境；每个引用该 Secret 的 service 都要部署新 task。若双方固定 VersionId，各自发布的新 revision 要指向正确版本。

若 key 已泄漏，不能保留新旧双接受窗口。先预先生成新键，暂停事件交付并阻断旧 receiver 入口或停掉旧 receiver task；部署只含新键的 receiver，接着原子更新 sender 的完整 `WEBHOOK_SIGNING_CONFIG_JSON`（新 keyId 和 key 同在一个 Secret 值中）并替换旧 task，确认旧进程退出后恢复交付。若 task definition 固定 VersionId，两端都更新 revision。还没有可用新键时就撤销旧键并保持暂停，不能为可用性继续接受泄漏密钥。发送端按被撤销的 keyId 找到未确认事件，只能在原 `createdAt + 30 天` 前，以原 eventId、原正文和新 attemptId 重签；换键不重置绝对期限。若旧请求已受理但响应丢失，持久 inbox 会识别重复；已确认 2xx 的事件不重放。删除 Secret 值不会清除进程中已经注入的副本，必须替换 task。其他可直接访问资源的凭据还需在签发方或目标资源撤销；OAuth access token 怎样停止使用则按 provider 契约处理。

用户 OAuth grant 代表的是另一个授权主体：按用户、租户、目标 audience（受众）、scope（权限范围）和有效期隔离，并在用户撤权后阻止新调用。它不是 ECS task role，也不是服务级 Webhook HMAC 密钥。Refresh Token（刷新令牌）不得塞进所有 worker 的共享环境、日志、模型上下文或恢复快照；运行时只可为已经绑定的用户 grant 取用。Web session 与 OAuth grant 的身份边界见[Cookie 会话与 OIDC 令牌怎样建立身份？](#4.%20Cookie%20%E4%BC%9A%E8%AF%9D%E4%B8%8E%20OIDC%20%E4%BB%A4%E7%89%8C%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E8%BA%AB%E4%BB%BD%EF%BC%9F)。

把 Secret 读取与业务 API 调用分开审计。Secrets Manager 的 `GetSecretValue` 会生成 CloudTrail 事件；该事件可用于调查哪个授权主体请求了哪个 Secret ARN，但不能假设它带有 taskArn 或 API 响应中的 VersionId。GetSecretValue API 响应本身含 VersionId，敏感的 SecretString/SecretBinary 值不会进入 CloudTrail。把读取事件与 task definition revision、task 启动和部署控制面记录关联：固定 VersionId 时 revision 记录期望版本；跟随 `AWSCURRENT` 时另保存 staging label 移动和滚动部署的时间线。若必须证明每个运行 task 实际解析的版本，应固定 VersionId，或使用平台确实提供的非敏感解析版本证据；仅凭 revision 与标签时间线不能断言竞态期间每个 task 实际读到哪一版。应用以 task role 调用 AWS API 的 CloudTrail session 可带 taskArn；这条业务调用审计不能替代 Secret 注入审计。所有自建日志也不能记录密钥、完整签名头或正文。审计轨迹说明谁在何时请求或启用了凭据，但不能单独证明 IAM policy 与对象前缀已最小化。


### 用失败信号和成本边界检查组件

| 边界 | 计划中的失败 | 观察信号 | 成本/限制 |
|---|---|---|---|
| 负载均衡 / 网络 | 错路由、无健康目标、出站流量受阻、证书过期 | 请求错误、连接失败、目标健康数 | 请求与字节、网络地址转换、数据传输 |
| 计算服务 | 启动失败、崩溃循环、CPU/内存饱和、扩容慢 | 就绪实例、CPU/内存、重启与请求排队 | 最低副本和运行时间；扩容不是瞬时容量 |
| 数据库 | 连接耗尽、锁等待、I/O/存储或故障切换 | 连接池等待、连接数、查询时延、锁 | 计算、存储、I/O、备份保留 |
| 对象存储 | 权限错误、路由故障、对象意外公开、无限保留 | API 错误、对象增长、下载量 | 存储、请求、生命周期、复制、出站流量 |
| outbox relay | relay 停摆、确认缺失、pending 意图反复重试 | 最老 pending outbox 年龄、认领过期数、发布确认失败 | relay 运行时间、数据库扫描与发布请求 |
| 队列 / worker | 重复/延迟投递、毒消息、积压上升、执行槽耗尽、过期租约接管 | 最老消息年龄、队列深度、未确认数、死信队列、物理执行槽、过期 lease 与恢复结果 | 保留消息、worker 计算、积压排空与孤儿对象清理 |

平台容量与业务结果要分开观察。CPU 不高并不能证明 report 42 可正确读取；queue 有消费者也不代表报表已经成功。组件信号还要与用户的 service level indicator（服务等级指标，SLI）和 request/job 结果连接；报表服务如何定义目标结果并定位发布故障，见[怎样从报表服务信号定位发布后的故障？](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)。

> [!info]- 来源
> - **HTTP 异步受理状态。** [IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) §15.3.3 定义 `202 Accepted` 表示请求已接受处理但尚未完成；本文在此基础上要求只有 job/outbox/等待槽事务提交后才回 202，后者是本案例的持久受理契约，不是 RFC 单独规定的数据库实现；checked 2026-11-12。
> - **网络入口、私有对象和 bearer URL。** Amazon S3 [Download and upload objects with presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)：URL 按签发主体权限授权、可在到期前重复使用、浏览器可以直接使用，临时凭据到期或撤销会提前失效；[Controlling access from VPC endpoints with bucket policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies-vpc-endpoint.html)：bucket policy 可拒绝没有经过指定 VPC endpoint 的请求；checked 2026-11-12。CloudFront [Serve private content with signed URLs and signed cookies](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html) 与[Restrict access to files](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-overview.html)：若用 CDN 分发私有对象，应配置签名访问并限制绕过 CDN 直达源站的路径；checked 2026-11-12。
> - **函数时长、重试和环境复用。** AWS Lambda [Designing Lambda applications](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html) §“Build for on-demand data instead of batches” 和 [Understanding the Lambda execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) §“Invoke phase”：默认函数调用上限、Lambda Managed Instances、durable functions 的不同期限与检查点语义；函数可能复用环境，但不会永久保留，重复事件要求幂等；checked 2026-11-12。这些结论只适用于所列 Lambda 模式，不代表所有函数服务。
> - **Kubernetes 探针与终止。** Kubernetes v1.37 当前文档 [Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)、[EndpointSlice conditions](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/#conditions)、[Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) 和 [Deployment API](https://kubernetes.io/docs/reference/kubernetes-api/apps/deployment-v1/)：Pod 删除时控制面评估 EndpointSlice 与 kubelet 本地优雅停止同时开始；终止中的端点可暂时保留但 `ready: false`，代理对全体端点均终止时存在继续路由至 `serving && terminating` 端点的行为，`publishNotReadyAddresses` 会影响 `ready`；Deployment 的 `restartPolicy` 只允许 `Always`；checked 2026-11-12。集群代理、入口控制器和 Service 配置会影响实际路由。
> - **ECS 身份、密钥注入和停止。** [ECS task IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)、[task execution role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)、[IAM role best practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html)、[Secrets Manager environment injection](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html) 与 [task lifecycle](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-lifecycle-explanation.html)：区分容器应用的 task role 与平台 agent 的 execution role、临时凭据、Secret 在启动时注入、版本引用规则与强制新部署、容器/task 隔离边界；仅配置负载均衡目标组的 service task 在 DEACTIVATING 注销目标，再于 STOPPING 发停止信号。[ContainerDefinition API](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ContainerDefinition.html) 中字段名为 `stopTimeout`，核到 Fargate 默认 30 秒/最大 120 秒与 ECS on EC2 agent 默认；checked 2026-11-12。AWS SDK [standardized credential providers](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html) 与 [container credential provider](https://docs.aws.amazon.com/sdkref/latest/guide/feature-container-credentials.html)：标准支持的 credential provider 会自动尝试更新临时凭据，具体仍由 SDK 实现决定；checked 2026-11-12。
> - **队列取消和 ACK。** RabbitMQ 4.4 [Consumers: Cancelling a consumer](https://www.rabbitmq.com/docs/consumers#cancelling-a-consumer-unsubscribing)：`basic.cancel` 阻止后续分发，但已有未确认投递不会自动丢弃或重排；关闭 channel 会自动重排其中仍未确认的投递；checked 2026-11-12。[Negative Acknowledgement and Requeuing](https://www.rabbitmq.com/docs/confirms#consumer-nacks-requeue) 同时说明 `basic.reject` / `basic.nack` 配合 `requeue=true` 可显式重排。上述行为只适用于 RabbitMQ 的相应协议/客户端路径，其他 broker 要按自身契约验证。
> - **Secrets Manager 审计与加密。** [GetSecretValue API](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html) 说明 API response 有 VersionId、SecretString/Binary 是敏感字段、不写入 CloudTrail，以及客户自管 KMS key 时需要 `kms:Decrypt`；[CloudTrail entries for Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/cloudtrail_log_entries.html) 说明 GetSecretValue 产生日志事件；checked 2026-11-12。API 响应字段不等于 CloudTrail 事件字段，因此本文不假定事件含 VersionId 或 taskArn。
> - **合成 Webhook 契约与 HMAC。** [Webhook 接收方如何验证并可靠受理？](#17.%20Webhook%EF%BC%88%E5%9B%9E%E8%B0%83%E9%80%9A%E7%9F%A5%EF%BC%89%E6%8E%A5%E6%94%B6%E6%96%B9%E5%A6%82%E4%BD%95%E9%AA%8C%E8%AF%81%E5%B9%B6%E5%8F%AF%E9%9D%A0%E5%8F%97%E7%90%86%EF%BC%9F) 明确其 HMAC、时间窗、事件期限和重试配置都是应用自定的合成协议；本文的 300 秒和 30 天仅复用该教学例，checked 2026-11-12。HMAC 的通用构造见 [IETF RFC 2104](https://www.rfc-editor.org/rfc/rfc2104.html) §2：签名与验证都依赖共享密钥，因此同一持钥方可以计算或验证 MAC；RFC 不规定 Webhook 的 keyId、请求字段或时间期限。
> - 本文用一个通用拓扑说明网络/身份边界，并分别标明 S3、ECS、Lambda、Kubernetes 的平台行为；实际系统应按部署所用版本、网络策略和服务合同核对。
## 35. 如何晋级并回滚已验证的报表服务产物？

**案例背景。** 一个假设的报表服务修复了租户授权漏洞，提交标识为 `c4f2a91`。发布要让用户逐步用上已经验证的版本；若验证失败，还要能转到安全、数据兼容的版本。本章沿这次发布，解释源码、镜像、配置、流量和数据分别在什么时候交接。

continuous integration (持续集成，CI) 先检查这份源码，并构建一次镜像。预发布环境用这份 image digest (镜像摘要) 启动服务，复放租户授权和异步任务。生产环境获批后也启动这份摘要，等待就绪并检查关键业务路径，再开放少量真实 HTTP 请求。之后，发布负责人或控制器根据新版本的请求、依赖和 worker (工作进程) 信号，决定加流、保持比例或止损。

continuous delivery (持续交付，CD) 指通过检查后随时可发布；continuous deployment (持续部署) 指门禁满足后自动发布。审批允许部署继续，流量仍要等后续条件满足才切换；API 入口切流也不会自动改变独立 worker 的消息消费。

以下流程从已隔离已知风险入口的状态开始；图中的“不切流”表示继续阻止真实用户请求进入尚未验收的新摘要。

![CI 固定源码并构建一份摘要；预发布验收、生产门禁、启动就绪和新摘要上的生产授权冒烟检查依次通过后，才开放首轮小流量。任一步失败时，不向尚未验收的新摘要开放真实用户流量。](../../engineering-foundations/infrastructure/resources/application-deployment-flow.svg)

图中的批准、启动、就绪和切流是四个不同状态。各角色也有不同责任：CI 检出并检查源码、构建产物、记录证据；预发布检查负责人确认业务验收；环境审批者放行生产部署；部署系统启动被批准的版本；流量入口只对就绪目标分配请求；发布负责人或已配置的控制器判断何时增加流量和何时止损。进入 10% 小流量是本例的示意起点，不是通用部署比例。随后继续、保持、停止或回退的条件在第二节说明。

### 一次构建，逐级测试并记录产物身份

先固定发布输入。CI 应检出确切的 commit (提交) `c4f2a91`，确认工作区干净，并把经过检查的源码树用作唯一 build context (构建上下文)。构建上下文是发送给 builder (构建器) 的文件集合；目录 `.` 只有在它就是预期源码根、且没有未跟踪的本机文件时才代表该提交。`.dockerignore` 应排除 `.git/`、虚拟环境、本机日志、真实 `.env` 和密钥文件。依赖锁文件、Dockerfile、基础镜像解析结果、构建器版本、平台和构建参数也属于产物来源记录。基础镜像 tag (标签) 和外部依赖可移动或更新，因此从同一源码树分别重建也可能得到不同内容；预发布与生产应晋级一次构建得到的摘要，不应各自重新构建。

检查随风险而定：提交级检查确认静态规则、单元和集成路径；涉及租户授权时，用两个独立认证身份访问同一张示例报表 42，tenant-a 必须返回 200 和预期内容，tenant-b 必须得到本例约定的 404。两种身份都经真实认证流程建立，不能用客户端自行填写的租户头代替身份；涉及 worker 时还要走真实消息代理的投递、持久化与 acknowledgement（确认，ACK）路径。若合并或重写提交改变了源码树，应在最终构建提交上重跑必要门禁，或提供可核验的树相同证据。构建和检查不能只靠同一条可移动标签推断彼此对应。

推送构建的例子把 metadata file (元数据文件) 放在本次任务独有的临时路径。`set -euo pipefail` 使 buildx 失败时命令串立即停止；`jq -e` 要求本次文件里有格式正确的 SHA-256 digest。最后的 `imagetools inspect` 按该摘要读取 registry (镜像仓库) 的实际清单：

~~~bash
set -euo pipefail
metadata_file="$(mktemp "${TMPDIR:-/tmp}/report-build.XXXXXX")"
trap 'rm -f "$metadata_file"' EXIT

docker buildx build \
  --push \
  --metadata-file "$metadata_file" \
  --tag registry.example.com/team/report-api:c4f2a91 \
  .
digest="$(
  jq -er '
    ."containerimage.digest"
    | select(type == "string" and test("^sha256:[0-9a-f]{64}$"))
  ' "$metadata_file"
)"
docker buildx imagetools inspect \
  "registry.example.com/team/report-api@$digest"
~~~

命令中的 registry、tag 和提交均是示意值；它从当前已确认的干净目录 `.` 构建。若 buildx 失败，脚本不会读取任何旧文件；若 metadata 缺字段或不是 SHA-256 摘要，`jq -e` 会失败；推送命令成功后仍通过远端检查确认 registry 清单。`containerimage.digest` 固定的是镜像清单内容身份，不会单独证明内容来自 `c4f2a91`。CI 还应保留提交、依赖锁、基础镜像摘要、构建器、目标平台和测试结果，并用可核验的 provenance (构建来源证明) 关联源码与产物。示例命令会实际向 registry 发布镜像；这里仅展示，不执行。

Buildx 的 `--load` 等价于 `--output=type=docker`，把结果载入本机 image store (镜像存储)；是否能载入多平台镜像取决于 builder 和 image store。classic image store (经典镜像存储) 不支持 image index 或 manifest list (清单列表)，因此不能在本机载入多平台镜像；containerd image store (containerd 镜像存储) 支持。Docker Engine 29.0+ 新安装默认使用 containerd image store，Docker Desktop 也默认使用它；升级旧 Engine 的机器仍可能保留 classic store。单看本地输出和 metadata 不证明 registry 已收到该镜像。多平台 build 可能生成一个 index digest (索引摘要)，该索引引用 `linux/amd64`、`linux/arm64` 等平台各自的 manifest digest (清单摘要)。核对索引与子摘要只证明清单之间的映射；如果预发布只运行了 amd64，而生产选用 arm64，就还没有验证实际生产子镜像。要在对应生产平台的预发布目标运行并验收每个将部署的子摘要，或把生产目标限制为预发布实际运行的平台。

门禁职责也要明确。GitHub Actions `environment` 可以配置必需审查者、部署分支限制、等待规则和环境 secrets（密钥）；引用该 environment 的 job 必须通过生效的保护规则后，才会执行受保护的部署步骤或取得相应 secret。规则可用性受计划和仓库配置影响，审批通过只表示允许该 job 继续，部署、启动、就绪和切流仍是后续状态。

第三方 GitHub Action（自动化操作）的 `uses: owner/repo@ref` 要固定到已核验的完整 commit SHA；也可对已纳入锁文件的 workflow 使用 workflow dependency lockfile (工作流依赖锁文件)，锁定远端步骤级 Action 及其传递依赖。仓库里存在锁文件不表示每条 workflow 都已纳入。本地步骤级 Action 的 `uses: ./path` 来自调用工作区，默认不作为锁文件依赖锁定。同仓的 reusable workflow (可复用工作流) 若写为 `uses: ./.github/workflows/deploy.yml`，由调用者的同一 commit 确定，不需要添加 `@ref`；跨仓可复用工作流的 `owner/repo/.github/workflows/deploy.yml@ref` 是另一种引用，应固定完整 SHA。其 Action 依赖只能由定义该 workflow 的仓库在将该 workflow 纳入相应依赖锁文件后锁定；调用仓库的锁文件不能替它锁定。GitHub 于 2026-10-28 宣布 workflow lockfiles 一般可用。Action 锁文件不锁 job 级可复用 workflow 调用、构建参数、secret 或 runner (工作流执行器) 镜像。

应用配置跟随部署版本记录，但密钥值留在 secret store (密钥存储服务)：数据库地址、启用的功能开关及配置版本可纳入受控配置，部署记录保存 secret 的名称或版本引用和适用范围，不保存值。若静态前端跨环境晋级同一 bundle (打包文件)，但各环境的非秘密值不同，可由 bundle 在运行时读取环境专属配置端点或配置文件；部署记录保存 bundle ID、配置版本和校验和，密钥仍只由服务端或密钥服务提供。编译期写进浏览器 bundle 的值可被用户读取，不能放秘密。静态资源的缓存与构建细节见[前端构建产物如何部署与缓存？](../../frontend/tooling/build-tools.md)。

### 将环境门禁、启动检查和渐进放量接起来

部署前核对目标环境的 identity and access management (身份与访问管理，IAM) 权限、网络路由、密钥来源和数据库迁移状态。环境审批通过后，部署系统用预发布已验收的同一摘要启动生产实例，附上版本化运行配置和密钥引用。新实例通过目标平台的 readiness check (就绪检查) 前，入口继续把流量送给当前版本。就绪只表示实例满足平台接流量的条件，不表示报表授权、异步导出或租户数据都正确。先执行 production smoke test (生产冒烟检查)：通过生产入口的受控测试路由，将专用测试身份 tenant-a 和 tenant-b 对示例报表 42 的请求都固定到同一轮新发布目标，检查 tenant-a 得到 200 和预期内容、tenant-b 得到 404，并在两次内部追踪中都确认请求命中本轮新摘要。任一身份结果错误时不开 10% 流量并定位业务错误；追踪、版本或摘要证据缺失时不开流并补齐证据。多平台发布还记录该实例的平台子摘要，并确认它等于该平台已验收的子摘要；仅确认它属于已验收索引不足以证明实际运行过该平台内容。测试路由必须保留正常认证与授权逻辑；若平台不能保证两项请求都命中新摘要，就先不开放 10% 小流量。两项请求都通过后才开放本例 10% 的真实 HTTP 小流量。readiness 只表明平台可把新流量发给实例；生产冒烟检查验证目标版本的关键业务路径；之后的用户 service level indicator (服务等级指标，SLI) 则按发布版本和平台子摘要归属统计，不能让稳定版结果掩盖本轮版本。

Kubernetes 中，Pod (容器组) 是承载一个或多个容器的调度单元，可配置 startup probe (启动探针)、liveness probe (存活探针) 和 readiness probe (就绪探针)：配置 startup 后，在它成功前 kubelet (节点上的容器管理代理) 不执行另两种探针；startup 或 liveness 达到 `failureThreshold` 后，kubelet 终止容器，再按 Pod 策略重启。readiness 失败会把 Pod 标成未就绪；默认 EndpointSlice (端点切片) 仍保留其地址，但将 `ready` 标为 `false`，匹配的 Service (服务对象) 不再把它作为就绪端点发送常规新流量。Service 设置 `publishNotReadyAddresses: true` 时该条件会被忽略。readiness 失败不会重启容器。Deployment (部署控制器) 的 Pod 模板只允许 `restartPolicy: Always`；这些是 Kubernetes 的行为，其他平台应查自己的语义。不要让 liveness 依赖每个短暂下游故障，否则多个副本可能一起重启，反而放大故障。

![逐轮判断只使用可归因到本轮摘要的证据：SLI 与业务达到加流门槛才加流，低于门槛但未止损时保持，越界时止损；切回安全候选或隔离并前向修复后，都要复验预期摘要、配置、两种身份结果和 worker。](../../engineering-foundations/infrastructure/resources/application-deployment-decision.svg)

SLI 的短期放量每一轮都要有完整证据。每轮先用生产冒烟检查对本轮目标摘要执行受控身份复测，并确认追踪记录中的版本和摘要；然后只统计归属于该版本的合格请求、错误/延迟、依赖容量，以及 worker 的队列最老消息年龄、未确认量和代表性任务结果。若版本标签缺失、聚合无法区分新旧版本，或两种身份测试未命中新摘要，就保持流量比例并补证据，不以稳定版结果替新版本背书。可承接[发布后故障诊断](#36.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BF%A1%E5%8F%B7%E5%AE%9A%E4%BD%8D%E5%8F%91%E5%B8%83%E5%90%8E%E7%9A%84%E6%95%85%E9%9A%9C%EF%BC%9F)中的示例短期条件：滚动 10 分钟内至少有 100 个符合条件的目标版本请求，好事件率达到至少 99%，并通过上述授权与任务检查。这里的 10 分钟、100 次和 99% 是合成示例，不是所有服务通用的阈值；另有告警若需连续 5 分钟越界才触发，不能用“告警没响”代替当前放量条件。若 100 个目标版本请求中 98 个为好事件，本例的 99% 加流门槛未达标；若尚未触发另行定义的止损条件，就保持比例并调查。租户授权契约失败仍须立即止损，不等统计窗口。

对每一轮小流量，发布负责人或控制器按以下规则决定。tenant-b 若读到不属于自己的内容是已确认的数据泄露，不能被 99% 汇总成功率平均掉，必须立即止损：

| 观察结果 | 动作 | 为什么 |
|---|---|---|
| 本轮新摘要的样本达到当前窗口要求、遥测完整、本轮 SLI 达到加流门槛、两种授权测试都确认命中新摘要并通过、依赖与任务信号在发布门槛内 | 按预定小步提高入口比例，每次都用目标版本的新窗口复核；达到 100% 后先检查最终窗口，全部门禁仍达标才结束本轮放量 | 只有可归因到本轮目标版本且达到本轮 SLI 门槛的代表性结果，才能支持更多用户经过它 |
| 请求不足、任一身份测试未确认命中新摘要、业务测试未执行、遥测缺失或聚合延迟；或本轮 SLI 低于加流门槛但尚未越过止损阈值，因而当前无法加流 | 保持当前比例；调查指标并补齐定向身份测试或版本遥测，取得完整窗口后再决定 | 未达加流门槛就不能增加流量；尚未触发止损条件也不等于必须回退 |
| 租户授权契约失败，或错误/延迟、依赖饱和、任务结果越过预先定义的止损阈值 | 停止继续增加比例，限制或移除问题版本的相关流量；检查安全候选并执行回退、隔离或前向修复 | 已确认的用户伤害不能靠尚未触发的告警门槛抵消 |

小流量本身可能无法产生 100 个符合条件的新摘要请求。如果合成请求被纳入分母，应在度量定义中事先说明并单独标记；不要将反复运行的测试身份伪装成真实用户流量。对于低流量服务，可结合生产冒烟检查、依赖和任务信号，或者在更长但仍预先定义的窗口收集目标版本证据；无论如何，样本不足时保持现有比例，不把不确定性记作成功。若稳定版已知有与本次修复相关的漏洞，在开出金丝雀前先隔离受影响入口，不能让仍暴露的稳定实例继续承担该路径。

HTTP 入口和 worker 是两个独立的控制面。入口按版本或实例权重分配新的请求，不会停止旧 worker 或让新 worker 自动切换队列消费。发布 worker 时，应单独决定是否暂停旧消费者、等待或释放在途任务、启动多少新消费者，以及如何检查队列延迟和 ACK；API readiness 只影响 API 流量。消息提交、重投和重复处理的边界见[发布确认与消费者 ACK](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)；进程优雅停止的职责见[报表 API 与异步 worker 应由什么运行时承接？](#34.%20%E6%8A%A5%E8%A1%A8%20API%20%E4%B8%8E%E5%BC%82%E6%AD%A5%20worker%20%E5%BA%94%E7%94%B1%E4%BB%80%E4%B9%88%E8%BF%90%E8%A1%8C%E6%97%B6%E6%89%BF%E6%8E%A5%EF%BC%9F)。

### 回退代码时不要假设数据也回去了

每次发布前记下当前稳定的镜像摘要、配置版本、入口路由比例、worker 部署状态、数据库结构版本和候选回退摘要。secret 只记录版本或引用，不复制密钥值。数据库变化和远端副作用也要列出兼容条件。发布出问题时，先停止放量并处置仍落在坏版本上的流量；如果已知旧版本仍含 tenant-a/tenant-b 跨租户漏洞，就不能把入口恢复到那个旧摘要。在开放 10% 金丝雀之前也先评估稳定实例：若它仍会接收有漏洞的受影响请求，先隔离该路径或让流量避开危险实例。部署前要确认的对象是当前安全、数据兼容且能恢复容量的候选版本，可能是最近稳定版本，也可能是更早的修复版。

安全候选已运行且就绪、有足够容量时，入口可先把新请求切回该候选、将不安全版本的权重降到零；若候选已下线或容量不足，先按记录恢复准确摘要与兼容配置并补足容量，等待目标就绪后再将流量切过去。若任何历史版本都不满足权限或数据不变量，就隔离受影响入口或功能，停止危险 worker 消费，并前向发布修复版。切流只是控制面提出的期望状态，回退或前向修复完成后还需核对：坏摘要已不再接请求；实际运行的目标摘要和适用配置正确；API 经生产入口以受控身份访问 report 42 时，tenant-a 得到 200/预期内容、tenant-b 得到 404，且追踪确认两者命中预期摘要；worker 的代表性任务和 ACK/队列年龄恢复。数据或遥测样本未达条件时保持修复后的低风险状态并继续取证，不因“恢复命令已成功”宣布完成。

数据库迁移通常先让新旧版本可共存，再在确认旧版本不会回来后收缩。假设旧列为 `report_name_old`，新列为 `report_name`：

1. **扩展。** 添加新列并暂时保持旧列为权威写入源。旧版 API 或 worker 此时仍只写旧列。
2. **捕获并回填。** 在回填开始前启用数据库触发器或变更捕获，记录旧列每次更新。分批回填时用行版本或更新时间保护并发修改，避免一个已读出的旧快照覆盖更新后的值；也可按提交顺序重放捕获的变更。旧列仍是写入权威，持续核对两列并追到明确水位，但这次核对还不能授权切换：旧写入仍可能在检查后提交。
3. **兼容发布与切换权威。** 新版代码先保持对新旧结构的兼容；旧列仍是读写权威，新版可在同一事务更新两列，而旧版写入由触发器或捕获流程复制到新列。对异步捕获，在切读写权威之前先暂停旧侧接收新写、排空在途任务，再记录旧侧最后一个已提交变更水位；等待捕获流程追到该水位并核对差异后，才把读写权威切到新列并开放新写入。若数据库事务能原子维护两种表示、原子选择权威，且没有绕过事务的写入者，可在事务边界协调切换，不必把停写扩大成所有方案都必须停写。
4. **保留可回退窗口。** 若允许回退到只读取旧列的版本，就要把新列权威期的每次写入也同步回旧列，例如同一事务双写，或使用有序反向变更捕获。异步模式下，切回旧列前先暂停新侧接收新写、排空在途任务，再记录新侧最后提交水位；保持新侧写入冻结或隔离，直到反向捕获追平并核对，然后才把读写权威交回旧列。随后在解冻旧版写入前，重新启用旧到新的同步或等价兼容写路径，确保旧版写入继续更新新列。无法维持这一条件时，冻结或隔离新写并缩小可回退版本集合；若数据已不兼容，就隔离或前向修复，不能假定旧版读旧列仍能得到当前事实。
5. **收缩。** 只有所有现行进程、在途任务和获准恢复的旧版本都不再读取或写入旧列，才停止同步并删除旧列。

捕获、回填、双写和反向同步的具体实现依数据库与业务写入模型设计；异步捕获必须定义提交顺序、水位和重放/重复处理语义，并在切换读写权威前暂停离任侧新写、排空在途写并等待最后提交追平。独立迁移任务与锁只避免并发执行，不保证任务严格执行一次；任务还需要版本记录、幂等批次、检查点和可恢复步骤。重试前核实部分批次的真实数据库状态。

例如 Amazon ECS 的 rolling deployment（滚动部署）断路器可以在配置开启时，因任务无法进入 steady state（稳定状态）判定部署失败；配置 rollback 后可恢复到最近一个 `COMPLETED` 部署。该自动回退只适用于 ECS 的 rolling update 部署类型且依赖已有完成版本，不是一般 canary（金丝雀发布）、蓝绿部署或任意平台的通用保证。平台的任务健康也不验证租户授权和 worker 业务契约；切回后仍要执行前述实际入口和任务复验。

无论应用是否回退，都不会自动撤销已经提交的 job、已引用的对象、已发出的邮件或已完成的支付。需要恢复的外部效果必须有对应补偿、幂等和审计边界；数据库备份恢复可能丢失备份之后的写入，是单独的数据恢复决策。发布版本、安全状态、数据兼容和外部效果要一起复核，才能确认止损已完成。

> [!info]- 来源
> - 持续交付与持续部署：[DORA continuous delivery](https://dora.dev/capabilities/continuous-delivery/)，checked 2026-11-12；将随时可发布与门禁满足后自动发布区分开。
> - 构建输入、缓存与机密：[Dockerfile reference](https://docs.docker.com/reference/dockerfile/)、[building best practices](https://docs.docker.com/build/building/best-practices/)、[optimize cache usage](https://docs.docker.com/build/cache/optimize/)、[Build secrets](https://docs.docker.com/build/building/secrets/)，checked 2026-11-12；覆盖 `RUN`/`CMD`/`ENTRYPOINT`、`.dockerignore`、层缓存、BuildKit secret mount 与不得把密钥放入 `ARG`/`ENV` 的边界。
> - 摘要、平台清单、Buildx metadata 与来源证明：[Docker Buildx build](https://docs.docker.com/reference/cli/docker/buildx/build/)（`--load`、`--push`、`--metadata-file`）、[Docker Desktop containerd image store](https://docs.docker.com/desktop/features/containerd/)（classic store 不支持多平台镜像，containerd store 支持）、[Docker multi-platform builds](https://docs.docker.com/build/building/multi-platform/)（Docker Engine 29.0+ 的默认 image store）、[imagetools inspect](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/)、[Docker image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/)（tag、索引与子清单）、[Build provenance attestations](https://docs.docker.com/build/metadata/attestations/slsa-provenance/)，checked 2026-11-12；本机多平台加载的能力分支见 [Buildx v0.39.0 exporter 选择](https://github.com/docker/buildx/blob/v0.39.0/build/opt.go#L494-L538)：发现 OCI importer 时切换导出类型，否则多平台 Docker 导出会报错。CLI 单平台示例不能据此推成所有 builder/store 的限制。摘要标识内容；代码提交与产物的联系需额外来源证据。
> - GitHub 环境门禁及 workflow 依赖：[deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)、[secure use](https://docs.github.com/en/actions/reference/security/secure-use)、[workflow dependency lockfiles](https://docs.github.com/en/actions/how-tos/secure-your-work/lock-workflow-dependencies)、[2026-10-28 lockfiles GA announcement](https://github.blog/changelog/2026-10-28-github-actions-workflow-lockfiles-are-generally-available/)、[reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)，checked 2026-11-12。GA 公告列出 Enterprise Cloud（含 data residency）、Team、Free；依赖须按 workflow 逐条纳入锁文件；锁文件覆盖相应远端步骤级 Action 和传递依赖，但默认不锁本地路径 Action；跨仓可复用 workflow 的调用 `@ref` 应固定完整 SHA，其 Action 依赖只有在定义仓库也将该 workflow 纳入自身锁文件后才会被该仓锁定，调用仓库的锁文件不能替代。同仓相对 workflow 来自同一调用提交。
> - Kubernetes 探针、EndpointSlice 条件与 Deployment API：[Kubernetes releases](https://kubernetes.io/releases/)、[Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)、[EndpointSlice conditions](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/#conditions)、[Deployment API](https://kubernetes.io/docs/reference/kubernetes-api/apps/deployment-v1/) 及 [Pod lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)，Kubernetes v1.37.1 当前维护文档 checked 2026-11-12；readiness 失败时 v1.37 controller 保留地址并将 `ready` 置 `false`（`publishNotReadyAddresses` 除外），Deployment 模板只允许 `restartPolicy: Always`。探针文档正文称 EndpointSlice 控制器移除 Pod IP；版本控制器的 `podToEndpoint` 则把保留地址与 `ready: false` 条件写入 Endpoint，本文按该具体 API 对象解释，见 [v1.37 controller 的 `podToEndpoint`](https://github.com/kubernetes/kubernetes/blob/v1.37.1/staging/src/k8s.io/endpointslice/utils.go#L33-L53)。
> - ECS 滚动部署失败检测：[deployment failure detection](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-failure-detection.html)、[deployment circuit breaker API](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentCircuitBreaker.html)，checked 2026-11-12；断路器仅支持 rolling update，回滚目标需为先前 `COMPLETED` 部署。
> - 并行代码与结构迁移：[AWS blue/green deployment whitepaper—Decoupling schema changes from code changes](https://docs.aws.amazon.com/pdfs/whitepapers/latest/blue-green-deployments/blue-green-deployments.pdf) 与[数据同步和 schema changes 最佳实践](https://docs.aws.amazon.com/whitepapers/latest/blue-green-deployments/best-practices-for-managing-data-synchronization-and-schema-changes.html)，checked 2026-11-12。文中捕获变更、回填防覆盖和保留回退读路径是按本文示例推导的通用安排，实际机制须匹配所选数据库与写入模型。
> - 放量信号的窗口示例：[怎样定义 SLI、SLO 和恢复证据？](#%E6%8C%89%E8%AF%81%E6%8D%AE%E7%BC%93%E8%A7%A3%E5%B9%B6%E7%A1%AE%E8%AE%A4%E6%81%A2%E5%A4%8D)，该章示例的 10 分钟、100 个合格请求和 99% 好事件率仅为说明条件的合成值，checked 2026-11-12。
## 36. 怎样从报表服务信号定位发布后的故障？

**案例背景。** 报表服务 `report-api` 正在把少量流量交给新镜像摘要 `d-new`，观察它是否可以继续放量。用户读取账户 `acct-17` 的报表 42 时变慢或遇到 `5xx`；同一时段，CSV（逗号分隔值）导出请求已收到 HTTP（超文本传输协议）`202 Accepted`，却迟迟没有结果。本页先定义怎样衡量这两种用户体验，再用 metrics（指标）、trace（追踪）和 logs（日志）定位受影响阶段，最后验证缓解后的读取、生成与下载。数字、身份和故障记录均为教学构造。

本例沿用合成账户 `acct-17`、报表 `42`、幂等键 `report-demo-208` 和任务 `job-demo-731`。事务里先尝试写入稳定任务 ID；提交后该 ID 才是持久且可查询的事实。读请求、导出受理、后台任务完成和结果下载是不同边界：`202 Accepted` 只表示服务已按本例合同持久化接收任务，不表示任务完成；任务只有在数据库提交 `succeeded` 和私有结果对象引用后才算生成完成；`report.ready` 的发送和消费者 ACK（消费者确认）也不是下载成功。先分清这些结果，才不会让错误的分母或信号带偏事故判断。

发布门禁应按已发布镜像摘要和目标 SLI 评估，完整构建到流量的边界见[测试验收与发布流程](#35.%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B9%B6%E5%9B%9E%E6%BB%9A%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E4%BA%A7%E7%89%A9%EF%BC%9F)。队列中的受理、尝试和 ACK 由[发布确认与消费者 ACK](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)定义；本页沿用其数据库权威状态合同。

### 从一个用户请求关联三种信号

先把一次用户意图拆成可度量的单位。`request`（请求）衡量每次 API（应用程序接口）往返，`job`（任务）衡量唯一持久任务，`attempt`（尝试）衡量 worker（工作进程）每次实际领取的执行轮次。客户端重试会增加请求数；同一个任务的多次 attempt 仍只是一项用户工作。

![从用户结果到信号定位、缓解和复验的短路径](../../engineering-foundations/reliability/resources/observability-diagnosis-flow.svg)

| 单位 | 分母如何计数 | 结果归属 |
|---|---|---|
| API request | 每次到达已定义服务边界且满足该 SLI 入选条件的调用 | 按该 API 的用户结果判好坏；不能把未响应的调用删掉 |
| accepted job | 每个唯一 `jobId` 一次；只要受理事务提交，就计入，即使 `202` 响应丢失 | 到自己的完成期限时判断成功、失败或仍待处理 |
| worker attempt | 每次数据库成功领取一次 | 诊断执行耗时、重试和资源占用；不作为用户完成率分母 |

沿用本例最多 3 次 attempt（首次领取也计一次）。只有数据库领取提交才开始一轮 attempt；重复 broker（消息代理）投递只是唤醒线索，不能重复算成一次新尝试。

#### 先定义读请求和导出的 SLI

service level indicator（服务等级指标，SLI）是对明确用户结果的测量；service level objective（服务等级目标，SLO）给它设定目标。两者都要先规定边界、分母、好事件、时间窗口和数据延迟，不能只写“成功率”。

##### 读取：按权限关系判断响应是否正确

以可信身份边界已确认主体、且报表 ID 格式有效后进入 API 的每次 `GET /api/reports/{id}` 为分母。有权主体 `principal-P17` 对 `acct-17` 的 `report 42` 有读取权；独立身份 `principal-PB` 无权读它，本例按策略返回 `404`。好事件要求 API 在 400 ms 内给出与这项权限关系一致的结果：有权请求返回 `200` 和预期报表，无权请求返回正确的 `404`。因此 `404` 是否为好事件取决于主体和资源的授权关系，不能只按状态码分类。有权请求误得 `404`、超时、无响应或 `5xx` 都是坏事件。

入口记录每次合格请求的时间、路由、区域和实际目标摘要，即使服务没有响应也保留；未响应请求即使没有摘要归属，也仍是坏事件，但不能拿它证明金丝雀健康。

只读响应码和耗时是可观测代理，不能单独证明正文正确；本例另外用有权与无权测试身份、已知报表标记核验授权和内容。若要声称每次真实响应都内容正确，就需要每次响应都有可信的内容/授权判定证据。身份服务在主体确认前的失败另计入口认证 SLI。这里的响应边界不覆盖用户设备或响应后的网络，也不能替代跨租户授权测试与审计。
##### 受理：一次请求与一个持久任务分别计数

以每次进入导出 API、身份已确认、调用主体对该账户有导出权限且请求格式有效的调用为请求分母；每次同键重试各算一次请求。首次有效意图只有在同一数据库事务提交 job、待发 outbox（事务发件箱）意图和一个等待槽后才创建 accepted job；数据库提交是裁决点，响应返回与否不改变是否已有一个 job。正常返回的 `202` 是服务观察到提交成功后给客户端的响应证据，不是任务分母的定义。

正确的同键、同指纹重放应指向原 job 并返回其当前持久状态，不增加 job 数或等待槽；它仍是一条好请求。

明确返回 `429`（速率限制）或 `503`（等待槽满）是受理请求的坏结果，但依本例受理合同没有创建 job；在本 SLI 的服务响应边界内观察到的超时或无响应记请求坏；服务已返回后才发生的客户端网络断开不归入这个 API SLI。客户端对是否已经受理保持未知，按 `(account_id, principal_id, key)` 查权威状态，不能由客户端没收到 `202` 推断未受理。相同幂等键却不同正文是客户端契约冲突，单列计数并排除在本例可靠性请求分母之外。这样，请求 SLI 衡量服务对一个合格意图的响应，job 分母只由数据库提交裁决。本例 `202` 的强持久化要求比 HTTP 对 `202 Accepted` 的通用语义更具体。
##### 完成：先说清测到的是提交，还是提交确认

一个已提交的唯一 job 只计一次，投递、重试和 attempt 不增加分母。成功事务将 `succeeded`、结果对象引用与 `report.ready` outbox 原子提交；客户端有没有收到 `202` 都不改变数据库里的事实。沿用本例业务目标，结果应在接受后 2 分钟内生成并提交。

但业务目标与现有遥测未必使用同一个时刻。本页假设可取得的是应用收到成功 `COMMIT` 响应后，再向同一数据库查询 `clock_timestamp()` 所记录的确认事件：`accepted_commit_confirmed_at` 和 `succeeded_commit_confirmed_at`。它们测量的是服务确认提交的时间。下文据此计算**提交确认完成 SLI**：以受理确认为起点，判断截至其后 2 分钟的观测期限是否已观察到成功确认。受理端确认采集可能更迟；若成功确认已先观察到，本口径视为已达标，不能由确认先后推断物理提交顺序。如果要验证“数据库必须在 2 分钟内提交”的物理时限，还需要经验证的权威提交时刻。

> [!info] 两次确认的时间差为什么不一定更保守？
>
> 接受提交与成功提交后的确认等待可能不同。物理提交间隔 121 秒，若前一次确认等了 10 秒、后一次等了 1 秒，观测间隔就成了 `121 + 1 − 10 = 112` 秒；反过来也可能高估。本例只把它当作独立的服务观察口径。事务内的 `accepted_at`、`succeeded_at` 也不能自动当成提交时刻：PostgreSQL 的 `now()` 使用事务开始时间。`track_commit_timestamp` 开启后可查询部分事务提交时间，但该信息会被 vacuum 清理，不能假设配置已开启或历史永远保留。

接下来要防止只统计已完成任务的偏差。给每个 job 定义观测期限 `due = accepted_commit_confirmed_at + 2 min`，窗口 `(T−W, T]` 只收进 `T−W < due ≤ T` 的成熟任务；也就是期限落在本窗口的任务。成功确认必须满足 `succeeded_commit_confirmed_at ≤ due`。`failed`、`cancelled`、到期仍 `queued`/`running` 和迟到才成功都计坏。本例把已受理后的取消视为未完成；若要排除用户主动取消，应另定义可审计的取消来源和分母规则。期限还没到的任务暂不进分母，同时观察其最老待处理年龄。

> [!example] 12:00 结束的十分钟窗口，哪些任务已经到期？
>
> 以下均使用提交**确认**时间；窗口为 `(11:50, 12:00]`。表中“坏”只裁决确认 SLI。
>
> | 接受确认 → 期限 | 成功确认 | 这个窗口怎样计数 |
> | --- | --- | --- |
> | 11:57:00 → 11:59:00 | 11:59:01 | 121 秒，计坏；不能据此认定物理提交也晚了 1 秒 |
> | 11:59:30 → 12:01:30 | 尚未观察到 | 期限还没到，不进本窗口分母 |
> | 11:58:00 → 12:00:00 | 12:00:01 | 121 秒，计坏；即使事务内 `succeeded_at` 写为 11:59:59，也不改变本口径 |

数据库 job 行仍裁决任务是否存在。只有当 watermark（事件时间完整水位）越过 `T`，即该时间之前的事件已收齐，并且到期 job 已逐一与数据库对账后，才发布窗口结果。接受确认缺失、无法重建期限时，窗口标为测量不完整并保持发布门禁；期限已确定，而完整水位之后仍缺成功确认的任务，在本确认 SLI 中计坏。不能把缺失遥测的任务静默删除，也不能用事后“现在已经成功”改写它当时是否按期确认。这套观测期限不修改任务的业务期限或租约合同。

##### 下载与通知：继续核验用户是否拿到了结果

本页确认完成 SLI 衡量是否按时观察到成功提交确认；下载另按通过身份与资源授权的请求定义结果读取 SLI，成功要求服务实际返回该引用对应的文件；未授权请求按安全策略单列。文件大小不同时要定义合适的时限/大小分组，不能直接套用元数据 `GET /api/reports/{id}` 的 400 ms。`report.ready` 尚待 relay（转发进程）发布不撤销已经提交的任务成功；若产品承诺通知送达，另定义通知投递 SLI。broker 确认或消费者 ACK 只属于消息交接边界。

##### 错误预算和发布门禁使用不同时间尺度

例如，30 天读取 SLO 设为 99.5%。若窗口内 10,000 个符合条件的读请求有 9,940 个在 400 ms 内返回预期结果，则 SLI 为 `9,940 ÷ 10,000 = 99.4%`。该窗口允许的坏请求数是 `(1 − 0.995) × 10,000 = 50`；实际 60 个坏请求，超预算 10 个。单位是该窗口里的请求数，不是百分比或毫秒。SLI 是测量结果，SLO 是内部目标；service level agreement（服务等级协议，SLA）是带对外承诺及可能后果的约定，不能仅把内部阈值改名为 SLA。请求加权汇总也不证明每个 region（区域）或用户群体验一致，必要时按稳定、低基数的区域维度查看。


30 天目标用于跟踪长期错误预算；金丝雀决策看分钟级发布窗口，不等到 30 天结束。保留一个简单示例门槛：按目标摘要、路由和区域分别统计，滚动 10 分钟至少有 100 个符合条件的读请求，若好事件比例低于 99% 并持续 5 分钟，则触发短期停止放量；本例把“持续 5 分钟”定义为每分钟评价一次，`t` 到 `t+5` 的六个评价点都满足样本数和比例条件；`98/100` 的单次观察只足以不增加流量，不能单独证明已满足持续止损条件，`99/100` 恰好达到比例门槛，仍须通过身份和内容检查。这些数值是本例的合成门槛，不是通用推荐。

不得把 `d-new` 的失败与稳定摘要合并后决定放量：例如目标 `d-new` 为 `98/100`、已知稳定摘要为 `900/900`，目标自身只有 98%，而汇总看起来却有 `998/1000 = 99.8%`。若无响应请求无法归入目标摘要，分母仍保留，但发布判断须保持而非把它算作健康目标样本。恢复也按相同口径查看变更后的实际摘要和新时间窗。

告警应附好/坏事件数、分母、窗口、摘要、路由/区域和指标/追踪查询链接，使值班人能检查门槛是否基于同一 SLI。长期 SLO 告警可按 burn rate（错误预算消耗率）使用长短窗口组合；Google Site Reliability Engineering（站点可靠性工程，SRE）Workbook 给出的是配置方法和起始示例，不应把其中某组比例直接套成所有服务的门槛。任务完成另按成熟 job 窗口计数，同时看未成熟 job 的最老年龄，避免“完成率尚未变坏”掩盖排队正在拉长。

#### 从聚合指标下钻到追踪与日志

metrics 把大量事件聚合成时间窗、计数、比率、分布或当前积压，回答影响何时出现、范围多大、是否集中在某个摘要或依赖。先用低基数的路由模板、响应类别、区域、服务角色、依赖名和受控版本标签定位 `d-new`；检查计数器分母、延迟分布/分位数、连接池等待、数据库饱和度、最老 outbox/job/broker 年龄、实际活跃物理槽、重试和容量失败；对适用的 broker 还看未确认消息数，以及按系统策略转入 dead-letter queue (死信队列) 的消息。租约到期只让恢复器有资格竞争，不表示它已提交写权栅栏（fence），也不表示旧 attempt 已停止；分别观察租约到期、恢复提交和被栅栏但仍占资源的 attempt。broker 队列浅不证明数据库 outbox 或 `queued` job 没有积压。

trace 把一次操作拆成有父子关系的 span（操作区间），回答该请求或任务在哪个阶段慢或失败。同步调用通过 context propagation（上下文传播）传递关联信息，使入口、授权、数据库和对象存储 span 可以串起。

异步导出在受理请求结束后，由 relay 根据已提交 outbox 中保留的 trace context 创建发布 span，并把它连到 broker 消息；worker 每次成功领取后创建独立 attempt span，通过消息创建上下文的 span link（跨度链接）关联回发布因果链，受控 `jobId` 则用于跨重试查询持久状态。不要让 HTTP span 挂起到整个任务完成；每次 attempt 的执行阶段应能单独定位。OpenTelemetry 消息语义默认用链接关联生产与消费；只有单条消息等约定情形才可考虑用消息创建上下文作 parent（父 span）。父子或并发 span 的持续时间可能重叠，不能把各 span 时长直接相加当总延迟。

logs 记录阶段发生的具体事件。把 trace ID、span ID 与受控的 `jobId`、`attempt`、状态转换、有限错误码放在结构化日志中，可以从代表性 span 回到实际错误；对照发布摘要和事件时间。指标把人带到受影响的窗口，trace 指出阶段，日志解释一次操作的结果。若 trace 有采样，查样本率、时间戳、导出健康度和覆盖范围；样本缺失不证明请求或故障不存在。

#### 用同一窗口解释两个症状

下面把这些信号合成一份可判定的事故记录，数字和日志均为教学构造，不是线上测量。12:10–12:20 同路由、同区域的目标摘要 `d-new` 窗口有 100 次合格读请求，合成数据假设逐次预期权限结果已知，其中 98 次在 400 ms 内符合该结果；这不是对真实服务逐响应正文判定能力的声称。同一窗口稳定摘要 `d-old` 为 900/900，合并后是 998/1000（99.8%），但分开看 `d-new` 仍低于门槛。门禁每分钟评价一次：12:15、12:16、12:17、12:18、12:19、12:20 六个相隔一分钟的点，各自的滚动 10 分钟目标摘要窗口都有至少 100 次请求，且好事件率都低于 99%，首末相隔完整 5 分钟，因此停止增加 `d-new` 流量。预先运行的合成核验还确认：有权的 `principal-P17` 读 `acct-17` 的报表 42 得到 `200` 和已知标记；无权的 `principal-PB` 得到符合本例策略的 `404`。目标摘要的正确率缺口不是把有效拒绝误算成成功造成的。

一条同窗口读取 trace 总耗时 900 ms。按阶段去重后的授权与报表读取墙钟时间是 720 ms，其中数据库连接池 checkout（从池中签出连接）等待 600 ms；这些阶段有包含关系，不能把 900、720、600 相加。查询 span 的 Structured Query Language（结构化查询语言，SQL）执行约 120 ms，剩余约 180 ms 在其他阶段。它把这条慢请求定位到取连接等待，却没有证明 `d-new` 是因果，也不能推出 worker 共用同一个池。

在同一 12:10–12:20 窗口于 12:16 按 `job-demo-731` 查权威 job 行、attempt 与 outbox：接受提交确认在 12:00，对应本确认 SLI 的 12:02 期限；12:16 查到状态仍是 `queued`、attempt=0，outbox 已发布且有 broker 唤醒记录，却没有成功领取、结果对象引用、`succeeded` 或 `report.ready`。权威状态在期限后仍未成功，完成用户结果显然已受影响；worker 的关联结构日志显示连接池获取失败发生在 claim 前，因此这项用户工作还未开始执行，最老待处理年龄本身不能给出这个阶段。它与读请求慢发生在同一故障窗口，但 API 与 worker 池分开配置，尚不足以证明二者同因。若数据库饱和度、池使用和查询时长对照仍缺，继续保留“共享数据库压力”的假设，不把相关性写成根因。

### 让遥测可诊断，但不泄露报表内容

指标标签应使用有限集合，例如规范化的 route template（路由模板）`/api/reports/{id}`、响应类别、区域、`service_role=api|worker`、依赖名和受控 release channel（发布通道）。标签的 cardinality（基数）要有界；每个标签组合都会成为独立 time series（时间序列）。不要把 `request_id`、trace ID、job ID、用户/tenant（租户）ID、原始 URL、报表标题、提示词、结果内容或任意错误文本作为指标维度。版本摘要适合短期发布比较，但需限制保留和组合数量，避免每次构建无限扩张时序。

trace 与日志可在有访问控制和保留期限的前提下包含用于关联的操作 ID；只记录必要字段。不得记录 access token（访问令牌）、cookie、授权 header（请求头）、报表正文或原始用户内容。优先用有界事件分类，如 `authorization=allow|deny`、`db_error=timeout|unavailable`、`job_state=queued|running|succeeded|failed|cancelled`、`error_code=capacity_exhausted|attempts_exhausted`。跨租户授权错误需要独立的安全审计和回归测试，不能靠指标里暴露 tenant ID 来排查。

### 按证据缓解并确认恢复

发布事故处置沿着“用户结果—SLI—依赖阶段—可逆动作—同一用户路径复验”推进。把操作和判据分开记录：

1. **确认用户影响与信号质量。** 固定事件起止、受影响接口、区域、API 与 worker 各自运行摘要，以及读请求 SLI 的分子/分母。检查遥测是否新鲜、采样和导出是否正常；请求无响应仍是坏事件，不能因为没有 span 而移出分母。
2. **核对任务处在哪个持久边界。** 对 `POST` 超时按 `(account_id, principal_id, report-demo-208)` 查询幂等记录，未知结果先标记为待裁决；受理事务一旦提交就计一个 accepted job，即使客户端没收到 `202`。相反，明确 `429`/`503` 依合同没有创建 job。分别观察 outbox 发布、broker 投递/确认、worker 领取、attempt、数据库终态和结果读取；ACK 只确认当前消息交接。已成熟的 `queued`/`running` 任务按完成 SLI 算坏，尚未成熟的任务暂不进分母但保留 pending-age 证据。
3. **用多条证据定位。** 按摘要和路由对照 canary 与基线窗口，选代表性的慢/失败 trace，再用 span 与 job/attempt 受控键查日志。交叉检查 API/worker 池等待、数据库连接数与查询耗时、最老 outbox/job 消息、对象存储错误码；不要把单条 trace、进程健康探针或 broker 队列深度当成根因。
4. **先降低影响，再选择安全路径。** 示例中 `d-new` 在 12:15 至 12:20 的六个每分钟评价点上，各自滚动 10 分钟分母均至少 100、好事件率均低于 99%，持续满 5 分钟，因此停止增加该摘要流量。假设发布记录已核实 `d-old` 满足当前安全不变量，就把新流量回到 `d-old`；若旧版本含相同跨租户漏洞，不能盲目回滚，应隔离受影响入口或前向修复。连接池等待尚未证明 API 和 worker 共用故障源，因此先比较各自连接预算与数据库活动，再按证据限流/降载，不要仅增大每个进程池。对未受理的新导出请求可按准入合同返回 `429`/`503`；已经接受的任务保持可查询、可恢复，不把拒绝伪装成 job 失败。
5. **以同一用户结果复验后再放量。** 示例在 12:20 将流量回到实际运行摘要 `d-old` 后，等待第一个完整的变更后滚动 10 分钟窗口于 12:30 结束，再用同一读 SLI 口径复验：该窗口 100/100 个合格请求为好事件，摘要归属完整。若样本不足或归因缺失就继续保持流量，不以切换前数据或跨摘要总量代替。业务核验另从已装配入口确认有权主体 `principal-P17` 读取 `acct-17` 的 `report 42` 得到 `200` 和已知标记，独立无权主体 `principal-PB` 得到本例约定的 `404`。

   `job-demo-731` 在 12:16 仍是 queued；流量回到 `d-old` 后，12:26 才观察到成功提交确认并按当前授权下载、核对文件。它在原期限之后才可观察为成功，且其晚完成不能归因给回退本身；这只证明旧任务后来可用。为验证新请求路径，再用新意图键 `report-demo-209` 创建 `job-demo-732`：12:31 确认受理提交并返回 `202`，12:32 观察到成功提交确认、结果引用与 `report.ready` outbox 已原子提交，然后从同一入口按授权下载并核对文件。该 60 秒确认间隔通过本页的确认 SLI；它不是物理 COMMIT 间隔的证明。旧任务后来恢复不替代这条新意图的受理、执行与下载复验。通知 outbox 是否送达按独立通知合同复验；队列 ACK 仍不代表用户拿到了文件。告警未持续满足 5 分钟可能只表示尚未触发/解除，不等于恢复；长期 30 天预算继续单独跟踪。
6. **记录可行动的事后改进。** 记用户影响时间窗、各 SLI 分子与分母、摘要和阶段证据、采取的缓解、确认安全的旧版本或前向修复、关联测试，以及为何现有门禁未更早发现。若只记“服务恢复”而无用户路径和窗口，无法判断是否真正止损。

若报表包含模型生成内容，HTTP 可用性和任务完成只衡量服务是否交付；内容质量需要独立评估与反馈，不应混成一个 SLI。用户主动评分的样本可能偏向更愿意反馈的人群，不能直接当成所有用户的质量分布。见[LLM 任务评估方法](../../ai-engineering/evaluation/llm-evaluation-methods.md)和[生产反馈信号](../../ai-engineering/systems/ai-production-observability-and-feedback.md)。

> [!info]- 来源与核对范围
> - OpenTelemetry 官方文档：[Signals](https://opentelemetry.io/docs/concepts/signals/)、[Traces](https://opentelemetry.io/docs/concepts/signals/traces/)、[Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/)、[Logs](https://opentelemetry.io/docs/concepts/signals/logs/)、[Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) 与[消息 span 语义](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/#consumer-spans)，核对于 2026-11-12：核对指标/追踪/日志各自模型、span 字段、异步操作的 span link（跨度链接）和跨服务上下文传播；当前消息语义以 link 关联生产与消费为默认，单消息等条件下才采用消息创建上下文作 parent。该语义页面标记版本 1.45.0；本例的采样与敏感字段约束是应用边界。
> - Prometheus 官方[指标与标签命名实践](https://prometheus.io/docs/practices/naming/)，核对于 2026-11-12：核对单位命名建议、标签组合形成时序及高基数标签风险；该页面是实践建议，不是所有遥测系统强制规范。
> - Google SRE Workbook：[Implementing SLOs](https://sre.google/workbook/implementing-slos/) 与 [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)，核对于 2026-11-12：核对用户结果型 SLI、错误预算、短长窗口与 burn rate（错误预算消耗率）告警方法。本文的 30 天、400 ms、99.5%、2 分钟、10 分钟/100 请求/99%/5 分钟均为合成教学数字，不是该书给所有服务的统一建议。
> - PostgreSQL 18 [日期/时间函数](https://www.postgresql.org/docs/current/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT) 与[事务提交信息函数](https://www.postgresql.org/docs/current/functions-info.html)，核对于 2026-11-12：核对 `now()`/`current_timestamp` 使用事务开始时间，而 `clock_timestamp()` 随墙钟变化；`pg_xact_commit_timestamp` 只在启用 `track_commit_timestamp` 后对启用后的事务有用，且信息会被 vacuum 清理。本文将提交确认间隔定义为服务观察 SLI；两次确认延迟可能不同，所以它相对物理提交间隔可双向偏差。
> - [RFC 9110 §15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3)，核对于 2026-11-12：通用 `202 Accepted` 不承诺后续操作最终成功；本文要求先提交 job、outbox 与等待槽是本例更具体的应用合同。
> - [怎样设计一个可持久查询的账户报表？](#15.%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E4%B8%80%E4%B8%AA%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F)、[如何估算并限制异步工作管线？](#28.%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) 与[发布确认与消费者 ACK](#16.%20%E6%8A%A5%E8%A1%A8%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E4%B8%8E%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)，核对到本例任务与队列合同：job/outbox/等待槽持久受理、`succeeded`/结果引用/`report.ready` 原子提交、租约与 attempt 归属。容量、租期与 broker 行为以对应章节合同为准。
## 37. 怎样根据输入约束和访问模式选择算法？

以合成的报表 42 为例：请求已从数据库得到 acct-17 的事件页，共 1,024 条，按 (occurred_at, event_id) 升序排列。接口要定位游标、显示分类树、缓存最近查看的页面，并按事件描述处理 Unicode（统一码）文本。这里完整展开游标定位；分类树、缓存和文本处理仅作情境，具体操作见后续链接。选算法前先写明输入保证、要执行的操作和结果约束；只有这样才能证明候选范围可以缩小，并估计成本。

本篇给出选型与复杂度模型。后续章节分别回答[数据结构怎样匹配访问方式](#38.%20%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%A6%82%E4%BD%95%E5%8C%B9%E9%85%8D%E8%AE%BF%E9%97%AE%E6%96%B9%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F)、[队列和栈怎样表示待处理工作](#39.%20%E9%98%9F%E5%88%97%E5%92%8C%E6%A0%88%E6%80%8E%E6%A0%B7%E8%A1%A8%E7%A4%BA%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%EF%BC%9F)、[LRU 如何维护按键查找与新近顺序](#40.%20%E6%9C%80%E8%BF%91%E6%9C%80%E5%B0%91%E4%BD%BF%E7%94%A8%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E6%8C%89%E9%94%AE%E6%9F%A5%E6%89%BE%E5%B9%B6%E6%9B%B4%E6%96%B0%E6%9C%80%E8%BF%91%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F)、[有序数据怎样缩小候选范围](#41.%20%E6%9C%89%E5%BA%8F%E6%95%B0%E6%8D%AE%E6%80%8E%E6%A0%B7%E8%AE%A9%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%E5%AE%89%E5%85%A8%E6%8E%92%E9%99%A4%E5%80%99%E9%80%89%EF%BC%9F)、[动态规划怎样定义状态和更新顺序](#45.%20%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92%E5%A6%82%E4%BD%95%E5%AE%9A%E4%B9%89%E7%8A%B6%E6%80%81%E5%B9%B6%E5%AE%89%E6%8E%92%E6%9B%B4%E6%96%B0%E9%A1%BA%E5%BA%8F%EF%BC%9F)、[分区如何改变排序成本](#46.%20%E5%88%86%E5%8C%BA%E5%A6%82%E4%BD%95%E6%94%B9%E5%8F%98%E5%BF%AB%E9%80%9F%E6%8E%92%E5%BA%8F%E7%9A%84%E6%97%B6%E9%97%B4%E5%92%8C%E7%A9%BA%E9%97%B4%E4%BB%A3%E4%BB%B7%EF%BC%9F)和[文本算法应选哪种字符单位](#47.%20%E6%96%87%E6%9C%AC%E7%AE%97%E6%B3%95%E5%BA%94%E6%8C%89%E7%A0%81%E5%85%83%E3%80%81%E7%A0%81%E7%82%B9%E8%BF%98%E6%98%AF%E5%AD%97%E7%B4%A0%E7%B0%87%E5%A4%84%E7%90%86%EF%BC%9F)。

### 先写明不变量，再选方法

事件页按复合键 (occurred_at, event_id) 排序，因此只有使用同一比较规则才能二分定位游标；这不意味着 event_id 单独有序。若排序规则、键字段或空值规则改变，数据顺序和比较器也要一起改变。若数据未排序，则不能直接二分；可扫描，或先排序并把预处理计入成本。

~~~mermaid
flowchart LR
    I[输入保证与规模] --> O[需要执行的操作]
    O --> P[候选方法能利用的输入保证、表示或已有信息]
    P --> C[时间、空间与分配成本]
    C --> V[用边界输入复算结果]
~~~

#### 同一条比较规则如何缩小区间？

为了看清每轮保留什么，下面把 1,024 条页数据缩成四条合成教学记录；沿用同一复合排序键和比较规则，并具体取 `(09:02, e08)` 作为下界查询。这里在已加载的有序页中找 `≥ target` 的插入位置，不是分页取下一页要求的严格 `> cursor`。例如已有游标 `(09:02,e03)` 时，`lower_bound` 返回 1（游标本身），而 `upper_bound` 返回 2（下一个更大键）。lower_bound 返回首个键不小于目标的下标；若所有键都小于目标，则返回 `n`。对升序数组，循环从 `lo=0, hi=n` 开始，并保持左侧 `[0,lo)` 的键都小于目标、右侧 `[hi,n)` 的键都不小于目标。`[lo, hi)` 是后续仍可能探测的元素下标范围，`[lo, hi]` 是可能的插入边界。若中点键小于目标，答案边界必须在 `mid` 右侧，令 `lo=mid+1`；若中点键不小于目标，`mid` 自己仍可能是答案，令 `hi=mid`，把它保留为右边界。直到 `lo=hi`，该边界就是结果。

![四条按复合游标排序的记录经过两次比较，lower_bound 返回插入位置 2](../../engineering-foundations/algorithms/resources/algorithms-and-complexity-search.svg)

第一次探测 index 2 的 `(09:02, e11)`；复合键排在目标之后，令 `hi=2`。下轮只探测元素下标 `[0, 2)`，但边界 2 仍可能是答案。第二次探测 index 1 的 `(09:02, e03)`；复合键排在目标之前，令 `lo=2`。元素探测范围变成空的 `[2, 2)`，唯一可能边界是 2。若只比时间戳，`e03`、`e08`、`e11` 在该比较器下都相等，便无法确定目标相对于这两条记录的精确位置。

例如，有序页中每次中点比较可以排除一半范围；动态规划复用相同子问题的结果；队列用头下标出队可免于搬移其余项。若缺少相应不变量，复杂度表中的数字便不适用。

### Big-O 表示增长，不是耗时承诺

Big-O notation（大 O 记号）描述输入规模增大时，所选成本单位的操作数或额外空间的渐近上界，省略常数因子和低阶项。这里 n 是元素数；示例默认键和数值能以常数时间比较或运算。若字符串长度、任意精度整数的位数或记录字段数随输入增长，就要把这些大小另列为参数。背包问题的 W 是数值容量，不是表示容量所需的位数。期望复杂度还依赖哈希分布等假设，需要明确标出。

| 增长量 | 典型例子 | 成立条件 |
|---|---|---|
| O(1) | 数组下标访问 | 下标已知且合法；按值查找不是常数时间 |
| O(1) 期望 | 哈希表查找 | 负载因子受控且哈希值充分分散；这是期望模型，不是所有实现的严格界 |
| O(log n) | 有序数组二分、平衡搜索树 | 数据有序或树高受不变量约束 |
| O(n) | 顺序扫描 | 每个元素检查常数次 |
| O(n log n) | 归并排序；划分大致均衡的快速排序 | 快速排序最坏可退化到 O(n²) |
| O(n²) | 两层全量扫描、平方级简单排序 | 两层循环均随 n 线性增长 |
| O(2ⁿ) | 朴素递归 Fibonacci 的上界、枚举子集 | 搜索树节点或候选数；按每个候选常数工作计 |
| O(n!) | 枚举所有排列 | 搜索树节点工作；每个节点做常数工作时成立 |

这些界只覆盖指定模型中的工作量。若枚举器还要复制并输出每个完整候选，输出成本要另算：从 n 个元素生成全部子集并复制为数组，元素总数为 n·2ⁿ⁻¹；输出所有 n 项排列则要写出 n·n! 个元素。连续数组扫描可能比指针跳转更快；哈希表扩容会让单次插入成本波动；数据库索引还涉及存储页读取。大 O 不替代测量，也不消除数据布局、内存局部性和运行时常数的影响，见[内存局部性如何改变实际成本](#48.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)。

> [!example] 1,024 条事件页上的查找
> 假设 1,024 条事件已经按复合游标键升序，且一次键比较按常数时间计。扫描到末尾要比较 1,024 次。lower_bound 在最坏路径每轮将待探测元素数减半，直到空：`1,024→512→256→128→64→32→16→8→4→2→1→0`，共有 11 次探测；例如找首个元素时，探测下标 `512,256,128,64,32,16,8,4,2,1,0`。另换成数值键和闭区间 `[low, high]` 的普通查找，若先判 `A[mid] === target`、再判 `A[mid] < target`，搜索最后一项也会探测 11 次：前 10 轮各做两次关系判断，末轮只做一次，共 21 次。复合键比较器内部还需另数比较了几个字段。若数据无序且只需判断是否存在某键，可线性扫描并返回匹配/未找到；无序数组没有有意义的 lower_bound 插入位置，需先按同一比较器排序、用有序结构查找，或返回排序副本，且要计入预处理成本。

### 怎样判断选型假设是否成立？

检查目标是定位还是排序、排序由谁建立且是否使用同一比较规则；是否存在可复用子问题、状态是否包含转移需要的信息；是否允许原地修改、复制、分配、扩容和递归栈是否进入内存预算；空输入、重复键、相同排序值、零容量、超大数和非 ASCII 文本是否改变结果。最后用边界输入复算返回值、副作用和复杂度条件。对本例的有序查找，排序保证失效时不能二分；精确查找可线性扫描，lower_bound 则须先按同一比较器排序并计入成本。其他算法应按各自不变量重新验证。

> [!info]- 来源
> - 二分查找只在输入已按同一键顺序排列时反复减半候选：[NIST Dictionary of Algorithms and Data Structures 的 binary search 条目](https://xlinux.nist.gov/dads/HTML/binarySearch.html)；复杂度分析的规模模型见 [MIT 6.006 Lecture 3: Sorting](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/6d1ae5278d02bbecb5c4428928b24194_MIT6_006S20_lec3.pdf)。四项下界图与 1,024 项探测数按区间更新手算复核；子集和排列输出量由各候选长度求和。
## 38. 数据结构如何匹配访问方式，复杂度界何时成立？

案例背景：以一份合成事件报表为例，报表 42 要按下标显示事件页、按 event_id 找记录、按时间顺序遍历；分类视图需要层级结构，运行时也可能保存工作树。选择数据结构时，应看目标如何被找到、链接如何更新、是否需要排序，以及树高或哈希分布等前提是否成立。实际速度还会受连续存储和指针跳转影响。

### 数组、链表和树各自适合什么操作？

| 结构 | 访问或查找 | 插入、删除 | 条件与代价 |
|---|---|---|---|
| 数组 | 已知下标 O(1)；按查询值扫描 O(n)，按该查询键排序后可二分 O(log n) | 中间改动 O(n)，后续元素要移动 | 连续访问方便；增长时可能分配和复制 |
| 单链表 | 按值或下标找节点 O(n) | 已知前驱链接时 O(1)，否则先找前驱 | 删除节点需要前驱 |
| 双向链表 | 查找通常需外部索引；裸链表 O(n) | 已知节点时 O(1) 改邻接链接 | 每个节点多存前后引用 |
| 高度平衡搜索树 | 搜索 O(log n) | 插入、删除 O(log n) | 需要不变量限制树高 |
| 未平衡搜索树 | 最坏 O(n) | 最坏 O(n) | 递增插入可形成长链 |
| Trie 前缀树 | 长度 m 的键约 O(m) | 沿字符路径增删 | 子边选择成本需受控；可能占较多内存 |

**同一批事件在数组、单链表和平衡搜索树中的布局与查找路径：**

![同一批事件在数组、单链表和平衡搜索树中的布局，以及各自走到 e18 的路径](../../engineering-foundations/algorithms/resources/core-data-structures-representation-choice.svg)

这组四条合成事件沿用本章报表页，按 `(occurred_at, event_id)` 排序。知道下标时，数组直接读槽位；按时间遍历可顺扫这份有序数组；按完整排序键精确查找或找边界可二分。只知道 `event_id` 时不能在这份时间加 ID 的排序上二分，可另建 ID 哈希索引，但它不提供时间顺序。沿单链表按值找 e18 要经过三个 next；搜索树也按同一复合键比较，查找 e18 需要完整目标键 `(09:05, e18)`，图示形状中先比较 e11，再走到右孩子。若数据频繁插入或删除，需比较数组搬移与树更新的维护成本。图只展示一个具体树形布局：树操作一般按树高 h 计，只有维持平衡的不变量才能保证 h=O(log n)。

链表只有在已知所需节点/链接时才是 O(1) 更新；先扫描定位会让整体操作成为 O(n)。树的 O(log n) 需要高度界。连续数组扫描通常比指针追逐更有局部性，硬件成本见[内存局部性如何影响访问](#48.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)。

### 树的遍历顺序和搜索条件是什么？

二叉树深度优先遍历有三种访问时机：中序为左、节点、右。若 binary search tree（BST，二叉搜索树）的次序不变量保证左子树所有键不大于当前键、右子树所有键不小于当前键，中序输出非降序；若实现还规定相等键只能放某一侧，非降序结果本身不能证明这条重复键规则成立。例如根 2、左子 2、右子 3 的中序仍为 2、2、3，但违反“相等键只能放右侧”的约定。前序先节点，适合配合结构信息序列化；后序先子节点，适合先计算或释放子树。下面迭代中序返回第 k 小值；要求节点值为有限数字、比较规则一致且树满足 BST 次序（含其重复值规则）。重复值按节点分别计数；若实现把同值压在一个节点的计数器里，选择第 k 项时也要计入该计数。k 非正、非整数或节点不足时返回 null。本算法至多弹出 k 个节点；结束时栈中至多还留 h 个祖先，所以 push 次数至多 k+h、pop 次数至多 k，总时间 O(h+k)，最坏 O(n)；栈空间 O(h)，h 是树高；平衡树 h=O(log n)，退化时 h=O(n)。

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

> [!example] 栈怎样找出中序第 k 项？
> 为看清序号，暂换成一棵 4 节点合成数值树：根 3，左子 1（其右子为 2），右子 4；取 `k=3`。算法先 push 3、1，pop 1 后剩 `k=2`；转到 1 的右子，push 并 pop 2 后剩 `k=1`；再 pop 3 时返回 3。中序次序为 1、2、3、4，因此第三项确为 3。

red-black tree（红黑树）给二叉搜索树节点着色，要求红节点的孩子为黑、从任一节点到后代叶哨兵的黑节点数相同，并依实现把根和哨兵视为黑色。这些约束给出树高 O(log n)，所以基于树高的搜索、插入、删除在最坏情况下为 O(log n)。Java SE 25 的 TreeMap API 明确说明它基于红黑树，并保证 containsKey、get、put、remove 为 O(log n)；键按自然顺序或构造时给定的 Comparator 排序，Comparator 若与 equals 不一致会破坏 Map 接口的通用约定。C++ std::map 按 Compare 的严格弱序维护唯一键；标准对操作分别规定 find 和不带提示的单项 insert 为 O(log n)，按已知位置 erase(iterator) 摊还 O(1)，erase(first,last) 为 O(log n + k)，k 是被删元素数；标准不规定底层树形。这里的树界按一次键比较为常数计；字符串或复合键比较若随字段长度增长，还要乘上比较器成本。不能从一种实现推断另一种产品。

B-tree（B 树）每个节点容纳多个键，以降低存储页读取次数；其内部节点也可以保存记录或记录引用。B+ tree（B+ 树）内部节点只用于导航，叶节点保存完整记录或指向记录的条目，叶页通常相连以支持范围扫描；具体数据库索引布局由产品文档决定。trie（前缀树）共享键前缀，适合前缀查询；m 是键的被遍历表示单元数（如字节或代码单元），若每个单元的子边能以常数期望时间选出，查找约 O(m)，否则还要加上各节点的子边查找成本。子边表示也会改变总内存。

### 哈希表为什么有碰撞，何时能快速查找？

#### Java SE 25 HashMap 契约与 OpenJDK 25u 实现边界

哈希表根据键的哈希值选桶，再在桶内处理冲突。不同键可落入同一桶；扩容按新容量重分桶，能拆开一部分碰撞，但不能保证不再碰撞。以 OpenJDK 25u HashMap 的扩散后哈希 `h` 为例，容量 16 时 `h=1` 与 `h=17` 都落在桶 1，容量 32 时分别落在桶 1 和 17；扩容也无法拆开扩散后哈希完全相同的键。Java 中 equals 相等的键必须有相同 hashCode；若键入表后改变参与 hashCode/equals 的字段，后续查询可能找不到原条目。哈希表适合精确键查找，不保证按键排序。

Java SE 25（LTS）HashMap 允许一个 null 键和多个 null 值，不保证迭代顺序，也不负责并发安全。合理散列下 get/put 有常数时间期望；哈希分布很差时碰撞会增加成本。键的 hashCode/equals 若随变长内容增长，也要计入访问成本。默认初始容量为 16、负载因子为 0.75；超过阈值后表会扩容。扩容时要重分桶，单次 put 可能花 Θ(n)，把一系列插入的扩容成本摊开后才是均摊常数；散列冲突仍另算。

旧档案使用的 Java SE 17 HashMap API 也规定默认初始容量 16、负载因子 0.75，并具有上述 null、顺序和并发边界。这些公共契约在这里与 Java SE 25 共用解释。负载因子较高通常减少表的空间开销，但会增加碰撞与查找成本；较低则用更多桶空间换取较少碰撞。选择时还应考虑条目数量和迭代成本：HashMap 迭代要经过桶容量与实际条目，过大的预留容量也有代价。

OpenJDK 25u 维护分支在桶索引前用 h ^ (h >>> 16) 扩散哈希高位，并定义 TREEIFY_THRESHOLD=8、MIN_TREEIFY_CAPACITY=64。对普通 putVal 的链表桶追加路径，8 个既有碰撞节点后追加第 9 个：若表容量已是 64，该次 put 将桶树化；若初始容量为 16，且这些键的扩散后哈希值完全相同，第 9、10 个碰撞项分别触发扩容到 32、64，第 11 个才树化。仅在旧表中同桶的不同哈希值可能在扩容时分到不同桶，不能沿用这个极端例的计数。这个计数只描述该源码路径，不能外推到 compute/merge 或任意树桶查询的严格 O(log n) 界。旧档案原解释针对 OpenJDK 17；17u 维护分支在 2026-11-11 对照了同一组哈希扰动和相关阈值。桶细节是源码实现，不是 Java Map 接口保证；键的可比较性可帮助处理哈希值相同的树桶项，差的哈希分布仍会影响总体成本。

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

对固定树且 `visit` 每次为 O(1) 时，访问 n 个节点的遍历工作为 O(n)。递归 DFS 的调用栈为 O(h)，h 是树高；每个活动递归帧还会保留该节点的 `childNodes` 数组快照，树高之外的快照元素合计最坏 O(n)，例如根节点有 n−1 个孩子。显式 DFS 栈或 BFS 队列最坏 O(n) 空间。若回调改树，应按实际访问的节点数和回调成本另算。每个节点在调用 `visit` 后立即把自己的 `childNodes` 转成数组快照；回调对该节点的修改会影响随后快照，遍历不是整棵树在开始时的一致快照。BFS 用递增 head 下标；反复对普通密集数组调用 `shift` 会移动后续索引，若每次还需搬移剩余项，总工作可达 O(n²)。实现见[队列和栈如何表示待处理工作](#39.%20%E9%98%9F%E5%88%97%E5%92%8C%E6%A0%88%E6%80%8E%E6%A0%B7%E8%A1%A8%E7%A4%BA%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

扁平分类行可两趟转成树：第一趟用 Map 按唯一 ID 建浅拷贝节点，第二趟按 parentId 把节点引用接到父节点的 children 数组。每个父节点的 children 按输入行出现顺序追加，因此保留各自子项的相对输入顺序；这不会保留不同父节点之间原先交错的行顺序。输入约定为普通数据记录（字段是数据属性，不依赖 getter 或 Proxy 自定义访问），ID 是互不重复的正安全整数且不能使用根标记 0、一个根的 parentId=0、其他行的父 ID 都存在；然后从根遍历检查不可达环。

节点复制时显式写回 `id` 与 `parentId`，所以即使这两个数据属性不可枚举，节点索引和父子连接仍保留所需字段。其他预期随节点复制的业务字段（如 `name`）应是自有可枚举属性，或由实现显式复制。若采用平均常数时间的哈希 Map/Set 操作模型，节点索引、链接和可达性检查预期 O(n)；ECMAScript 2026 对 Map/Set 只要求平均访问次线性，并未承诺 O(1)。对象展开按 ECMAScript 的 CopyDataProperties 先枚举自有键、再检查每个属性描述符，只复制可枚举属性。设 Q 为所有行的自有键总数（含不可枚举），P 为其中自有可枚举属性总数，浅拷贝扫描时间为 O(Q)，实际复制输出的属性空间为 O(P)；每行显式保留 `id`、`parentId`、`children` 等固定字段和数组另需 O(n)，所以总时间为 O(n+Q)，输出空间为 O(n+P)。属性值没有递归深拷贝；若字段或值的复制成本随内容长度增长，还须另计字节数。

**两行分类记录先建立 `id` 索引，再按 `parentId` 接成一棵树：**

![两行分类记录经过 Map 浅拷贝和父节点索引，接成一棵树](../../engineering-foundations/algorithms/resources/core-data-structures-array-to-tree.svg)

~~~javascript
function arrayToTree(rows) {
  if (!Array.isArray(rows)) throw new TypeError('rows must be an array');
  const nodes = new Map();
  for (const row of rows) {
    if (!row || !Number.isSafeInteger(row.id) || row.id <= 0 || nodes.has(row.id)) {
      throw new RangeError('rows must have unique positive safe-integer IDs');
    }
    nodes.set(row.id, { ...row, id: row.id, parentId: row.parentId, children: [] });
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
> 输入故意先放子行：`[{id:2,parentId:1,name:"收入"},{id:1,parentId:0,name:"根"}]`。第一趟 `Map` 先建 node 2，再建 node 1；第二趟读到子行时，虽然根行尚未出现在输入位置，`Map.get(1)` 已找到根节点，于是把 node 2 引用接到根的 `children`。根遍历访问 1、2，`seen` 与 Map 都有两项，因此数据可达且合法。`treeToArray` 按树的前序输出 `[{id:1,parentId:0,name:"根"},{id:2,parentId:1,name:"收入"}]`。

treeToArray 按前序输出父节点后再输出各子树；它不恢复任意扁平输入原先跨父节点交错的行顺序。回转假设输入为 ID 正安全整数、单根无环树，根 ID 标记 0 只用于 parentId；示例只输出 id、parentId、name；其他业务字段需显式复制。根标记不是 0 时应替换为实际协议。

### React Fiber 内部为什么把树节点链接起来？

React Fiber 节点用 child、sibling、return 等链接表达父子关系和同级顺序，使协调器能按工作单元保存进度。树仍是树，只是同级孩子通过 sibling 串联。transition 等并发特性允许某些渲染工作暂停、重启或让位；不能据此说每个 render 和 DOM commit 都可任意中断。DOM 变更在准备好的 commit 阶段应用。Fiber 布局是实现细节，应用应依赖 React 公共 API。

> [!info]- 来源
> - Java SE 17 的公共契约、默认容量/负载因子及空间与访问成本取舍：[HashMap API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/HashMap.html)（2026-11-13 核对）。
> - HashMap 契约、默认值与期望复杂度：[Java SE 25 HashMap API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/HashMap.html)，Java SE 25。
> - 哈希扰动与树化机制：[OpenJDK 17u HashMap 源码](https://github.com/openjdk/jdk17u/blob/master/src/java.base/share/classes/java/util/HashMap.java)（2026-11-11 对照）、[OpenJDK 25u HashMap 源码](https://github.com/openjdk/jdk25u/blob/master/src/java.base/share/classes/java/util/HashMap.java)（2026-11-11 核对）；比较 hash、TREEIFY_THRESHOLD、MIN_TREEIFY_CAPACITY 与 putVal，作为实现样本。
> - JavaScript Map/Set 的复杂度边界：[ECMAScript 2026 §24.1、§24.2](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)，只要求平均访问次线性；本文 O(1) 是常见哈希实现的分析模型，不是规范保证。对象展开的 [CopyDataProperties §7.3.25](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-copydataproperties) 先枚举全部自有键并检查描述符，再复制可枚举属性，不递归复制属性值。
> - 有序容器契约：[Java SE 25 TreeMap API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/TreeMap.html) 的 red-black tree、键序和 containsKey/get/put/remove 成本；[C++ associative container requirements §23.2.7](https://eel.is/c++draft/associative.reqmts) 的 find/insert、erase(iterator) 与 erase(first,last) 复杂度要求。
> - DOM 子节点快照：[WHATWG DOM Standard](https://dom.spec.whatwg.org/#old-style-collections-nodelist) 的 live `NodeList` 与 `childNodes`；[`Array.from`](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.from) 将当下迭代结果放入新数组。
> - React 阶段与并发：[Render and Commit](https://react.dev/learn/render-and-commit) 说明提交到 DOM 的阶段；[React 18](https://react.dev/blog/2022/03/29/react-v18) 说明并发渲染仅在使用并发特性时启用，2022-03-29；Fiber 内部字段见[React Fiber 类型](https://github.com/react/react/blob/main/packages/react-reconciler/src/ReactInternalTypes.js)，2026-11-11 核对。
> - B+ 树索引结构：[Database System Concepts 第 7 版 Chapter 14](https://db-book.com/slides-dir/PDF-dir/ch14.pdf)，14.20–14.22；内部节点作导航，叶节点保存索引/记录指针并按键顺序链接。具体数据库布局由产品文档决定。
## 39. 队列和栈怎样表示待处理工作？

案例背景：报表 42 的通知消费者要按到达顺序处理事件，例如先处理 e07，再处理 e03；扫描 `f(a, g(b))` 时，遇到左括号便把它的位置及所属调用标记压入栈，遇到右括号便弹出最近仍未匹配的标记。前者是 first-in, first-out (FIFO，先进先出) 队列，后者是 last-in, first-out (LIFO，后进先出) 栈。选好顺序后，还要让空状态和可存储值之间没有歧义。

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

**链表队列以 `head` 指向最早项、`tail` 指向最新项；图中跟踪报表 42 的 e07、e03 两条通知入队和出队。**

![两个通知入队后依次出队；head 和 tail 在删除最后一项时都清空](../../engineering-foundations/algorithms/resources/queue-and-stack-representations-linked-queue.svg)

链表队列的 `enqueue`、`dequeue` 和 `peek` 都只访问或更新固定数量的字段，按此成本模型单次为 O(1)；这个界不计节点分配和垃圾回收的实际耗时。每项需一个节点及其 `next` 引用；`head`、`tail` 和 `length` 共用 O(1) 个队列级元数据。

容量有上限时，环形缓冲区可用长度为 `capacity` 的固定数组 `items` 循环复用槽位。`capacity` 是正整数，`head` 是 `[0, capacity)` 内的整数下标，`size` 是 `[0, capacity]` 内的整数。从 `head` 开始，环绕数组读取 `size` 个槽，依次组成 FIFO 队列：第 `j` 项位于 `items[(head + j) % capacity]`，其中 `0 ≤ j < size`。`tail` 是 `(head + size) % capacity`；只有 `size < capacity` 时它才指向空槽，满队时会与 head 重合，但该槽仍存着队列项。

`dequeue` 只在 `size > 0` 时读取并清空 head 槽，再令 `head = (head + 1) % capacity`、`size--`；空队时拒绝出队。`enqueue` 只在 `size < capacity` 时写入 tail 槽并令 `size++`；本文采用固定容量，满队时拒绝入队。固定容量下，入队和出队都只做常数次槽访问与字段更新，均为 O(1)。若另选扩容策略，触发扩容的那次还要复制槽位；几何倍增时单次成本可为 O(capacity)，连续入队的扩容成本摊还 O(1)。

具体状态沿用报表 42 的 e07、e03、e11：起初三个事件待处理，`capacity=4、head=0、size=3、tail=3`；出队 e07 后变为 `(head,size,tail)=(1,2,3)`；收到 e18 并写入槽 3 后变为 `(1,3,0)`；再将合成事件 e21 写入绕回的槽 0 后，队列为 e03、e11、e18、e21，状态为 `(1,4,1)`。满时 head 与 tail 相同但 `size=4`；再依序读完四项后，`head=tail=1、size=0`，因此 `size` 区分空与满。

![容量为 4 的环形队列先出队 e07，再将 e18、合成事件 e21 写入槽 3 和绕回后的槽 0；队满时 head 与 tail 都指向槽 1](../../engineering-foundations/algorithms/resources/queue-and-stack-representations-ring-buffer.svg)

图中出队后清空槽位以释放对象引用；队列的有效项由 head 与 size 界定，不靠空槽值判空。

一次性的 BFS 扫描可用数组与递增 head 下标。长期 FIFO 若只增加 head，会保留已消费的对象引用并让底层数组持续增长；可清空已消费槽并定期压缩，或用环形缓冲区复用空间。对起初有 n 项、中途没有入队、连续出队直到队列为空的普通密集数组，ECMAScript 2026 的 `shift` 抽象步骤逐个检查并写回后续下标；若成本模型把每次写回计为一次搬移，总写回量为 `(n−1)+…+1 = Θ(n²)`。这描述规范步骤的抽象计数，不表示引擎一定执行同样数量的物理复制或耗时。

用 head 而不是槽值表示空状态时，队列可以安全保存 `null` 和 `undefined`。假设 `head` 是 `[0, items.length]` 内的整数，且有效队列项恰是后缀 `[head, items.length)`。先读槽，再把已消费槽设为 `undefined` 以释放其中对象的引用，最后让 head 前进；判断空队列要看 `head === items.length`，不能看槽值。赋值为 `undefined` 不会删除数组下标，只表示该位置已不在队列的有效区间内。

按一次槽读取、一次槽赋值和一次 head 更新计，图中的 dequeue 是 O(1)。

~~~javascript
function dequeue(items, state) {
  if (state.head === items.length) throw new RangeError('queue is empty');
  const value = items[state.head];
  items[state.head] = undefined; // 释放对象引用；下标仍存在，不作为空队列信号
  state.head++;
  return value;
}
~~~

**边界输入 `[null, undefined]` 展示：`head` 从 0 推到 1、再到长度 2；第二个存储值即使是 `undefined` 仍可出队。**

![head 从 index 0 推到 1、再推到长度 2；第二个存储值即使是 undefined 仍可出队](../../engineering-foundations/algorithms/resources/queue-and-stack-representations-head-index-queue.svg)

此代码只展示出队步骤，队列从 `[null, undefined]` 开始时 state.head 为 0；真实实现还需定义入队、压缩或固定容量。长期数组若频繁复用，压缩时要把 `[head, items.length)` 搬到开头并重置 head，一次需搬移 O(items.length - head) 个项；环形缓冲区则用取模循环利用有限槽位。

旧数值队列以 `null` 作为空队列的返回哨兵。若运行时允许入队 `null`，只看 `poll()` 的返回值无法区分该值与空队列；这个类提供 `size`，调用者可在 `poll()` 前检查 `size`，据此区分。运行时入队的 `undefined` 会原样返回，与 `null` 哨兵不同。静态类型 `number` 是否排除 nullish 值取决于 TypeScript 的 `strictNullChecks`：启用时才会排除。若 API 需要每次都从返回结果本身判断是否取到值，可改用带状态的结果或空时抛错。其受限实现保留如下。

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

数组末尾 push/pop 表达栈的入栈和出栈；显式空检查可避免把已存的 undefined 当作空栈。这里每个栈项保存左括号的位置及其所属调用标记。遇到右括号而栈已空，或扫描结束后栈仍有未配对的左括号，都表示括号不匹配。

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

**对表达式 `f(a, g(b))`，按字符位置跟踪两个左括号及调用标记入栈，右括号按后进先出配对。图中 `␠` 表示下标 4 处的空格。**

![在 f(a, g(b)) 中，两个左括号依次 push，两个右括号按最近未完成项依次 pop](../../engineering-foundations/algorithms/resources/queue-and-stack-representations-nested-expression-stack.svg)

在几何扩容的动态数组模型下，`push` 扩容复制会让单次插入成本升高，但把复制量摊到一系列插入后为 O(1)；末尾 `pop` 不移动其余项。运行时回收和具体收缩策略另计。未知输入深度的递归还受运行时栈大小限制，可改用显式栈。

> [!info]- 来源
> - 数组末端和首端操作的规范行为：[ECMAScript 2026 indexed collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)，§23.1.3.22–23、§23.1.3.27（Array.prototype.pop/push/shift）；shift 对普通密集数组逐个处理后续下标。标准描述可观察步骤，不规定引擎执行相同数量的物理搬移。
> - 空值类型边界：[TypeScript `strictNullChecks` 配置说明](https://www.typescriptlang.org/tsconfig/strictNullChecks.html)：关闭时忽略 `null` / `undefined`，开启后将它们作为独立类型检查。
## 40. 最近最少使用缓存怎样按键查找并更新最近使用顺序？

案例背景：用一份合成报表界面说明 Least Recently Used (LRU) cache（最近最少使用缓存）。容量为 2；A 表示账户 acct-17 的 report/42 游标页，B 表示同一账户的 report/41 页面，C 表示账户首页。先 `put(A)`、`put(B)` 放满缓存，再重新查看 A 并打开 C；结果应保留 A、C，淘汰最久未使用的 B。实际缓存受权限和查询条件影响时，键还须隔离账户/授权范围、过滤器和游标；命中缓存不能代替本次授权检查。

### 用 Map 插入顺序表示新近程度

Map 的迭代顺序是插入顺序。此实现把它当作从最旧到最新的队列：命中时先删键再重设，使它移到最新端；只调用 `set` 更新已有键不会改变其位置。对此实现，命中 `get` 和容量大于 0 时的 `put` 都算一次使用并更新顺序；未命中的 `get` 不改顺序，`has` 只查是否存在、不会刷新最近使用时间。构造参数须为非负整数，容量 0 时 `put` 不保留数据。若缓存最多容纳 c 项，存储空间随 c 线性增长为 O(c)。

实现接受任意 Map 键和值。`has` 能区分已存入 `undefined` 和键缺失；基本值按 SameValueZero 比较（例如 `NaN` 与自身匹配，`+0` 与 `-0` 是同一键），对象键按对象身份比较，所以内容相同但新建的数组仍是另一个键。

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
> `put(A, 页面42)`、`put(B, 页面41)` 后，A 最旧、B 最新。`get(A)` 命中后顺序变成 B、A；`has(B)` 返回 true，但不改变顺序。`put(C, 首页)` 淘汰 B，留下 A、C。对已有键调用 `put` 会更新值并把该键移到最新端。
>
> | 操作 | 最旧 → 最新 | 返回或淘汰 |
> |---|---|---|
> | put(A) | A | — |
> | put(B) | A, B | — |
> | get(A) | B, A | 页面 42 |
> | has(B) | B, A | true，顺序不变 |
> | put(C) | A, C | 淘汰 B |

ECMAScript 要求 Map 的平均键访问时间为元素数量的次线性，但不承诺精确 O(1)。新键的 `put` 分支还读取 `.size`；规范的 getter 按语义列表统计未删除项，没有给出 O(1) 复杂度保证，而引擎可以另外维护计数。

这些保证也不能推出 `keys().next()` 取得最旧键有 O(1) 上界。规范描述迭代时按插入顺序前进并跳过已删除项；在数组式表示里，反复删后重插可能留下许多待跳过的位置，但规范也明确说明这种列表只是可观察语义模型、不是要求引擎采用的内部表示。因此只用 Map 的版本顺序正确且代码短，却不能仅凭 Map 键访问要求证明满容量淘汰操作 O(1)；`.size` 与迭代器的实际代价由引擎实现决定。

### 用双向链表加 Map 显式维护索引与顺序

Map 把键映射到链表节点；双向链表用 `prev`/`next` 保持新近顺序，`tail.prev` 直接定位待淘汰项。每次操作结束后，两种结构保持以下关系。非空时，`head.next` 指向最近使用的节点，`tail.prev` 指向最久未使用的节点；空链时 `head.next === tail` 且 `tail.prev === head`。每个真实节点恰好在链上一次，Map 中的键恰好指向相应节点。`head` 和 `tail` 是不进入 Map 的哨兵，因此插入头部和删除节点都不用分支处理空链或真实边界。此实现沿用上一节的调用约定：命中 `get` 或容量非零时的 `put` 刷新顺序；`has` 和未命中 `get` 不刷新，`has` 也能区分值为 `undefined` 与缺失。

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

按同一组 A/B/C 操作看节点链接和 Map 索引。图中每行都是操作完成后的状态，从 `head` 向右按最近到最久排列，与上一节表格的最旧到最新方向相反；`has(B)` 不改变状态，所以不另画一行。Map 单独映射键到这些节点。橙色标出本次命中的 A，绿色标出新插入的 C；节点文字和箭头仍直接给出前后关系。

![容量为 2 的 LRU 双向链表随 get(A) 和 put(C) 改变的三种状态](../../engineering-foundations/algorithms/resources/practical-data-structure-implementations-lru-linked-order.svg)

`get(A)` 先由 Map 找到 A。`_remove(A)` 将 A 的前驱 B 与后继 `tail` 接起来；随后 `_addToFront(A)` 把 A 插到哨兵 `head` 后。中间摘链期间 A 自己的 `prev`/`next` 暂时仍保存旧指针，紧接着的插入步骤会覆盖它们。此后 B 成为 `tail.prev`。满容量执行 `put(C)` 时，`tail.prev` 直接给出 B；摘除 B 后还要从 Map 删除 B，再创建 C、登记其节点并插入表头。

已知节点时，链表摘除或移到 head 只改固定数目的链接；从 `tail.prev` 取最旧项也是固定访问，所以这些链表步骤确定为 O(1)。在通常的可扩容哈希 Map 模型中，键查找、插入和删除的成本按期望均摊 O(1) 估算，读取 `.size` 按 O(1) 估算；基于这些假设，完整缓存 `get`/`put` 的成本是期望均摊 O(1)，其中写入扩容的重排成本也计入均摊分析。ECMAScript 对键访问的最低保证只是平均次线性，并未规定 `.size` 的复杂度。双链表版每条缓存项多一个节点和两条链接，连同 Map 共用空间 O(capacity)；节点分配与垃圾回收（GC）时间不在这个抽象操作计数内。

| 只用 Map | Map + 双向链表 |
|---|---|
| **刷新命中项 A：** 删除再重设；查找/更新由 Map 实现 | **刷新命中项 A：** Map 定位节点，再做固定次数的指针改写 |
| **满容量加入 C：** 先读 `.size`，再用 `keys().next()` 取最旧键；两者都没有规范 O(1) 界 | **满容量加入 C：** 先读 `.size` 判断是否已满；满时 `tail.prev` 即最旧节点，再删除 Map 项并把新节点插到头部 |
| 状态少、代码短；不能从标准推出淘汰 O(1) | 多一组指针和节点分配；在哈希 Map 插删查找期望均摊 O(1)、`.size` 读取 O(1) 的模型下，完整操作期望均摊 O(1) |

> [!example]- 可选：不使用 Map/Record 的数字键练习变体
> 这是一个受限练习：有效缓存值不能是 -1，因为 `get` 用 -1 表示未命中，而代码本身不拒绝写入 -1。实现用 `Object.create(null)` 建无原型索引，以数字键查节点；命中移到头部，满容量插入时淘汰尾节点。空表时 `head` 和 `tail` 都是 null；有一个节点时两者指向同一节点。键和值沿用 `number` 契约，不限于有限整数；对象索引把数字键转成属性名，所以 +0/-0 共用 `"0"`，NaN 共用 `"NaN"`，正负无穷分别成为属性名。文本 ID `9007199254740992` 与 `9007199254740993` 转成 Number 后都会舍入为 `9007199254740992`，不能再作为不同数字键区分。容量须为非负整数；对象属性访问的复杂度由引擎决定，ECMAScript 不保证精确 O(1)。
>
> 容量为 2 时沿用相同策略，`get(1)` 后 1 成为最近项，下一次加入 3 淘汰 2：
>
> | 操作 | head → tail（最近 → 最久） | 返回或淘汰 |
> |---|---|---|
> | `put(1, 10)` | 1 | — |
> | `put(2, 20)` | 2 → 1 | — |
> | `get(1)` | 1 → 2 | 10 |
> | `put(3, 30)` | 3 → 1 | 淘汰 2 |
> | `get(2)` | 3 → 1 | -1，未命中 |
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
> - Map 使用 SameValueZero 区分键；Map 迭代按插入顺序；已存在键的 `set` 原位更新，删除后重设会追加；实现须提供平均次线性键访问。规范的 `.size` 语义按列表统计，且其逐项列表是可观察语义模型，并非引擎实现要求：[ECMAScript 2026, §§24.1、24.1.3.3、24.1.3.11–24.1.3.12、24.1.5.1](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - 无 Map 变体以数字作对象索引时按 ToPropertyKey 转换；Number 安全整数之外的不同整数可能得到同一 Number 值：[ECMAScript 2026, §7.1.19 `ToPropertyKey`](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-topropertykey)、[§21.1.2.6 `Number.MAX_SAFE_INTEGER`](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)。
> - 容量 2 的状态和链表指针更新按本页代码复算。Node.js v26.13.0 运行了两种 JavaScript 实现；数字键练习以 TypeScript 5.7.2 严格模式编译并运行。上述结果只验证这些输入下的代码行为。
## 41. 有序数据怎样让二分查找和双指针安全排除候选？

案例背景：报表 42 已取回一页按 (occurred_at, event_id) 升序排列的事件。需要在页内定位记录、找出分页边界，并在其他已排序数组上找两数之和。本页用同一排序规则追踪每轮能排除什么；排序、比较器和返回结果约束必须一致。最后的零值压缩例子不依赖排序，它使用读写下标不变量。

### 二分查找如何缩小有序区间？

精确查找要求输入已按比较器定义的升序排列，目标也在同一键域里；比较器每次对同一对值给出相同符号，且这些比较结果能传递地定义顺序。下面的闭区间版本返回任意一个相等项的下标；空数组或找不到目标时返回 -1。若有重复项，命中不保证是第一个。

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

先用便于手算的数字输入 `[3, 7, 11, 15, 19, 23, 27]` 查找 19；对本例有限数值，可传入比较器 `(a, b) => a - b`，其符号表示数值顺序。循环不变量是：若目标存在，它仍在当前闭区间 `[left, right]` 中。

| 轮次 | 当前闭区间 | 中点下标和值 | 比较后的动作 |
|---|---|---|---|
| 1 | `[0,6]` | `3 → 15` | `15 < 19`，排除下标 0–3，令 `left=4` |
| 2 | `[4,6]` | `5 → 23` | `23 > 19`，排除下标 5–6，令 `right=4` |
| 3 | `[4,4]` | `4 → 19` | 命中并返回下标 4 |

若查找 20，前两次更新相同；第三次比较下标 4 的 19，令 `left=5`，闭区间 `[5,4]` 变空，返回 -1。若目标不在数组中，闭区间最终会变空。键序一致性还解释复杂度：中点小于目标时，从 `left` 到 `middle` 都更小；中点大于目标时，从 `middle` 到 `right` 都更大。一次比较因此舍弃至少一半候选，剩余候选每轮至多为原来的一半，最多比较 O(log n) 次键，额外空间 O(1)。中点写作 `left + floor((right-left)/2)`，在固定宽度整数语言中可避免先算 `left+right` 溢出；JavaScript 数组长度本身远低于 Number 的精确整数上限，但差值写法便于移植。若输入无序或比较器不匹配排序规则，不能按此方式排除。

**回到报表 42：复合键要逐字段比较。** 排序键先比较 `occurred_at`，时间相等时再比较 `event_id`。示例把时间存为统一 UTC、相同固定精度的 ISO 8601 字符串，因此字符串顺序与时间顺序一致；ID 用两位数字的固定宽度 `eNN` 字符串，因此字典序与示例编号顺序一致。生产比较器还须与数据库的字段类型、空值顺序和排序规则相同。

~~~javascript
function compareEvent(a, b) {
  if (a.occurred_at < b.occurred_at) return -1;
  if (a.occurred_at > b.occurred_at) return 1;
  if (a.event_id < b.event_id) return -1;
  if (a.event_id > b.event_id) return 1;
  return 0;
}
~~~

同一时刻时 ID 决定顺序；但时间优先于 ID。以下复用完整合成页：e07 在 09:00，e03、e11 在 09:02，e18 在 09:05。e03 的 ID 小于 e07，但时间更晚，所以仍排在 e07 后面。只按 `event_id` 搜索这份按时间和 ID 复合键排序的数组，并不满足二分所需的升序条件。

| 排序行 | `occurred_at` | `event_id` | 与游标 `(09:00, e07)` 的关系 |
|---|---|---|---|
| e07 | 09:00 | e07 | 相等 |
| e03 | 09:02 | e03 | 更大；时间更晚，即使 ID 字典序更小 |
| e11 | 09:02 | e11 | 更大；时间晚于游标。两条 09:02 记录中，e11 排在 e03 后 |
| e18 | 09:05 | e18 | 更大；时间更晚 |

`compareEvent` 可以用于精确查找，也可以求边界；生产用值应是完整时间戳，表格中的时分为简写。用于分页时，完整排序键 `(occurred_at, event_id)` 必须能区分每条记录；若仍有完整键相同的记录，才需增加一个同样用于排序和分页、能区分这些记录的 tie-breaker（平局裁决键）。

~~~javascript
const events = [
  { occurred_at: '2026-11-12T09:00:00.000Z', event_id: 'e07' },
  { occurred_at: '2026-11-12T09:02:00.000Z', event_id: 'e03' },
  { occurred_at: '2026-11-12T09:02:00.000Z', event_id: 'e11' },
  { occurred_at: '2026-11-12T09:05:00.000Z', event_id: 'e18' }
];

console.log(binarySearch(events, events[1], compareEvent)); // 1：精确找到 e03
~~~

**找边界时，元素范围与答案边界不是同一个区间。** 对已加载页的升序数组，`lower_bound` 返回首个键 `>= target` 的下标；所有键都小于目标时返回 `n`。设可能继续探测的元素下标为半开区间 `[lo, hi)`，可能的答案边界则在闭区间 `[lo, hi]`。初值 `lo=0, hi=n`，不变量是 `lo` 左侧的键都 `< target`，`hi` 起的键都 `>= target`。若中点小于目标，令 `lo=mid+1`；否则 `mid` 仍可能是答案，令 `hi=mid`。

~~~javascript
function bound(values, target, compare, afterEquals = false) {
  let lo = 0;
  let hi = values.length;
  while (lo < hi) {
    const mid = lo + Math.floor((hi - lo) / 2);
    const order = compare(values[mid], target);
    if (order < 0 || (afterEquals && order === 0)) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

const target = { occurred_at: '2026-11-12T09:02:00.000Z', event_id: 'e08' };

console.log(bound(events, target, compareEvent)); // 2：首个 >= target
console.log(bound(events, events[1], compareEvent)); // 1：首个 >= (09:02,e03)
console.log(bound(events, events[1], compareEvent, true)); // 2：首个 > (09:02,e03)
~~~

查询键为 `(09:02,e08)`，两条同时间记录之间没有相等项。下表逐轮记录元素范围与边界候选：

| 当前状态 | 元素探测范围 | 候选边界 | 中点 | 比较与更新 |
|---|---|---|---:|---|
| 第 1 轮 | `[0,4)` | `[0,4]` | 2，`(09:02,e11)` | 大于目标，令 `hi=2`；下标 2 不再探测，但边界 2 保留 |
| 第 2 轮 | `[0,2)` | `[0,2]` | 1，`(09:02,e03)` | 小于目标，令 `lo=2` |
| 结束 | `[2,2)` | `[2,2]` | — | 探测范围为空，唯一边界为 2，首个符合项是 `(09:02,e11)` |

若要找第一条与目标相等的记录，先用 `lower_bound` 求 `pos`，再检查 `pos < n && compare(values[pos], target) === 0`；否则 `pos` 可能指向第一个更大项或等于数组长度 `n`，不能当作命中。分页读取下一页通常要求严格 `> cursor`，应找首个严格大于目标的边界，即 `upper_bound`。本代码将 `afterEquals` 设为 `true`，让相等项也被跳过；此时不变量改为 `lo` 左侧的键都 `<= target`、`hi` 起的键都 `> target`，循环结束时返回当前已加载数组中第一条严格大于游标的记录位置；若没有更大键则返回 `n`。已加载页的边界不是数据库下一页查询本身；查询仍需用相同查询范围、排序规则及严格游标条件继续取数。已有游标 `(09:02,e03)` 时，`lower_bound` 返回 1（游标自身），`upper_bound` 返回 2（当前页中下一条）。即使游标行已删除，只要继续使用同一完整排序键，严格边界仍可定位第一条更大的记录。两条记录若排序键完全相同，游标落在两者之间时严格 `>` 会跳过后一条，因此用于分页的键必须唯一或增加 tie-breaker。

两个边界版本都从 `[0,n)` 开始，每轮剩余的待探测项数至多为原来的一半，因此最多做 O(log n) 次键比较、使用 O(1) 额外空间。本例键字段是固定长度，故一次比较按 O(1) 计；若键长度随输入增长，应另计比较成本。无序数组没有由当前顺序定义的 lower/upper bound；若只查记录是否存在，可以线性扫描并返回匹配项或未找到。若要找有序边界，须先按同一比较器排序或换用满足该顺序不变量的数据结构，并计入建立有序表示的成本。

### 双指针何时能替代重复扫描？

双指针不是一般嵌套循环的替代品。下面的两数之和依赖数组升序；零值压缩则不要求排序，它按读写位置推进。两种做法都要给出每个指针能前进的理由。

#### 有序数组两数之和

输入需按数值升序排列。为让这段 JavaScript `Number` 代码中的整数比较精确，本例把值、`target` 及每次计算的两端和都限在安全整数范围内；若业务数据超出该范围，应使用精确数值类型并匹配其比较器。若两端和小于 `target`，固定左端时它已经与剩余最大项相加，和仍不足，所以当前左端不可能参与答案；若两端和大于 `target`，固定右端时它已与剩余最小项相加，和仍过大，所以当前右端不可能参与答案。按本轮证明排除一端后，另一端无需回头。

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

本例输入 `[1, 2, 4, 7, 11]`，`target=9`；函数返回一对下标或 `null`，值和目标是可精确比较的小整数。下标必须不同，`left < right` 正是这一结果约束：

| 步骤 | `left` 与值 | `right` 与值 | 和 | 排除理由或结果 |
|---|---|---|---:|---|
| 1 | `0:1` | `4:11` | 12 | `12 > 9`；右端 11 与其余任一左值配对也会过大，`right=3` |
| 2 | `0:1` | `3:7` | 8 | `8 < 9`；左端 1 与其余任一右值配对也不足，`left=1` |
| 3 | `1:2` | `3:7` | 9 | 命中，返回下标 `[1,3]` |

循环不变量是：所有尚未排除的解都只能由当前 `left` 到 `right` 之间的两个不同下标组成。表中的每次移动都证明被删去的一端不可能再参与解；指针相遇或交错时，候选集合为空。每轮至少移动一个端点，因此总扫描 O(n) 时间、O(1) 额外空间。重复数值也可由不同下标组成解，例如 `[2,2]` 求 4；若目标不存在，循环结束后返回 `null`。数组未排序时，上述极值论证不成立，不能照搬这两个移动方向。例如未排序的 `[3,1,2]` 对目标 3 有下标 `[1,2]` 这一解，但这段代码会先将右指针左移两次并返回 `null`。若必须先排序，移动结果下标属于排序后的数组；需要原数组下标时还须保留位置映射并计入排序成本。

#### 把零移到末尾并保留其他次序

这项双指针操作不靠排序。循环开始处理下标 `i` 时，`[0,next)` 保存已扫描的非零值且顺序与原输入相同，`[next,i)` 全是零，`[i,n)` 尚未扫描。若当前值是零，`next` 不动；若当前值是非零值且 `next<i`，`[next,i)` 已全为零，交换把该非零值写入 `next`，并把原来 `next` 处的零移到 `i`；若 `next===i`，数组已在正确位置，代码的自交换不改变它。处理完当前值并推进 `i` 后，相同不变量重新成立。

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

以 `[0,1,0,3,12]` 为例。每步处理前，`next` 都是下一个非零值的落点；扫描结束后剩余后缀全是零：

| 处理下标 `i` | 处理前 `next` | 操作 | 处理后的数组 | 新 `next` |
|---:|---:|---|---|---:|
| 0 | 0 | 值为 0，跳过 | `[0,1,0,3,12]` | 0 |
| 1 | 0 | 交换下标 0 与 1 | `[1,0,0,3,12]` | 1 |
| 2 | 1 | 值为 0，跳过 | `[1,0,0,3,12]` | 1 |
| 3 | 1 | 交换下标 1 与 3 | `[1,3,0,0,12]` | 2 |
| 4 | 2 | 交换下标 2 与 4 | `[1,3,12,0,0]` | 3 |

函数返回同一个数组，时间 O(n)、额外空间 O(1)。它适用于稠密数组，并把严格等于 0 的项（包括 -0）移到末尾，其他项保持扫描时的相对次序。若要把 null、空字符串或其他值也当作零，需改写判定条件；若输入含空槽，迭代会读到缺失值并把它当作非零值移动，需先定义所需语义。

> [!info]- 来源
> - 二分在升序数组中比较中点并缩小区间：[NIST Dictionary of Algorithms and Data Structures, “binary search”](https://xlinux.nist.gov/dads/HTML/binarySearch.html)。本页闭区间精确查找和半开边界查找按所列不变量分别推导。
> - 双指针只在端点单向移动且每步排除成立时为线性扫描：[Antti Laaksonen, *Competitive Programmer’s Handbook*, “Two pointers method”](https://cses.fi/book/book.pdf)。两数之和的排除证明与零值压缩状态按本页例子复算。
> - 时间字符串字典序与时间顺序一致的条件：[RFC 3339 §5.1 “Ordering”](https://www.rfc-editor.org/rfc/rfc3339.html#section-5.1)：时区、Z/偏移写法和小数位数需相同。
## 42. 怎样在边界前进时维护一个有效窗口或活动区间？

案例背景：一份合成报表按到达时间记录事件。一个问题要找连续 k 条事件中净变化最大的窗口，另一个问题要找出处理耗时累计达到阈值时最短的连续事件段；资源预约表则要找同一时刻最多有多少任务占用资源。前两项是 fixed-size sliding window（固定宽度滑动窗口）和 variable-size sliding window（变长滑动窗口），第三项要用扫描线。三者都维护随边界变化的状态，但输入次序、状态不变量和移动理由各不相同。

本章统一用 [start, end) 表示半开区间：成员下标满足 start ≤ i < end，长度为 end - start；start = end 时窗口为空。相邻的 [a, b) 与 [b, c) 没有共同元素，位置 b 不属于前窗、只属于后窗。

### 固定宽度窗口：移出一项，再加入一项

假设按到达顺序记录每个事件对待处理任务数的净变化，完成任务可为负数。稠密一维数组 [4, -2, 3, 5] 的下标和值依次为 0:4、1:-2、2:3、3:5；求连续 3 条事件的最大净变化。第一段 [0, 3) 的和是 4 - 2 + 3 = 5。代码里的循环变量 `right` 是本轮新加入项的下标；加入下标 3 后，窗口的排他右界是 `right+1=4`，新段为 [1, 4)。只需移出下标 0 的 4、加入下标 3 的 5，得到 -2 + 3 + 5 = 6。

| 窗口 | 对应下标和值 | 本轮变化 | 和 |
|---|---|---|---:|
| [0, 3) | 0:4、1:-2、2:3 | 4 - 2 + 3 | 5 |
| [1, 4) | 1:-2、2:3、3:5 | 旧和 5 − 移出 4 + 加入 5 | 6 |

首窗 [0, k) 的和给 `best` 初值。其后每轮代码变量 `right` 是本轮新加入项的下标；更新并比较时，`sum` 恰好等于窗口 [right-k+1, right+1) 中所有值的和，`best` 是已经比较过的完整窗口最大和。固定宽度意味着每次右边界多含一项、左边界少含一项，所以只需增量更新这两项；不要求数据非负。代码要求 values 是稠密数组、每项和 k 都是 JavaScript 安全整数、k > 0；每次加减后窗口和也必须仍是安全整数，否则抛出 RangeError。若 n < k（包括空输入），没有完整窗口，返回 null。输入校验与窗口扫描各至多遍历 n 项，合计 O(n) 时间；除输入外只保留几个数值状态，额外空间 O(1)。这里按到达顺序计算；为了套用有序数组的双指针套路而先排序，会改变连续事件的含义。

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

若业务值为小数，需改用相应的数值精度约定；这段代码刻意不把浮点误差当成精确净变化。

### 变长窗口：只在扩展和收缩都可证明时使用

另一项报表指标是：按事件顺序找到处理耗时总和至少达到 5 毫秒的最短连续区间。输入是稠密数组 [2, 1, 3, 2]，所有耗时均为非负安全整数，target = 5 是正安全整数。代码变量 `right` 表示本轮要加入项的下标，不是排他边界：加入 `values[right]` 后，当前窗口是 [left, right+1)。每轮先加该项；达标时记录候选，再逐项移出 `left`，直到窗口不再达标。

| 操作后的状态 | 当前窗口 [left, right+1) | 和 | 决定 |
|---|---|---:|---|
| 加入下标 0 | [0, 1) | 2 | 未达 5，继续扩展 |
| 加入下标 1 | [0, 2) | 3 | 未达 5，继续扩展 |
| 加入下标 2 | [0, 3) | 6 | 达标，记录长度 3；移除下标 0 |
| 移除下标 0 | [1, 3) | 4 | 低于 5，结束本轮收缩，继续扩展 |
| 加入下标 3 | [1, 4) | 6 | 达标，比较候选长度 3；与现有 best 同长，保留先前值；移除下标 1 |
| 移除下标 1 | [2, 4) | 5 | 仍达标，记录长度 2；移除下标 2 |
| 移除下标 2 | [3, 4) | 2 | 低于 5，结束收缩 |

扫描结束，最短区间是 [2, 4)，即下标 2、3 的耗时 3 和 2；函数返回 `{ start: 2, end: 4, length: 2 }`，边界采用半开区间。状态是当前区间总和和目前最短候选。对每个 right，达标后逐步增加 left，依次检查仍可达标的更短后缀；因为值非负，某次移除使和低于阈值后，再移除只会保持或降低和，不可能得到有效后缀。若 left 已在更早轮越过某个起点，当时对应的达标区间已经比较过；之后以同一起点延长只会更长，因此不会漏掉全局最短解。left、right 都只向前；每项至多进入和离开一次，加上输入校验总计 O(n) 时间、O(1) 额外空间。若从未达标，返回 null；同长候选保留先发现的那个。

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

非负约束是这段代码正确性的前提，不是对输入的清洗偏好。代码要求 values 为稠密数组，项和 target 均为安全整数，target > 0，且每一步的 sum 仍在安全整数范围内。若绕过入口的非负检查，把相同移动规则照搬到输入 [1, -1, 5]、阈值 5 上，算法先得到整段 [0, 3) 的和 5，记录长度 3；移除 1 后和变成 4，于是停止收缩并返回长度 3。但 [2, 3) 只含 5，长度为 1。负数让扩展可以降低总和、移除左项也可以提高总和；原来的移动理由失效，不能照搬这个窗口算法。

### sweep line（扫描线）：先排序端点，再维护活动集合大小

预约区间是另一类输入：它们不按开始时间排列，需先把端点排序。对同一批合成任务，预约为 A=[1,4)、B=[2,4)、C=[4,6)；下面传给函数的次序故意为 C、A、B。区间采用半开约定，任务在开始时刻已占用资源，结束时刻则已释放；另一个任务可在该结束时刻开始而不与它重叠。

扫描线按时刻由小到大处理端点。在同一时刻，先结束 [a,t) 的任务，再开始 [t,b) 的任务；代码把同刻端点合成一组，先扣除结束数，再加开始数。`active` 只保存活动任务数，因为问题只问并发峰值；需要列出具体任务时才需保留任务身份。处理完时刻 t 的整组端点后，`active` 等于该时刻（开始端计入、结束端不计）及其右侧直到下一端点之间的任务数。该例的状态变化为：

![A、B、C 三个半开预约区间在时间轴上的位置，以及各端点间的活动任务数。](../../engineering-foundations/algorithms/resources/range-scans-and-active-sets-timeline.svg)

| 时刻 | 结束 | 开始 | 处理后活动数 | 峰值 |
|---:|---|---|---:|---:|
| 1 | — | A | 1 | 1 |
| 2 | — | B | 2 | 2 |
| 4 | A、B | C | 1 | 2 |
| 6 | C | — | 0 | 2 |

峰值是 2。若逐个处理时刻 4 的端点，并在每项处理后更新 peak，先加入 C 会把临时 active 计为 3，错误抬高答案；代码先统计该时刻的 starts、ends，整组扣除结束数并加入开始数，再更新 peak，因此组内暂态不会计入峰值。为使 `events[i].time === time` 合并同一时刻，传入端点需使用同一个规范化 Number 值；若由不同浮点计算得到的近似值代表同一业务时刻，应先归一为统一刻度再扫描。

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

  events.sort((a, b) => a.time - b.time);
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
  { name: 'C', start: 4, end: 6 },
  { name: 'A', start: 1, end: 4 },
  { name: 'B', start: 2, end: 4 }
])); // 2
console.log(maxConcurrentHalfOpen([])); // 0
~~~

输入必须是数组；每项需有有限数值 start、end 且满足 start < end，空区间会被拒绝。事件生成及分组各为 O(n)，事件表占 O(n) 空间。若使用最坏 O(n log n) 的比较排序（例如归并排序或堆排序）处理 2n 个端点，总时间为 O(n log n)。ECMAScript 规定 `Array.prototype.sort` 的排序行为与比较器契约，但比较调用的具体序列由实现决定，不承诺这一渐近复杂度；这里的界是采用上述排序算法时的成本模型，不是 JavaScript API 保证。扫描线与保留到达顺序的窗口都维护局部状态，但前者先重排端点，后者不能改变原序列；两者的正确性分别来自半开端点分组规则和窗口的移动不变量。

> [!info]- 来源
> - 固定/变长窗口的双指针推进、每个元素有限次进入和离开：[Antti Laaksonen, Competitive Programmer’s Handbook, 2018 draft, §8.1 “Two pointers method” 与 §8.3 “Sliding window minimum”](https://cses.fi/book.pdf)。本页的求和窗口根据各自输入前提推导；带负值的失效例子由本页代码状态复算。
> - 端点排序后维护活动集合的扫描线思路：[Robert Sedgewick 与 Kevin Wayne，Algorithms, 4th ed. 配套网站，“Geometric Intersections”](https://algs4.cs.princeton.edu/93intersection/)，并参看作者实现 [IntervalIntersection.java](https://algs4.cs.princeton.edu/93intersection/IntervalIntersection.java.html)。该例讨论端点事件与活动区间；本页据此按半开预约区间分组事件，并只统计活动数量。
> - `Array.prototype.sort` 的稳定排序要求、比较器以及实现定义的比较调用序列：[ECMA-262, 2023, §§23.1.3.30–23.1.3.30.1](https://tc39.es/ecma262/2023/multipage/indexed-collections.html#sec-array.prototype.sort)。ECMA-262 未给本方法规定 O(n log n) 时间界；本页只在比较排序成本模型下给出该复杂度。
## 43. 怎样在不断加入任务时持续取出最高优先级？

案例背景：合成报表 42 的调度器不断收到待处理任务；每当有执行资源空出来，就取当前最紧急的一项。若每次都重新排序整个集合，就会重复整理旧任务。priority queue（优先队列）只要求快速插入和取出当前最高优先级项；binary heap（二叉堆）用一条父子顺序约束支持这两项操作。

### 堆序只规定父子关系，不会把数组排好序

以下用最大堆，数值较大的优先级代表任务更紧急；相同优先级按先到先出。入堆时附上从 0 开始递增的 `sequence`，只有优先级相同时才比较它，较小序号先出。把完全二叉树（最后一层从左向右填充）按层从左到右放入数组，使用 0 起始下标时，只有 `i > 0` 的位置才有父节点，父节点下标是 `floor((i - 1) / 2)`，子节点是 `2i + 1` 与 `2i + 2`。在比较关系可传递时，堆序要求任一父项不低于它的孩子；根沿路径传递下来，便不低于任何节点。除根以外，兄弟节点之间没有整体次序，数组也不是排序结果。

任务 A 和 B 的优先级均为 5，A 先到；C 的优先级为 8。插入 C 后的树形与数组层序表示如下。箭头只表示父子堆序，不表示数组整体排名。

![插入 C 后最大堆的树节点、数组下标和层序数组对应](../../engineering-foundations/algorithms/resources/heaps-and-priority-queues-array-tree.svg)

| 操作 | 堆数组（按层序） | 发生的修复 |
|---|---|---|
| 插入 A(5) | [A(5)] | 根无需调整 |
| 插入 B(5) | [A(5), B(5)] | 同优先级时 A 序号较早，不交换 |
| 插入 C(8) | [C(8), B(5), A(5)] | C 从下标 2 上浮到根 |
| 插入 D(2) | [C(8), B(5), A(5), D(2)] | D 低于父项 B，留在数组末尾 |
| 取出 | [A(5), B(5), D(2)] | 返回 C；D 补到根后，B、A 都优于 D；两者同分，较早的右孩子 A 优先，与 D 交换 |

插入先放数组末尾，再只沿父节点上浮；删除根时先用末项填根，再比较左右孩子，和优先级更高的孩子交换后继续下沉，直到当前项不低于两个孩子，或已到叶子。例子中 B 与 A 同为 5，`sequence` 较小的 A 胜出，所以 D 先与右孩子 A 交换。每次修复只走一条根到叶路径，不扫描整堆。

堆有 `n` 个节点时，最大高度 `H = floor(log₂ n)`。因此上浮或下沉至多走 O(log n) 层：以元素比较和交换次数计，push、pop 各为 O(log n)，peek 只读根是 O(1)，堆项占 O(n) 个槽位。

如果所有元素一开始都已知，可以从最后一个非叶节点向根逐个下沉来建堆，整体 heapify 为 O(n) 次比较/交换；若元素逐个到达，则逐项 push，累计为 O(n log n)。heapify 仍为线性，是因为大多数节点靠近叶子，只能下沉少数几层；可继续下沉至少 h 层的节点数，随 h 每增加 1 至多约减半。设完全树的最大高度 `H = floor(log₂ n)`；高度为 `h` 的节点至多有 `ceil(n / 2^(h+1))` 个，每个最多下沉 `h` 层，因此有限范围 `1 ≤ h ≤ H` 的工作量上界为 `Σ h·ceil(n / 2^(h+1)) = O(n)`。自底向上建堆要求能同时访问整批初始元素。

> [!info]- 实现成本口径
> 上述堆操作复杂度把单次优先级比较视为 O(1)，计的是元素比较和交换。一次 `items.push` 若触发动态数组扩容，可能额外复制 O(n) 个槽位；在常见几何扩容模型下，扩容成本摊还为每次追加 O(1)。稳定队列用 BigInt `sequence` 作次级键：若序号有 `b` 位，比较或递增最多需 O(b) 位操作；累计 `m` 次入队时，序号位数随 `log m` 增长。这里的 O(n) 空间计堆槽位，不计 BigInt 字段的位数。

普通堆若只比较优先级 `priority`，并不保证并列项稳定；稳定行为来自代码中的 `sequence` 次级键。此实现用 BigInt 序号，优先级必须是有限 JavaScript Number；进入队列的优先级与序号保持不变。非空 `peek()`/`pop()` 返回含 `priority`、`sequence`、`value` 的冻结记录；空堆的两者都返回 `null`。任务包装在对象中，所以任务 `value` 本身即使是 `null`，也不与空队列哨兵混淆。

`BinaryHeap(higher)` 要求 `higher` 是函数，否则抛 `TypeError`；它还必须形成严格弱序：没有元素高于自身，优先关系可传递；若两项互不高于对方，就把它们视为同一优先级档，而且“同档”关系也可传递。堆项留在堆中期间，比较结果也必须保持一致；若可变字段改变了项的相对顺序，就要重建或重新调整堆。否则父子堆序不一定能让根代表全体最高项。`toArray()` 返回内部堆数组的浅拷贝，仍按堆布局排列，不是排序结果；Top K 会再对这份拷贝排序。

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
> tasks.push(2, 'D');
> console.log(tasks.pop().value); // C
> console.log(tasks.pop().value); // A
> console.log(tasks.pop().value); // B
> console.log(tasks.pop().value); // D
> console.log(tasks.pop());       // null
> ~~~

若元素已知且要完整排序，直接排序可能更简单；堆的优势出现在不断插入、只需当前极值，或只保留少量 Top K 的时候。

### 只保留 Top K 时，根节点代表淘汰线

这里切换到另一组合成输入：一次收到一批带分数的候选，只返回最高的 K 项。维护最多 K 项的最小堆，根就是当前保留集合里最差的一项；同分时较晚到达者更差。堆未满 K 项时直接插入候选；堆满后，仅当候选分数严格高于根时才删除根并插入候选。与根同分的后来候选也应丢弃，因为根比新候选更早到达。下方代码复用前面折叠示例中的 `BinaryHeap`。依次读入 A(8)、B(5)、C(5)、D(7)、E(1)，K=3：

`topK` 接收 `values` 数组、非负安全整数 `k`，并要求每项都有有限数值 `score`；先校验整批输入，再开始筛选。返回值按分数降序排列，同分按输入先后。

返回数组沿用 `values` 中的原对象引用，筛选和最终排序不会改写输入数组。

| 已读分数 | 保留集合 | 根（当前淘汰线） | 动作 |
|---|---|---|---|
| A(8) | A(8) | A(8) | 堆未满 3 项，直接插入 |
| A(8)、B(5) | A(8)、B(5) | B(5) | 堆未满 3 项，直接插入 |
| A(8)、B(5)、C(5) | A(8)、B(5)、C(5) | C(5) | 插入后堆已满；同分时较晚的 C 是淘汰线 |
| 再读 D(7) | A(8)、D(7)、B(5) | B(5) | D 高于根，替换同分中较晚的 C |
| 再读 E(1) | 不变 | B(5) | E 不高于根，丢弃 |

令 `k' = min(K, n)`。K 为正且 n 非零时，代码先花 O(n) 校验输入，再扫描 n 项；堆满后，每个候选至多触发一次 O(log(k' + 1)) 的堆调整，所以扫描最多做 O(n log(k' + 1)) 次堆比较。最后只排序保留的 `k'` 项，按比较排序模型另需 O(k' log(k' + 1)) 次比较；分数并列时由 `sequence` 明确排序，因此不依赖内置排序的稳定性。ECMAScript 不保证内置 `sort` 的具体比较次数。堆、中间副本和返回数组共占 O(k') 额外空间；调用方传入的 `values` 不计入。K=1 时扫描为 O(n)，K>n 时保留并返回全部 n 项，再按分数与输入先后排序。K=0 仍先校验全部 n 项，再返回空数组，耗时 O(n)；n=0 时返回空数组。

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

若所有项都已到达且最终要完整排序，排序一次通常更直接（见[分区如何改变快速排序的时间和空间代价](#46.%20%E5%88%86%E5%8C%BA%E5%A6%82%E4%BD%95%E6%94%B9%E5%8F%98%E5%BF%AB%E9%80%9F%E6%8E%92%E5%BA%8F%E7%9A%84%E6%97%B6%E9%97%B4%E5%92%8C%E7%A9%BA%E9%97%B4%E4%BB%A3%E4%BB%B7%EF%BC%9F)）；若 n 很大而 K 很小，同一 Top K 更新规则可在输入逐项到达时只保留 O(K) 个候选。本页代码接收的是数组，所以其 O(K) 是算法额外堆空间，不包括调用方已持有的 O(n) 输入。优先队列可用于任务调度；固定大小堆适合筛选少量最高分候选，二者共享堆操作，但取舍目标不同。

> [!info]- 来源
> - 完全二叉树数组表示、上浮/下沉、插入/删除极值、线性 bottom-up heapify：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §2.4 “Priority Queues”](https://algs4.cs.princeton.edu/24pq/)。该章按比较次数说明堆界，并说明动态数组扩容的界是摊还界。本页以 0 起始数组实现同一堆序；操作结果由 Node.js 运行复算。
> - 并列键稳定处理的作者实现样本：[Algorithms, 4th ed., §2.5 “Sorting Applications” 的 StableMinPQ.java](https://algs4.cs.princeton.edu/25applications/StableMinPQ.java.html)。本页显式把到达序号作为次级比较键，稳定性因此属于本页 API 合约。
> - `Array.prototype.sort` 的稳定比较规则及由运行时决定的比较调用序列：[ECMAScript 2026, §23.1.3.30](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)。本页 Top K 的最终排序复杂度按比较排序模型计，不把某个引擎的具体算法写成语言保证。
## 44. 搜索状态图时，何时永久标记节点，何时必须回退？

以一张合成路网为例：站点 S 要把包裹送到 Z。路网是有向图：S 可到 A、B；A 与 B 都可到两路会合的 T；T 可回到 S，也可到 Z。回边让图有环，共享的会合节点让两条路线合流。我们先用它找一条最少跳数路线，再枚举简单路线；随后把部分边改作依赖，检查依赖环；最后给路段加入非负代价。

在 BFS 与 Dijkstra 的路网查询中，站点 ID 足以代表到达状态，前提是当前站点确定可走边及各边代价，且与先前路径无关。若钥匙、剩余预算等到达信息会改变后续转移，就要把这些条件并入状态键；否则仅按站点去重会合并实际上不同的状态。简单路径枚举另用 `onPath` 记录本分支到过的站点，因为它的合法性确实取决于这段历史。

无权图用 `Map<顶点 ID, 邻居数组>` 表示；ID 是字符串，每个顶点都作为键出现（没有出边时用空数组），邻居也必须是图中的键。邻居数组按给定顺序扫描；简单路径示例按顶点序列输出，所以数组中不放重复邻居。BFS 用 `null` 表示起点没有父节点，因此顶点 ID 不使用 `null`。

~~~mermaid
flowchart LR
    S --> A
    S --> B
    A --> T
    B --> T
    T --> S
    T --> Z
~~~

下文复杂度按图已用邻接表建好、不含建图成本计算；采用常见哈希字典模型，把一次 `Map`/`Set` 查询或更新、一次堆比较/交换视作平均 O(1)，并按固定成本处理这些短顶点 ID。这是分析模型；ECMAScript 规范只要求 `Map`/`Set` 平均访问时间次线性，并未保证 O(1)。若键很长或字典操作成本显著，须另计键处理时间。

这些操作都沿边扩展候选状态，但保留的状态不同：breadth-first search（BFS，广度优先搜索）在顶点首次入队时记录父节点，因队列按边数分层，之后可全局去重；枚举简单路径时，同一顶点可能属于不同合法路线，必须只在当前递归路径内标记并在返回时撤销；拓扑排序维护尚未满足的依赖数，要求图无环；Dijkstra 先保留暂定距离，只在当前最小距离项出堆时定型顶点，旧堆项可能过期，且边权必须非负。

### 无权图最短路：顶点第一次入队时记录父节点

breadth-first search（广度优先搜索，BFS）用先进先出队列按层扩展：先看距 S 一条边的顶点，再看两条边的顶点。队列中的顶点按发现距离非递减排列，所以第一次发现一个顶点时，已找到它的最少边数路径。用 parent 同时记录“已经发现”与首次父节点，之后的回边或另一条同层路线不再入队。

| 处理的顶点 | 刚发现的邻居 | 队列（从前到后） | parent 新增 |
|---|---|---|---|
| S | A、B | A、B | A←S，B←S |
| A | T | B、T | T←A |
| B | T 已发现 | T | 无 |
| T | S 已发现、Z | Z | Z←T |
| Z | 已到目标 | 空 | — |

按首次父节点从 Z 回溯得到 S→A→T→Z，共 3 条边。若邻接表把 B 放在 A 前，BFS 可能返回 S→B→T→Z；两条都是最少边数路径。起点或目标不存在、或目标不可达时返回 `null`；起点等于目标时返回仅含起点的路径。

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

若要列出所有不重复经过同一站点的路线，S→A→T→Z 与 S→B→T→Z 都是有效候选。BFS 的 parent 只保留 T 的第一个父节点 A；若把全局 visited 直接拿来做路径枚举，T 经 A 加入 visited 后，经 B 到达 T 的分支会被误删。这里的输出身份是顶点序列；若邻接数组允许重复邻居，同一路线会重复输出。若平行边本身代表不同路线，则须把边身份也纳入结果。

backtracking（回溯）沿候选边选下一站，递归扩展；回到上一层时撤销刚才加入的站点和路径项。onPath 只表示“这个顶点正在当前候选路径上”。它会拒绝 T→S，因为 S 已在这条路径里；回到起点的另一条分支时，T 的标记已撤销，因此 T 可以再次进入另一条路线。

下图跟踪同一张路网的两个分支。走完 A 分支并返回 S 后，`onPath` 恢复为 `{S}`；因此 B 分支可以再次进入 T。到 T 时仍会跳过回到 S 的边，因为 S 还在当前路径上。

![两个分支中的 path 与 onPath 状态，以及返回时如何撤销标记](../../engineering-foundations/algorithms/resources/graph-search-and-backtracking-backtrack.svg)

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

调用 `visit` 时，`path` 和 `onPath` 都已含起点；到达目标时先复制路径，再逐层返回并撤销各自加入的顶点。起点等于目标时只返回零边路径 `[[start]]`；起点或目标不存在、或目标不可达时返回 `[]`。

如果本次问题只需一条路线，不应枚举所有路线。在起终点不同的完全有向图中，恰好经过全部 V−2 个中间顶点的简单路径就有 (V−2)! 条，未计只经过其中一部分的路径；数量至少可达阶乘级，本例代码没有候选数上限。令 C 为实际检查的候选边数、L 为复制到结果中的路径总长度，运行时间按 O(C + L) 计；即使结果少，搜索也可能访问许多最终无法到达目标的前缀。递归栈、path 与 onPath 的辅助空间为 O(V)，返回结果另占与所有输出路径总长度相称的空间。深图也可能超过 JavaScript 调用栈深度，此时应把递归状态改成显式栈，但仍须在回退时撤销 onPath。

### 依赖排序：每条有向边都必须满足先后顺序

topological sort（拓扑排序）回答的是依赖能否排成执行顺序。此处暂把 S→A、S→B、A→T、B→T、T→Z 解释为“前站必须先完成”的依赖；若每条边 u→v 表示 u 必须先于 v，拓扑序才是可执行顺序。把 T→S 也解释为依赖时，S→A→T→S 已成环，要求 S 先于 T 又要求 T 先于 S，因此不存在合法顺序。若 T→S 只是回程路线、不是依赖，就从依赖图删去这条边；其余边形成 DAG（directed acyclic graph，有向无环图），可排成 S、A、B、T、Z。

下面的 Kahn 算法维护每个顶点尚未满足的入边数。入度为 0 表示当前可执行；取出它后，逐条解除后继的一项依赖。依赖图移去了作为回程路线的 T→S 后，队列和入度按下表变化：

| 操作 | ready 队列（队首→队尾） | 输出 order | 入度变化 |
|---|---|---|---|
| 初始化 | S | — | S=0，A=1，B=1，T=2，Z=1 |
| 取出 S | A、B | S | A、B：1→0 |
| 取出 A | B | S、A | T：2→1 |
| 取出 B | T | S、A、B | T：1→0 |
| 取出 T | Z | S、A、B、T | Z：1→0 |
| 取出 Z | 空 | S、A、B、T、Z | 无 |

若取出的顶点数少于图中顶点数，返回 `null` 表示不存在完整拓扑序；剩下的顶点可能在环内，也可能只被环阻塞，因此该返回值不是环路径。

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

在本例的原路网中，S、A、B、T、Z 的初始入度分别为 1、1、1、2、1，ready 为空；边 S→A→T→S 已成环，Z 又依赖 T，所以没有节点可取。剩余集合含真正成环的节点，也含被环阻塞的 Z。每个顶点和边各处理常数次，邻接表下时间 O(V + E)、额外空间 O(V)。入度为 0 的顶点可能不止一个，因此不同合法拓扑序都可能成立。初始 ready 队列按顶点首次出现顺序排列；后续变为 ready 的顶点则按当前出队顶点的邻接表扫描顺序入队，并由 FIFO 队列处理，不保证沿用它们在原 Map 中首次出现的顺序。若业务要求特定顺序，应明确再加优先级规则，而不能把任意拓扑序当成唯一答案。

### 非负权最短路：松弛距离，并跳过过期堆项

现在切回路网而非依赖图，为每条路线边加上非负安全整数耗时：S→A 为 1，S→B 为 4，A→T 为 6，B→T 为 1，T→S 为 2，T→Z 为 1。加权邻接表的每个键仍代表一个顶点，每条边是 `{to, weight}`，且 `to` 必须是图中的键。BFS 仍找到 3 条边的 S→A→T→Z，但总代价是 8；代价较小的 S→B→T→Z 为 6。边数最少和代价最低是两个问题。

Dijkstra 算法用最小堆优先处理当前距离最小且尚未定型的顶点。relaxation（松弛）一条边 v→w 时，若 dist[v]+weight 小于已知 dist[w]，就更新距离与前驱并把新距离推入堆。此实现不原地修改旧堆项；某顶点改善时会留下旧项，弹出时若其距离已不等于当前 dist，就跳过。堆还可含同一个顶点的多条距离记录，settled（已定型）集合保证顶点只处理一次。本函数计算 source 到全图的距离，不因找到 Z 就提前结束；Z=6 先作为暂定距离入堆，等 Z:6 作为最小的未定型项出堆时才定型。

| 弹出的堆项 | 更新 | 堆中待处理项（可能含过期项） | 说明 |
|---|---|---|---|
| S:0 | A=1，B=4 | A:1、B:4 | 从源点展开 |
| A:1 | T=7 | B:4、T:7 | 暂时走 A |
| B:4 | T 从 7 改为 5 | T:5、T:7 | 新项入堆，T:7 成为过期项 |
| T:5 | 暂定 Z=6；S 已定型，跳过 T→S（若计算，和为 7） | Z:6、T:7 | Z:6 尚未定型 |
| Z:6 | 无 | T:7 | Z 此时定型，距离 6 才可确认 |
| T:7 | 无 | 空 | 因 7 不等于 dist[T]=5，跳过 |

跳过旧项并处理完全部可达点后，最终距离表为 `S=0, A=1, B=4, T=5, Z=6`。

可定型的理由：若到刚弹出的 v 仍有更短路线，取路线上的第一条 u→x，其中 u 已定型、x 尚未定型。u 的定型距离不大于路线到 u 的前缀；出队时扫描 u→x 后，堆中 x 的有效距离不大于路线到 x 的前缀（若新候选没有改善，原有效项不大于新候选）。非负边使此前缀不超过全路线，因此 x 的有效项应小于 dist[v]，与 v 是最小未定型项矛盾。

负权会破坏这个前缀关系。作为反证，假设不执行下方的负权校验而直接运行核心循环，再加 B→A、权重 −5，则 A 在距离 1 时已定型；处理 B:4 时，经 B 到 A 的候选代价为 −1，但核心循环会跳过已定型的 A，错误保留 1。本文实现会先扫描整张图；任何负权或非安全整数权重、以及指向非图顶点的边都会抛出 `RangeError`，即使该边从 source 不可达。搜索中若形成超出安全整数范围的候选和，也会抛出 `RangeError`。负权图应改用能处理负边的算法（例如无负环前提下的 Bellman–Ford），不能因为某个负权样例恰好算对就使用 Dijkstra。

下面的最小堆仅按 `distance` 排序；它只服务此完整示例，与[优先队列的上浮和下沉](#43.%20%E6%80%8E%E6%A0%B7%E5%9C%A8%E4%B8%8D%E6%96%AD%E5%8A%A0%E5%85%A5%E4%BB%BB%E5%8A%A1%E6%97%B6%E6%8C%81%E7%BB%AD%E5%8F%96%E5%87%BA%E6%9C%80%E9%AB%98%E4%BC%98%E5%85%88%E7%BA%A7%EF%BC%9F)共享数组堆机制。`weightedPath` 必须接收运行 Dijkstra 时使用的同一 source；不在图中的 target 或从 source 不可达的 target 返回 `null`，source 等于 target 时返回 `[source]`。通过整图预检后，若 source 不在图中，Dijkstra 返回空的距离表和前驱表；在图中但从 source 不可达的顶点距离为 `Infinity`。代码把权重和距离限制为安全整数，并拒绝负权或超出安全范围的路径和。

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

实现先用一个独立循环预校验全图的 E 条边；在随后的松弛循环中，每个已定型顶点只扫描一次出边，因此该阶段总计至多扫描 E 条边，至多成功松弛并压入 E 个新项。加上起点初始项后，惰性堆最多处理 E+1 个项，故 `dijkstra` 时间 O(V + (E + 1) log(E + 1))、空间 O(V + E)。若用带 decrease-key 的索引优先队列，通常可把堆空间降到 O(V)，时间写作 O((V + E) log V)。`weightedPath` 沿前驱回溯一条长度为 P 的路径，另需 O(P) 时间并返回 O(P) 个顶点。无论用哪一种实现，距离表、前驱表、堆项和 visited/settled 状态都要对应同一个图与同一组边权。

> [!info]- 来源
> - 邻接表遍历、BFS 按边数找最短路、首次发现时记录父边：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §4.1 “Undirected Graphs”](https://algs4.cs.princeton.edu/41graph/)，作者实现 [BreadthFirstPaths.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/BreadthFirstPaths.java.html)。BFS 原理同样适用于本页的有向邻接表。
> - DAG 才有拓扑序，以及顶点/边线性量级的 DFS 版本：[Algorithms, 4th ed., §4.2 “Directed Graphs”](https://algs4.cs.princeton.edu/42digraph/)，作者的队列版本 [TopologicalX.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/TopologicalX.java.html)。本页采用 Kahn 入度实现，示例输出由 Node.js 运行复算。
> - Dijkstra 的非负权前提、松弛与索引优先队列复杂度：[Algorithms, 4th ed., §4.4 “Shortest Paths”](https://algs4.cs.princeton.edu/44sp/)，作者实现 [DijkstraSP.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/DijkstraSP.java.html)。惰性重复入堆会让优先队列最多保留与边数同阶的项：[LazyDijkstraSP.java](https://algs4.cs.princeton.edu/44sp/LazyDijkstraSP.java.html)。本页用这类堆显示过期项，复杂度按本页实现计。
> - 本页图算法的哈希字典成本模型：[ECMAScript 2026, §24.1 “Map Objects” 与 §24.2 “Set Objects”](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。规范要求平均访问时间次线性，不规定具体的数据结构或 O(1) 上界。
## 45. 动态规划如何定义状态并安排更新顺序？

dynamic programming（动态规划，DP）把问题拆为有限状态；每个状态只保留后续转移需要的信息。先写递推关系和初始状态，再按依赖顺序计算，复用一维数组时还要追踪每个格子属于哪一轮。

### 状态如何消除重复计算？

若多个递归分支会请求同一个子问题，记忆化将结果保存后复用；自底向上迭代则按依赖次序计算状态。以 Fibonacci 数列为例：F(0)=0、F(1)=1、F(n)=F(n-1)+F(n-2)。朴素递归每层分叉，O(2ⁿ) 是一个时间上界，调用栈 O(n)；迭代每个 n 只更新一次，执行 O(n) 次加法并同时保留两个数。

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

迭代状态的含义是：进入第 i 轮前，`previous=F(i-2)`、`current=F(i-1)`；一轮同时把二者移到 `F(i-1)`、`F(i)`。右侧先读取旧状态，再一次赋给两个变量：

| i | 进入本轮的 `(previous,current)` | 本轮之后 | 新的 `current` |
|---:|---|---|---:|
| 2 | (0, 1) | (1, 1) | F(2)=1 |
| 3 | (1, 1) | (1, 2) | F(3)=2 |
| 4 | (1, 2) | (2, 3) | F(4)=3 |
| 5 | (2, 3) | (3, 5) | F(5)=5 |

`n` 为 0 或 1 时直接返回初值，不进入循环。这里的 O(n) 指加法次数；若每个数占固定宽度，迭代时间为 O(n)、额外空间为 O(1)。若换成 BigInt，整数位数随 n 增长，每次加法也会变贵，不能把 O(n) 次加法直接称为 O(n) 位运算。

JavaScript Number 的整数运算只有在每个中间结果都落在安全整数范围内时才保证精确。F(78)=8,944,394,323,791,464 仍可精确表示；F(79)=14,472,334,024,676,221 已超过 2⁵³−1。相同限制也作用于楼梯方案计数，例如 climbStairs(78,[1,2]) 计算 F(79)；背包有限值相加也可能越界，甚至把两个有限 Number.MAX_VALUE 加成 Infinity。若要求大整数精确，用 BigInt 并调整初始值、返回类型和调用方；若背包值含小数，Number 结果本来就是二进制浮点近似。按精确整数契约时，输入值应为安全整数且所有候选和不超过 Number.MAX_SAFE_INTEGER。

### 计数问题的状态和循环顺序是什么？

爬楼梯示例定义 `ways[total]` 为按顺序选择合法步长、总和恰为 total 的方案数。`ways[0]=1` 表示空序列；每个合法正整数步长 `step` 贡献 `ways[total-step]`。输入要求步长为互异正整数，否则重复步长会重复计算同一选择。下面按目标总和再按步长转移。计算 `ways[total]` 时，所有更小的总和已经完成；把新步长接到较小总和的每条序列末尾，恰好得到以该步长结尾的序列。

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

当 `steps=[1,2]`、`n=3` 时，循环状态如下。`total` 是外层循环，因此每条有序序列只会在其最后一步被加进一次：

| total | 已有状态 | 各步长贡献 | 更新后 `ways[total]` |
|---:|---|---|---:|
| 0 | `ways[0]=1` | 空序列作为基底 | 1 |
| 1 | `ways[0]=1` | step 1: 1 | 1 |
| 2 | `ways[1]=1, ways[0]=1` | step 1: 1；step 2: 1 | 2 |
| 3 | `ways[2]=2, ways[1]=1` | step 1: 2；step 2: 1 | 3 |

对应序列是 1+1+1、1+2、2+1；顺序有意义，1+2 与 2+1 是不同方案。若改成先遍历步长、再递增遍历总和，仍会更新较小总和，但每种步长组合只计一次；本例会得到 2，而不是这里定义的 3。空步长数组也有效：`n=0` 返回空序列方案 1，`n>0` 返回 0；`[1,,2]` 会在按下标校验时拒绝，避免 `some` 跳过数组洞。

循环主体执行 n×k 次步长检查，分配 `ways` 需要 n+1 个槽位。去重还会建立一个大小为 k 的 `Set`；常见哈希实现下，插入和查重平均 O(k)，所以整段代码平均时间为 O((n+1)(k+1))、辅助空间为 O(n+k+1)。ECMAScript 只要求集合访问平均为次线性，不保证每种引擎的每次访问严格 O(1)；这里把动态规划循环成本与集合实现的平均成本分开说明。数组长度仍须能在当前运行时分配。

### 0/1 背包为何要从大容量向小容量更新？

先保留物品轮次，定义 `dp[i][c]` 为只看前 i 件物品、总重量不超过容量 c 时的最大价值。空选择可行，所以 `dp[0][c]=0`；第 i 件物品重量 w、价值 v 的转移为 `dp[i][c]=dp[i-1][c]`，或在 `c>=w` 时取两者较大值 `max(dp[i-1][c], dp[i-1][c-w]+v)`。选当前物品后剩余容量的子问题只能使用之前的物品，这正是 0/1（每件最多一次）约束。

代码把上一行和当前行压进同一个 `best` 数组：处理完前 i 件物品时，`best[c]` 应等于 `dp[i][c]`。容量从大到小时，若 w>0，来源 `c-w` 比 c 小，尚未在本轮更新，所以读到的是上一行；因此不能重复拿当前物品。若容量从小到大，只有 `c-w>=w` 时，来源槽 `c-w` 已在本轮访问过，才可能含当前物品；对 w=2，c=2、3 的来源 0、1 仍是旧行，走到 c=4 时读取的 `best[2]=3` 已含当前物品，因而可再取一次。所有容量都按升序完成后，结果满足无限次取用的转移。w=0 时来源与目标是同一槽，每个容量槽在本轮只访问一次，右侧只读旧值，仍是每件最多取一次。

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

假设容量 W=4，有两件物品 (重量,价值)=(2,3)、(3,4)。表格的行表示已经处理完的物品数，列 c 表示容量上限；每格允许未装满：

| 已处理物品 | c=0 | c=1 | c=2 | c=3 | c=4 |
|---|---:|---:|---:|---:|---:|
| 0 件（初始行） | 0 | 0 | 0 | 0 | 0 |
| 只处理 (2,3) | 0 | 0 | 3 | 3 | 3 |
| 再处理 (3,4) | 0 | 0 | 3 | 4 | 4 |

因此一维状态依次为 `[0,0,0,0,0]`、`[0,0,3,3,3]`、`[0,0,3,4,4]`，最优价值 4，可留下未用容量。若只处理第一件且按容量从小到大更新，会先写 `best[2]=3`，再用已更新的 `best[2]` 算出 `best[4]=6`；这一步把唯一一件物品用成了两件。

0/1 背包对 n 件物品、整数容量 W 的动态规划时间为 O((n+1)(W+1))，数组辅助空间为 O(W+1)，不计输入数组。它覆盖 n=0 或 W=0；这是伪多项式复杂度，因为 W 的数值可比其输入编码位数大得多。W=0 时仍会处理每件零重量物品一次；倒序循环在容量 0 也只更新一次，所以正价值零重量物品可各取一次。有限价值允许为负，但零初始化表示可以不选任何物品，因此负价值项不会改善答案。若要恰好装满，除 `best[0]=0` 外其余状态应初始化为不可达哨兵，并在转移时跳过不可达状态。若物品允许无限次且重量为正，才可从小容量向大容量更新；若零重量物品有正价值且可无限选，最优值没有有限上界。若把数值改成 BigInt，比较与加法成本还取决于价值的位数。容量数组也必须能在当前运行时分配。

> [!info]- 来源
> - 三类递推、初值和循环顺序按本页方程、表格及可运行代码逐项复算；动态规划时间只计状态转移/数值运算，状态数由容量 W 等数值参数决定，故背包为伪多项式。经典有限容量表格转移、计数递推见 [CSES Competitive Programmer’s Handbook, ch. 7 “Dynamic programming,” §7.4 “Knapsack problems”](https://cses.fi/book/book.pdf)，以及 §7.1 “Coin problem” 中计数解的基础状态和递推；本页将其状态和循环次序具体化到 JavaScript 一维数组。
> - Number 安全整数边界按 ECMAScript Number.MAX_SAFE_INTEGER=2⁵³−1 核对：[ECMAScript 2026 numbers](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)。集合的平均访问要求见 [ECMAScript 2026 Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-keyed-collections)。
## 46. 分区如何改变快速排序的时间和空间代价？

案例背景：合成报表 42 要按数值指标升序展示。为了只看排序过程，先把每行其他字段省略，改用一组教学指标 `[5,2,4,1,3]`。quicksort（快速排序）选择 pivot（基准值），把输入分到基准值前后，再递归排序两侧；每轮分区后的左右规模决定递归树有多深。

### 三路分区怎样处理小于、等于和大于基准的值？

下面是便于观察中间数组的构造版 quicksort：它为每次非基例调用新建 lower、equal、higher 三个数组，分别放小于、等于、大于基准值的项；只递归处理 lower 与 higher，最后按这三段顺序拼接。这里的 pivot 取当前数组的中间下标，不保证是数值中位数。

调用者需传入无空槽的普通数组；每个迭代到的值都必须是 JavaScript `number` 且不是 `NaN`。在未篡改原型的普通稀疏数组中，空槽会由 `for...of` 读作 `undefined`；`undefined` 和 `NaN` 与基准值的 `<`、`>` 都会得到 false，因而被放进 `equal`，破坏数值分区。正负 `Infinity` 仍能按数值比较；`-0` 和 `+0` 在这段代码里会进入同一个 equal 桶。混合类型还可能触发 JavaScript 的类型转换，不能再把桶当作一致的数值顺序。

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

长度为 0 或 1 时直接返回原数组。长度大于 1 时函数不改写输入数组，而是用分区数组和拼接结果生成新数组。

输入 `[5,2,4,1,3]` 的中间下标是 2，所以 pivot=4。下表逐项展示扫描怎样改变三个桶：

| 扫描到 | lower（小于 4） | equal（等于 4） | higher（大于 4） |
|---|---|---|---|
| 开始 | [] | [] | [] |
| 5 | [] | [] | [5] |
| 2 | [2] | [] | [5] |
| 4 | [2] | [4] | [5] |
| 1 | [2,1] | [4] | [5] |
| 3 | [2,1,3] | [4] | [5] |

所选 pivot 本身会进入 `equal`，所以每个长度大于 1 的调用至少从子问题中移走 pivot；两侧递归输入都严格短于当前数组，最终会到达长度 0 或 1 的基例。lower `[2,1,3]` 的中点下标为 1、pivot=1；其 higher `[2,3]` 再以中点下标 1 的 3 为 pivot。各子调用分区后的桶如下：

| 当前输入 | pivot | lower | equal | higher |
|---|---:|---|---|---|
| [2,1,3] | 1 | [] | [1] | [2,3] |
| [2,3] | 3 | [2] | [3] | [] |

空数组和单项数组都到达递归基。自底向上拼接：`quickSort([2,3])` 得 `[2,3]`；`quickSort([2,1,3]) → [...[], ...[1], ...[2,3]] → [1,2,3]`。回到第一轮后，`[...[1,2,3], ...[4], ...[5]]` 得 `[1,2,3,4,5]`。

为单独看重复值的分支，换成更小的合成输入 `[4,4,4]`：一次扫描就把三项都放进 equal，两个递归数组为空，不会再递归处理这些相等项；返回时拼接两个空结果和 `[4,4,4]`，输出仍是 `[4,4,4]`。大量相同值时，这能避免把同一批值反复切进递归。

### 为什么分区平衡决定递归深度？

复杂度按当前调用读过的元素数、数值比较、数组槽位写入和递归深度计算；假设单次数值比较为 O(1)，普通动态数组按几何扩容的摊还模型计算。长度为 n 的调用会扫描 n 项，每项最多做两次数值比较，向分区桶摊还写入 n 项，再在拼接时复制 n 项，所以本层工作为 Θ(n)；一次 `push` 仍可能因扩容复制 O(n) 个槽位。令 `L`、`E`、`R` 分别为 lower、equal、higher 的长度，满足 `L + E + R = n`；只有 L 与 R 会递归，E 已经归位。一般递推为 `T(n) = T(L) + T(R) + Θ(n)`。

若输入值在这段比较下互异（每次 `E=1`），且每个非基例调用的 `L`、`R` 近似均分其余项，那么每层至多扫描 n 项，其中靠近根的 Θ(log n) 层各扫描 Θ(n) 项；递归总深度为 Θ(log n)，因此总扫描为 Θ(n log n)。如果每个调用都有固定正比例的项进入 `E`，且剩余两侧持续近似平衡，各层待扫描规模会按几何比例递减，总扫描为 Θ(n)，即使递归深度仍是 Θ(log n)。因此不能只凭树深度推出 Θ(n log n)；全相等输入只需一轮 Θ(n) 扫描。

中点下标不保证 pivot 接近数值中位数。例如合成输入 `[7,5,3,1,2,4,6]` 中，这段实现每次都选出当前最小项。下表的每轮 lower 都为空、equal 只有 pivot；higher 是下一次非空调用：

| 当前输入 | 中点 pivot | 下一轮 higher |
|---|---:|---|
| [7,5,3,1,2,4,6] | 1 | [7,5,3,2,4,6] |
| [7,5,3,2,4,6] | 2 | [7,5,3,4,6] |
| [7,5,3,4,6] | 3 | [7,5,4,6] |
| [7,5,4,6] | 4 | [7,5,6] |
| [7,5,6] | 5 | [7,6] |
| [7,6] | 6 | [7] |

每轮把当前最小值放在结果前，完整递归仍返回 `[1,2,3,4,5,6,7]`；只是每层只少处理一个值，递推成为 `T(n)=T(n−1)+Θ(n)`，也就是 `n+(n−1)+…+2=Θ(n²)`；递归深度为 Θ(n)。大型输入的实际最大深度还受 JavaScript 引擎调用栈限制。

本实现并非原地排序。要读空间成本，先分开三个问题：整个运行总共写过多少数组槽位、某一时刻有多少数组槽位同时可达、递归调用栈有多深。按代码所需数组都由未返回的调用帧保留来估算：

| 计数口径 | 分区近似平衡 | 连续偏斜 |
|---|---|---|
| 累计槽位写入 | 每个非基例调用分区与拼接共写 Θ(n) 槽位；每层子数组总长 O(n)，共 O(log n) 层，合计 O(n log n) | 依次处理 n、n−1、n−2… 项，算术和为 Θ(n²) |
| 峰值同时可达槽位 | 活动路径上未返回帧引用的输入、分区桶和拼接进度，随子问题规模约为 n、n/2、n/4…；几何和为 O(n) | 未返回帧引用的输入、分区桶和拼接进度，随子问题规模约为 n、n−1、n−2…；算术和可达 O(n²) |
| 递归帧数量 | O(log n) | Θ(n) |

这里的峰值是调用帧仍引用数组时的槽位模型，不等于引擎实测字节数；变量回收、垃圾回收时机和容量增长由运行时决定。

### 内置排序何时修改数组，何时保留副本？

~~~javascript
const values = [80, 9, 12];
const sortedInPlace = values.sort((a, b) => a - b);

const copyInput = [80, 9, 12];
const sortedCopy = copyInput.toSorted((a, b) => a - b);
~~~

| 方法 | 调用后的原数组 | 返回值 |
|---|---|---|
| `sort()` | `[9,12,80]` | 同一个数组 `[9,12,80]` |
| `toSorted()` | `[80,9,12]` | 新数组 `[9,12,80]` |

省略比较器时，`sort()` 将元素转成字符串再按字符串顺序比较，因此 `[80,9,12].sort()` 得到 `[12,80,9]`；数值升序要显式给出 `(a,b)=>a-b` 这样的比较器，并让比较器对输入给出一致顺序。`toSorted()` 只有在运行环境支持该方法时才可用。对 n 项，它会返回一个存放 n 个结果的新数组；这份 O(n) 输出空间应与排序本身分开计算。

自 ECMAScript 2019 起，`sort()` 要求稳定；`toSorted()` 也使用稳定排序。对给出一致顺序的比较器，比较结果为 0 的项保留输入中的相对次序。例如 `[A(5), B(5), C(3)]` 按分数升序后为 `[C(3), A(5), B(5)]`。但“原地修改并返回同一数组”是 `sort()` 的接口行为，不保证实现内部排序时使用 O(1) 额外空间；`toSorted()` 还需为结果创建 O(n) 个输出槽位。ECMAScript 也没有规定排序算法或可移植的比较次数/时间界；实际比较调用序列由运行时实现决定。因此这里不把某个引擎的 O(n log n) 实现细节写成语言保证。

> [!info]- 来源
> - 三路快速排序将小于、等于、大于基准的项分开，并避免递归处理已相等项：[Robert Sedgewick 与 Kevin Wayne, *Algorithms*, 4th ed., §2.3 “Quicksort”](https://algs4.cs.princeton.edu/23quicksort/index.php)。其 `Quick3way.java` 先打乱输入再原地分区；本页保留数组构造版和中点下标 pivot，用它解释额外数组及偏斜输入的代价，不把两种实现混为一谈。
> - 输入约束中空槽及非数值比较的行为：[ECMAScript 2026 `%ArrayIteratorPrototype%.next`](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-%arrayiteratorprototype%.next) 按索引读取值；空槽读为 `undefined`。[关系运算符](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-relational-operators-runtime-semantics-evaluation) 规定 `undefined` 转为 `NaN` 后比较结果为 false；[`Number::lessThan`](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html#sec-numeric-types-number-lessthan) 规定 NaN 不形成小于关系。
> - `Array.prototype.sort` 的比较器约定、稳定次序、字符串默认比较和由实现决定的比较调用序列：[ECMAScript 2019 §22.1.3.27](https://tc39.es/ecma262/2019/#sec-array.prototype.sort)、[ECMAScript 2026 §23.1.3.30](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)。
> - `toSorted()` 创建新数组、逐项写入排序结果并使用稳定排序：[ECMAScript 2026 §23.1.3.34](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.tosorted)。示例由 Node.js v26.13.0 本地复算。
## 47. 文本算法应按码元、码点还是字素簇处理？

报表 42 的事件描述可能含 emoji、组合重音或其他扩展文字。JavaScript 字符串索引、Unicode 码点和用户看到的字符不是同一种单位：先定义任务要计数、比较或切分什么，再实现算法。这里第一次说明三个单位：UTF-16 code unit（UTF-16 编码单元）、Unicode code point（Unicode 码点）和 extended grapheme cluster（扩展字素簇）。一个 UTF-16 编码单元是一个 16 位值；补充平面的 emoji 以代理对占两个编码单元、表示一个码点。组合重音本身是一个码点，但通常同前一个基字符组成一个扩展字素簇。

### 三种长度会怎样不同？

JavaScript String.length 返回 UTF-16 编码单元数。Array.from 对字符串迭代时把有效代理对组合成一个码点，孤立代理仍单独保留，但组合附加符仍是另一个码点。Intl.Segmenter 的 grapheme 模式按 locale（语言环境）与实现提供的分段规则给出字素簇；这通常接近用户感知字符，但规则可定制，不能把某个 Node 运行时的结果等同于当前 UAX #29 版本的每条边界规则。

同一个输入 `A😀e\u0301` 可以按三种单位划分。每个方框算作该行的一个单位；横向边界对齐原始 UTF-16 位置，不表示字符在屏幕上的显示宽度。`◌́` 中的虚线圆只是帮助看清组合重音，不属于输入。

![A、emoji 与组合重音在编码单元、码点、字素簇三种粒度下的分组](../../engineering-foundations/algorithms/resources/text-string-units.svg)

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

这里 A 占 1 个编码单元和 1 个码点；😀 是代理对，占 2 个编码单元、1 个码点；e 加 U+0301 组合重音占 2 个编码单元、2 个码点，却通常成为 1 个字素簇。字符计数不能代替存储大小：若限制请求字节数，还要另外按明确编码计算字节。

### 返回的索引按什么单位计？

字符串方法返回的位置通常是 UTF-16 编码单元偏移；把字符串先转成数组后，数组下标则数数组元素。`Intl.Segmenter` 的分段记录也用原字符串的编码单元偏移，所以可直接用 `part.index` 定位原始字符串。

~~~javascript
const indexedSample = 'A😀e\u0301';
const graphemeSegments = Array.from(
  new Intl.Segmenter('en', { granularity: 'grapheme' }).segment(indexedSample)
);
const graphemes = graphemeSegments.map(({ segment }) => segment);
const finalGrapheme = 'e\u0301';

console.log(indexedSample.length); // 5 UTF-16 code units
console.log(indexedSample.indexOf(finalGrapheme)); // 3 code-unit offset
console.log(Array.from(indexedSample).indexOf('e')); // 2 code-point array index
console.log(graphemeSegments.find(({ segment }) => segment === finalGrapheme).index); // 3 code-unit offset
console.log(graphemes.indexOf(finalGrapheme)); // 2 grapheme-array index
~~~

| 表达式 | 返回值 | 位置单位 |
|---|---:|---|
| `indexedSample.length` | 5 | 编码单元数量，不是索引 |
| `indexedSample.indexOf(finalGrapheme)` | 3 | 原字符串编码单元偏移 |
| `Array.from(indexedSample).indexOf('e')` | 2 | 码点数组下标 |
| Segmenter 记录的 `.index` | 3 | 原字符串编码单元偏移 |
| `graphemes.indexOf(finalGrapheme)` | 2 | 字素簇数组下标 |

因此码点数组或字素簇数组里的下标不能直接传给原字符串的 `slice`、`substring` 等方法；它们按编码单元解释参数。这里 `slice(2)` 会从 😀 的低代理 U+DE00 开始，`slice(3)` 才从 `e\u0301` 开始。若要在原文本中高亮或替换数组中的元素，应保留原字符串偏移（例如 Segmenter 的 `.index`），或显式建立数组下标到原偏移的映射。

Array.from 也不会自动把规范等价的不同码点序列变成相同序列。例如预组字符 é 与 e 加组合重音肉眼可相同，但码点逐个比较不同：'é' === 'e\u0301' 为 false，而 NFC 规范化后两者相等。若业务要求规范等价比较，可在明确边界使用 `normalize('NFC')`；保留原始输入时不要无意改写其码点序列。NFC/NFD 处理规范等价；NFKC/NFKD 还会合并部分兼容形式，适不适合取决于任务，不能当作显示文本的通用清理。规范化后的索引属于规范化副本：例如 `'e\u0301'.length` 是 2，`'é'.length` 是 1；若要改写原输入，不能把副本上的偏移直接套回原文。

### 回文和连续重复要比较什么单位？

原示例的回文函数按码点逆向比较，所以它把代理对当作单个元素，但不会把规范等价序列规范化；若要按用户可见单元比较，先用 Segmenter 切成字素簇。相同函数逻辑可接受不同切分结果：

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

const palindromeText = 'e\u0301x\u0301e';
console.log(isPalindromeByCodePoint(palindromeText)); // true
console.log(splitGraphemes(palindromeText));          // ['é', 'x́', 'e']
console.log(isPalindromeByGrapheme(palindromeText));  // false
~~~

同一个输入可因单位不同而得出不同结果：

码点序列是 `e, U+0301, x, U+0301, e`，镜像两端相等；默认字素簇则是 `e\u0301, x\u0301, e`，首尾不相同。

两个回文函数的输入约定是字符串，空字符串返回 true；它们用精确字符串相等比较，不做规范化或 case folding。规范化是另一个决定：`'éxe\u0301'` 按字素簇比较为 false，先作 NFC 后成为 `'éxé'`，再比较为 true。UAX #29 的默认扩展字素簇是可复现的分段规则，但语言或应用可进行 tailor（定制），也不是编码字节长度。

令 m 为码点数、g 为字素簇数、u 为 UTF-16 编码单元数。码点版本先物化 m 个码点，再做至多 floor(m/2) 次等值比较，时间与临时数组空间为 O(m)。字素簇版本的分段时间由 `Intl.Segmenter` 实现决定，ECMAScript 不给它渐进界。收集段需要 O(g) 项；在常见的逐编码单元字符串比较成本模型下，至多比较 floor(g/2) 对段，所比较的段文本总长不超过 O(u)，故分段后的物化与比较为 O(u+g)。数组保存 g 个段引用，段文本的额外存储最多 O(u)（运行时可共享底层字符串）。两种实现都不含规范化成本。

最长连续重复示例的输入约定为字符串；它按码点统计完全相同的连续项，并在并列时返回第一个最长段。空字符串返回空字符、长度 0。对 Array.from('😀😀A')，结果是字符 😀、长度 2，而按 UTF-16 下标遍历会把每个 emoji 拆成两个编码单元。令输入有 m 个码点，`Array.from` 创建 m 个数组项，循环处理每个码点和一次末尾哨兵，因此总时间 O(m)、辅助空间 O(m)。

对 `AABB` 逐轮追踪 `currentLength` 和 `bestChar/bestLength`。每轮开始时，`currentLength` 记录以 `i-1` 结尾的当前段长度；第 i 项与前项相同就延长当前段，否则先结算上一段并从当前字符开始新段。到 `i===characters.length` 时，结束哨兵强制结算尾段：

| i | 输入 | 动作 | 当前段 | 最佳段 |
|---:|---|---|---|---|
| 初始 | A | 初始化 | A/1 | A/1 |
| 1 | A | 与前项相同，延长 | A/2 | A/1 |
| 2 | B | 结算 A，再从 B 开始 | B/1 | A/2 |
| 3 | B | 与前项相同，延长 | B/2 | A/2 |
| 4 | 结束哨兵 | 结算 B；长度相同，不覆盖 | — | A/2 |

使用严格大于 `currentLength > bestLength` 使并列时保留先出现的 A；结束哨兵负责结算尾段。

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

`Intl.NumberFormat` 按 locale 显示数值，也能接收 BigInt 和表示数值的字符串；手写函数则按三位给原始十进制文本插入逗号。下表显式调用 `Number(...)` 的一行，在格式化前就已丢失精度。用 `9007199254740993` 这个超过安全整数范围的文本作对照：

| 调用 | 输出 | 保留的信息 |
|---|---|---|
| `formatNumber(1234.5, 'en-US')` | `1,234.5` | en-US 数字显示规则 |
| `formatNumber(1234.5, 'de-DE')` | `1.234,5` | de-DE 数字显示规则 |
| `formatIntegerThousands('9007199254740993')` | `9,007,199,254,740,993` | 原整数字符串的全部数字 |
| `formatNumber('9007199254740993', 'en-US')` | `9,007,199,254,740,993` | 直接传入数字文本，未先转成 Number |
| `formatNumber(9007199254740993n, 'en-US')` | `9,007,199,254,740,993` | BigInt 表示的精确整数 |
| `formatNumber(Number('9007199254740993'), 'en-US')` | `9,007,199,254,740,992` | Number 转换时已舍入的数值 |

这个正则适合本例限定的 ASCII 整数字符串；普通回溯引擎可能在多个位置的前瞻中重复检查后缀，因此不对任意实现或输入规模声称线性时间。若要明确的单趟线性处理，可从右向左每三位分组再拼接，n 位输入需 O(n) 时间并生成 O(n) 输出；展示数字则优先使用 `Intl.NumberFormat`。

大小写切换示例的输入约定为字符串；它只变换 ASCII A–Z 与 a–z，其他码点保持不变。它不是适用于所有语言的大小写转换：Unicode 大小写映射可能依赖 locale，且转换前后长度也未必相同。若输入有 m 个码点、u 个编码单元，该函数逐码点处理一次并连接输出，时间 O(m+u)，临时映射数组 O(m)，结果字符串 O(u)；ASCII 大小写互换保持码点数和编码单元数不变。

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

大小写转换也不等于 case folding（大小写折叠）。`toLowerCase()` 使用 Unicode 默认小写映射；`toLocaleLowerCase(locale)` 按指定语言环境执行小写映射。两者都可能因上下文或语言规则扩展、改变文本，ECMAScript 没有通用的 `String.prototype.caseFold()`。例如 `'ß'.toLowerCase()` 仍是 `ß`，而 Unicode 18 的完整默认折叠把 U+00DF 映射为 `ss`；`'I'.toLocaleLowerCase('tr')` 则得到土耳其语无点小写 i `ı`。

| 输入与操作 | 输出 | 用途差别 |
|---|---|---|
| `'ß'.toLowerCase()` | `ß` | Unicode 小写映射，不是完整折叠 |
| Unicode 18 完整默认 case fold：U+00DF | U+0073 U+0073（`ss`） | Unicode 默认大小写无关匹配 |
| Unicode 18 完整默认 case fold：U+FB03 `ﬃ` | `ffi` | 个别兼容字符有专门的折叠映射 |
| Unicode 18 完整默认 case fold：U+017F `ſ` | `s` | 折叠映射也可能合并特殊字母 |
| `'I'.toLocaleLowerCase('tr')` | U+0131（`ı`） | 语言环境指定的大小写转换 |
| `'İ'.toLowerCase()` | U+0069 U+0307（`i` 加组合点） | 小写映射可能扩展为多个码点 |

若任务要求不区分大小写，先定义用默认完整折叠还是特定语言规则，并对存入键和查询文本使用同一处理链；如果还要求规范等价，再规定规范化与折叠的顺序及版本。NFC 本身不折叠大小写或重音；case folding 也不是通用兼容规范化或去重音规则，不过个别兼容字符有自己的折叠映射（如表中 `ﬃ` → `ffi`），且输出不保证保留原规范化形式。需要 NFC 输出时还须按契约再次规范化。通用文本匹配应使用明确版本的 Unicode 数据或库，不要把 ASCII 示例函数或普通小写转换当成跨语言折叠。

### Trie 怎样共享前缀并限制候选输出？

在合成报表 42 的描述搜索中，输入框要查找以已输入前缀开头的标签。Trie（前缀树）把键拆成一串单位，让有相同前缀的键沿着同一条路径前进；本例沿用本章的码点单位，按 Unicode 码点建边。Array.from 会把有效代理对组合成一个码点，所以 😀 是一条边；组合重音若未规范化，则仍是另一条码点边，不等同于视觉上的一个字素簇。

匹配契约选择 NFC（Normalization Form C，规范化形式 C）：写入键和查询前缀各自先作 NFC，Trie 再检查规范化后的查询码点序列是否为规范化后键码点序列的前缀。因而预组字符 café 与 cafe 加 U+0301 的查询相同；键以规范化后的形式枚举。这个选择会改变原始字符串前缀的语义：原键 `'cafe\u0301'` 确实以原始字符串 `'cafe'` 开头，但键 NFC 后是 `'café'`，Trie 用前缀 `'cafe'` 查询会得到 `[]`。NFC 不是去重音或大小写折叠：`Report` 也不匹配 `report`；若产品要不区分大小写、去重音或处理兼容字符，必须另外定义匹配规则。保存原输入展示时，可在 terminal 的 value 中保留显示文本。

| 插入键 | NFC 后的码点路径 | terminal 标记 |
|---|---|---|
| re | r → e | e 节点是完整键 |
| report | 与 re 共享 r → e，再接 p → o → r → t | t 节点是完整键 |
| reporter | 继续共享 report，再接 e → r | 最后一个 r 是完整键 |
| review | 与 re 共享 r → e，再从 v 分支 | 最后一个 w 是完整键 |
| 😀report | 😀 → r → e → p → o → r → t | t 节点是完整键 |
| 先 café，后 cafe 加 U+0301 | 两次写入经 NFC 后都走 café 的同一条路径 | 第二次写入覆盖第一次的 value |

每个节点有一张从码点到子节点的 Map 和一个 terminal（键结束）标记。只有 terminal 为 true 才表示完整键；“存在这段前缀”不等于“前缀本身也是键”。因此 re 可以既是完整键，也有通向 report 和 review 的后续分支。共享路径存一次，但每个前缀节点及子边 Map 都占内存。

下面实现插入、精确查询和有限前缀枚举。枚举从前缀节点开始做 depth-first search（DFS，深度优先搜索）；terminal 先于后代输出，因此前缀本身若也是键会先出现。子边按 Map 的插入顺序访问，所以结果不承诺字典序；limit 限制返回候选数，显式栈按需取一个子边，不会为了遍历先复制整张子边表。按本例的插入顺序，`keysWithPrefix('re', 3)` 先输出完整键 `re`，沿 p 分支输出 `report`、`reporter`，达到 3 后停止，因此尚未访问 v 分支中的 `review`。

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
> console.log('cafe\u0301'.startsWith('cafe'));    // true: raw-string prefix
> console.log(trie.keysWithPrefix('cafe'));        // []: separately NFC-normalized codepoint prefix
> console.log(trie.keysWithPrefix('re', 3));      // ['re', 'report', 'reporter']
> console.log(trie.keysWithPrefix('rep', 10));    // ['report', 'reporter']
> console.log(trie.keysWithPrefix('unknown', 5)); // []
> console.log(trie.keysWithPrefix('', 2));        // first two keys in trie traversal order
> ~~~

设 NFC 后的键含 m 个码点。插入和精确查询会先规范化一次，再把文本转为码点并沿 m 条边执行 Map 操作；在通常的哈希表平均 O(1) 子边访问模型下，路径查找/更新为期望 O(m)。规范化成本单独计为 `T_NFC(输入)`，不把它默认算作 O(m)；ECMAScript 规定 `normalize` 的结果形式，但不保证特定线性运行时间。规范化字符串和临时码点数组分别占 O(m) 空间；插入最多新建 m 个节点/边，已存在路径会复用。ECMAScript 对 Map 的要求也是平均次线性访问，严格 O(1) 同样是常见实现假设。

`keysWithPrefix` 的 `prefix` 先由 `normalizeKey` 规范化，再交给 `nodeFor`；而 `nodeFor` 又调用一次 `normalizeKey`，所以此例确实执行两次 NFC，第二次输入已经是 NFC。设规范化后前缀有 p 个码点和 u 个编码单元；设 DFS 实际访问 S 个节点、最大后缀深度 d、返回键字符串的编码单元总数 U、结果数 r。忽略实现相关的两次规范化成本后，前缀路径与 DFS/字符串构造的期望时间为 O(p + S + U)；完整时间另加 `T_NFC(原前缀)` 和 `T_NFC(规范化后前缀)`。不计 Trie 本身，规范化字符串占 O(u)，临时代码点数组占 O(p)，DFS 栈和码点路径占 O(d)，返回字符串占 O(U)，结果数组占 O(r) 个引用；合计 O(u+p+d+U+r)。limit 只限制返回条数，不保证访问节点数或输出字符总量为 O(limit)。若需要按语言区域排序的建议项，必须另外定义排序规则；本实现的 Map 插入顺序不等于语言排序。哈希表适合完整键的精确查找，不能直接定位整组前缀候选；按与前缀匹配一致的字典序排序时，匹配键形成连续区间，可以先二分找到起点再顺序输出；Trie 用更多节点和 Map 结构换取沿前缀直接定位。只有前缀查询足够常见时，这种空间取舍才值得。

> [!info]- 来源
> - JavaScript String 的 `length` 是 UTF-16 编码单元数、字符串迭代按码点处理、`indexOf`/`slice` 使用字符串偏移：[ECMAScript 2026, §22.1.3.9、§22.1.3.22、§22.1.3.36、§22.1.4.1](https://tc39.es/ecma262/2026/multipage/text-processing.html)。
> - Segmenter 的迭代位置是原字符串编码单元下标，分段记录 `.index` 返回 `startIndex`：[ECMA-402 2026, §§19.6–19.7](https://tc39.es/ecma402/2026/#segmenter-objects)，特别是 §19.7.1 `CreateSegmentDataObject`。
> - NFC 规范化 API：[ECMAScript 2026, §22.1.3.15 `String.prototype.normalize`](https://tc39.es/ecma262/2026/multipage/text-processing.html#sec-string.prototype.normalize)；该方法按最新 Unicode Standard 的规范化形式处理输入。规范等价、NFC/NFD 与 NFKC/NFKD 的区别：[UAX #15, Unicode 18.0.0, Revision 58, §§1.1–1.2](https://www.unicode.org/reports/tr15/tr15-58.html)，2026-08-12。
> - `toLowerCase` 的 Unicode 默认大小写映射及可能扩展码点数：[ECMAScript 2026, §22.1.3.28](https://tc39.es/ecma262/2026/multipage/text-processing.html#sec-string.prototype.tolowercase)；`toLocaleLowerCase` 语言环境映射、可扩展且上下文相关：[ECMA-402 2026, §20.1.2](https://tc39.es/ecma402/2026/#sec-string.prototype.tolocalelowercase)。Unicode 18 完整默认折叠按 UCD `CaseFolding.txt` 的 C+F 映射定义，U+00DF→U+0073 U+0073、U+FB03→U+0066 U+0066 U+0069、U+017F→U+0073；T 状态仅供 Turkic 选择，且该文件提醒 case folding 不保留 normalization form：[CaseFolding-18.0.0.txt](https://www.unicode.org/Public/18.0.0/ucd/CaseFolding.txt)，[UAX #44, Unicode 18.0.0, Revision 38](https://www.unicode.org/reports/tr44/tr44-38.html)。
> - Intl 构造器和本地化数字机制：[ECMA-402 2026 §8.2.7 `Intl.NumberFormat`](https://tc39.es/ecma402/2026/#sec-intl.numberformat)、[§8.2.10 `Intl.Segmenter`](https://tc39.es/ecma402/2026/#sec-intl.segmenter)、[§16 NumberFormat Objects](https://tc39.es/ecma402/2026/#numberformat-objects)；§16.5.16 `ToIntlMathematicalValue` 说明本例的数值字符串与 BigInt 如何跳过先转换为 Number 的步骤。字素簇默认边界与适用限制：[UAX #29, Unicode 18.0.0, Revision 49](https://www.unicode.org/reports/tr29/tr29-49.html)，2026-09-01；以 extended grapheme cluster 作默认分段，允许声明定制。
> - 运行复算：Node.js v26.13.0，ICU 79.1，Unicode 18.0，CLDR 49.0。只记录该运行时的输出，不据此断言其它运行时使用相同国际化数据或逐条采用 UAX #29 rev.49。
> - 数字安全整数上限：[ECMAScript 2026 Number.MAX_SAFE_INTEGER](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)，2⁵³−1。
> - Trie 的前缀路径、完整键终端标记和前缀枚举：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §5.2 “Tries”](https://algs4.cs.princeton.edu/52trie/)，作者实现 [TrieST.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/TrieST.java.html) 使用 256 路扩展 ASCII；本页使用 Map 子边与码点，避免把该 ASCII 实现误当成通用 Unicode 代码。
> - Map 的平均访问时间要求和迭代顺序：[ECMAScript 2026, Keyed Collections, §24.1 Map Objects](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-map-objects)，实现须平均次线性；Map iterator 按插入顺序产生条目。本页 O(m) Trie 路径步数采用常见哈希 Map 的平均 O(1) 子边访问模型，非规范保证。
## 48. 为什么连续扫描往往比链表遍历快？

假设代码要累计四个事件的时长。为了把内存位置画清楚，下面用一个合成例子：数组依次保存时长 `[4, 7, 1, 3]`，链表节点保存相同的时长，并额外保存 `next` 指针；两者的和都是 `15`。两边都访问 n 项，时间复杂度都是 O(n)，但复杂度不表示处理器要传输多少字节、何时知道下一次读取地址，或需要等待多少次缓存未命中。

图中的 cache line（缓存行）指缓存一次填充取得的一段相邻字节。本例假设每个时长和指针各占 8 B、节点无额外填充共 16 B、缓存行是 64 B；合成地址特意让数组项相邻、链表节点各自落在不同的缓存行。图示没有测量性能。

下图给同一组时长画出两种布局：数组的后续地址由基址和下标得出，链表的后续地址则来自当前节点的 `next`。

![数组中的四个时长共享一条 64 B 缓存行；链表的四个节点各在不同缓存行，前一节点的 next 指针给出后一节点地址](../../engineering-foundations/operating-systems/resources/memory-hierarchy-and-data-locality-access-layout.svg)

数组的第 i 项地址可从基址和 i 算出，不必先读完第 i 项才能知道第 i+1 项在哪。若该数组缓存行不在所观察的缓存层中，一次填充会把这 64 B 取入，其中已包含四个时长。链表里，节点 A 的 `next` 值是 `0x5080`；处理器要先取得 A 所在缓存行，才能读到这个地址并发出对节点 B 的依赖读取。

在同一缓存层中，若图中涉及的缓存行起初都缺失且没有预取抢先填充，数组访问触发 1 次 64 B 填充，链表访问四条不同的节点缓存行触发 4 次、共 256 B 填充。这只比较该层的传输量，不表示耗时或性能比值。这里链表行分散是人为假设；若多个节点落在同一行，后续节点可能复用该次填充，但仍要读到当前节点的 `next` 才能确定其地址。数组跨越多行时也会需要相应的更多填充。

若链表各节点行都未命中、又没有预取先行，单条链的后续 demand load（按需读取）就按 `next` 的地址依赖顺序发出。这个结论不表示每条链表必然一次节点一行或一次访问一次缓存未命中。

这条依赖链不等于 central processing unit（中央处理器，CPU）整体停住：缓存命中时等待较短，处理器也可能执行链外的独立指令或读取。某些硬件能识别规则地址模式，甚至改善固定步幅的指针追逐；任意分散的链表地址通常更难提前预测。图示只展示一种分散布局和冷缓存分支，不给出固定耗时或实测快慢。

### 延迟与带宽限制的是不同事情

一次内存读取的 latency（延迟）是从请求发出到数据可用的时间；bandwidth（带宽）是单位时间内能传送的数据量。读取若命中 cache（缓存），数据从相应缓存层级提供；未命中则还需从更远的缓存层级或主存取得。数据到达后，指令才能使用它，通常会把结果送入寄存器。缓存层数、容量、带宽和延迟随处理器与系统配置变化，代码不能假定固定层级或耗时。

cache line（缓存行）是缓存填充以及 cache coherence（缓存一致性）处理中常用的数据粒度。请求一个地址时，缓存通常按缓存行取得数据，因此相邻字节可能随同带回；之后访问相邻元素，就有机会直接使用已缓存的数据。这是 spatial locality（空间局部性）。短时间再次使用同一数据，它仍留在缓存中的机会较高，这是 temporal locality（时间局部性）。局部性增加命中机会，不保证每次都命中。

若流式循环平均每项实际传输 s 字节，可用带宽为 B 字节/秒，而且循环已受带宽限制，那么吞吐量上限约为 B/s 项/秒。这个估算不包含计算时间，也不能预测一次数据依赖读取的等待时间；延迟与带宽是不同约束。

Wulf 与 McKee 在 1995 年讨论处理器能力与内存供数能力之间逐渐扩大的差距，并称之为 memory wall（内存墙）。当程序在关键路径上等待数据或达到带宽上限时，再提高算术指令吞吐未必能加速整体工作。若工作集已在缓存或计算量占主导，内存供数就不一定是瓶颈。彼此独立的读取可以重叠等待、隐藏一部分延迟，但仍消耗共享带宽；独立请求足够多时，带宽同样会饱和。

### 连续地址让后续读取容易提前安排

下面的 C 片段要求实现提供 `uint64_t`。它们展示 C 的值与指针运算；图中的 8 B 指针和无填充 16 B 节点是教学布局，不是所有 C ABI 的保证。在 C 中，`durations[i]` 是数组中的第 i 个元素。`&durations[i]` 的字节地址可写成基址加上 i 乘以元素字节数；C 的指针加法本身已按元素大小前进，不能对指针再额外乘一次 `sizeof`。

~~~c
#include <stddef.h>
#include <stdint.h>

uint64_t sum_array(void) {
    uint64_t durations[] = {4, 7, 1, 3};
    size_t count = sizeof durations / sizeof durations[0];
    uint64_t total = 0;
    for (size_t i = 0; i < count; i++) {
        total += durations[i];
    }
    return total;
}
~~~

本例四项只占一条缓存行，展示的是同一填充内的空间复用。数组跨越多条缓存行时，处理器不必等待当前行的数据返回，就能算出后续地址；许多 hardware prefetcher（硬件预取器）可以利用这种规律，处理器也可能让多个彼此独立的读取同时在途，这类并行请求能力常称为 memory-level parallelism（内存级并行度，MLP）。

这只说明预取和重叠有机会发生，不保证一定发生。上述求和的 `total` 有逐次累加依赖；编译器是否展开循环或改用多个累加器、硬件能否发出多个读取，还取决于数据依赖、编译结果、可用请求资源和目标处理器。因此不能只凭代码外形承诺向量化或吞吐量。

### 链表遍历必须先取到下一个指针

下面的函数假设链表无环、尾节点的 `next` 为 `NULL`。每轮从当前节点读取 `next`；只有该字段的值可用以后，程序才能确定下一节点的地址。这种 pointer chasing（指针追逐）让一条普通链形成地址依赖。

~~~c
#include <stddef.h>
#include <stdint.h>

struct event_node {
    uint64_t duration;
    struct event_node *next;
};

uint64_t sum_events(struct event_node *head) {
    uint64_t total = 0;
    for (struct event_node *node = head;
         node != NULL;
         node = node->next) {
        total += node->duration;
    }
    return total;
}
~~~

节点的 `duration` 和 `next` 通常位于同一对象内；在图示的合成布局中，一次缓存行填充会同时带回这两个字段所在的数据。字段读取仍须从节点内存中取得，下一节点的地址仍要等 `next` 值可用。若多个节点恰好共处一条缓存行，后续节点可能复用填充；若节点分散且各行未命中，则链上的每个地址依赖都可能暴露等待。

乱序执行的处理器仍可执行这条链之外的独立工作；其它线程或另一条独立链也能产生在途请求。链上的依赖指令仍要等数据。若处理器没有别的就绪工作，这段等待就会影响整体进度。常见的 stream prefetcher（顺序流预取器）较难预测任意散布的指针链，但不能说指针链绝对不可预取：可识别的固定步幅等地址模式，在一些处理器上能降低有效延迟；software prefetch（软件预取）是否有益也要对目标负载测量。

### 渐进复杂度没有包含布局、移动与分配

两种遍历的渐进复杂度都可为 O(n)，这不代表实际耗时相同，也不表示两种表示每步读取相同的数据：

- 数组按下标访问通常为 O(1)；中间插入或删除需要移动后续元素，工作量为 O(n)，但移动范围连续，运行库或处理器可以使用优化过的批量操作。
- 链表按值查找通常为 O(n)。只有已经持有目标节点和所需链接时，插入或删除才需要有限次指针更新，可视为 O(1)；若还需先扫描定位，整个操作仍是 O(n)。
- 分配节点、节点大小、缓存未命中、锁竞争和访问顺序都会改变实际成本。对象池可以改变分配成本，却不保证链表顺序就是地址顺序。

因此，主要工作是按顺序扫描时，连续数组常是更好的起点；若系统频繁改动已知节点、要求节点地址稳定，或同一对象要参加多个关系，链表可能更合适。先按操作和所有权选择，再测量代表性数据规模与访问模式。Linux 内核文档也提醒，能满足需求的简单数组通常有更好的数据局部性。

### “数组”在语言中不总是同一种布局保证

C 数组的元素连续，多维数组按行优先排列。C++ `std::vector<T>` 对 `T` 非 `bool` 保证连续容器语义；`vector<bool>` 是专门化，不属于这项保证。C++ `std::list<T>` 规定容器操作、迭代器与复杂度，但标准不承诺其内部节点的具体布局。

ECMAScript 定义 JavaScript `Array` 的索引属性、长度和操作行为，并不承诺像 C 数组那样连续存储。引擎可以优化常见数组；以 V8 为例，元素种类可区分 packed（紧凑）和 holey（有空位）等实现状态，这属于 V8 实现，不是 JavaScript 语言对物理布局的承诺。`TypedArray` 则以固定数值元素类型查看 `ArrayBuffer` 的字节范围；它也不能让程序据此推断物理地址或缓存行。

### 其他数据结构也会受访问模式影响

| 对比 | 何时可能改变选择 |
|---|---|
| 线性搜索与二分搜索 | 二分搜索要求输入有序或满足相应单调条件；最坏比较次数随规模按对数增长，线性搜索最坏按规模线性增长。小数组、目标位置、比较成本和缓存状态会改变实际时间。 |
| 行遍历与列遍历 | C 的 row-major（行优先）布局中，按最后一维顺序扫描更连续；跨距读取会改变缓存利用率。 |
| false sharing（伪共享） | 多个 CPU 核心访问同一缓存行，且至少一方写入时，彼此独立的字段也可能引起缓存一致性流量；纯并发读取不构成伪共享。Linux 的 `perf c2c` 可帮助定位受争用的缓存行，再结合结构布局检查对应字段。 |
| PostgreSQL B-tree 与 red-black tree（红黑树） | PostgreSQL 的 B-tree 索引页存放多个索引项，叶页用右兄弟链接支持有序范围扫描；内存中的指针式红黑树逐节点查找。这是 PostgreSQL 的具体布局，不代表所有 B-tree。主导成本可能是存储页、缓存未命中或更新。 |
| 无分支代码与可预测分支 | 去掉分支可能增加无效工作或数据依赖；分支预测稳定时，保留分支也可能更快。 |
| 扁平与节点式哈希表 | 以 Abseil Swiss Tables 为例，扁平表密集组织元数据并分组探测；节点式表将值放入独立节点，较易保持元素地址，但查找需额外间接访问。扩容、删除与引用稳定性也重要。 |
| 结构体填充 | 对齐和字段布局会影响对象大小；应查看目标 ABI 下的 `sizeof` 与成员偏移，再判断是否值得调整。 |
| 增加核心数 | 更多核心可执行更多独立工作，但共享带宽、一致性流量或同步争用可能成为瓶颈。 |

这些比较是定位访问瓶颈的线索，不是脱离负载的通用性能结论。

least recently used（最近最少使用，LRU）缓存常用 Map 按键定位节点，再用双向链表维护新旧顺序；Map 已给出节点、而节点提供前驱和后继时，移到最近使用端只需有限次链接更新。若没有索引而要遍历链表找键，查找仍是 O(n)，指针追逐也没有消失。可继续看[队列、LRU 等数据结构的实际实现](#40.%20%E6%9C%80%E8%BF%91%E6%9C%80%E5%B0%91%E4%BD%BF%E7%94%A8%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E6%8C%89%E9%94%AE%E6%9F%A5%E6%89%BE%E5%B9%B6%E6%9B%B4%E6%96%B0%E6%9C%80%E8%BF%91%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F)。

**相关机制：** [数据结构怎样匹配访问方式，复杂度界何时成立？](#38.%20%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%A6%82%E4%BD%95%E5%8C%B9%E9%85%8D%E8%AE%BF%E9%97%AE%E6%96%B9%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F)说明链表更新所需的前驱与树高条件；[Linux 内核为什么把链表节点嵌入对象？](#49.%20Linux%20%E5%86%85%E6%A0%B8%E4%B8%BA%E4%BB%80%E4%B9%88%E6%8A%8A%E9%93%BE%E8%A1%A8%E8%8A%82%E7%82%B9%E5%B5%8C%E5%85%A5%E5%AF%B9%E8%B1%A1%EF%BC%9F)说明内嵌节点减少了哪种分配，以及为什么它仍然保留指针依赖。

> [!info]- 来源
> - 内存墙的历史背景：[Wulf 与 McKee, Hitting the Memory Wall: Implications of the Obvious（1995）](https://doi.org/10.1145/216585.216588)。
> - C 数组的连续存储、数组下标语义，以及指针加减按元素前进：[WG14 N3220，ISO/IEC 9899:2024 工作草案](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf)，§6.2.5、§6.5.3.2、§6.5.7。
> - 缓存层级、规则访问预取、指针追逐与独立读取重叠：[Intel 64 and IA-32 Architectures Optimization Reference Manual，248966-050US（version 050）](https://cdrdv2-public.intel.com/821612/248966-Optimization-Reference-Manual-V1-050.pdf)，§9.5.2–9.5.4（包括固定步幅指针追逐的示例）；这些微架构说明不是所有 CPU 的固定行为。
> - 简单数组与链表数据局部性的权衡：[Linux 内核 Linked Lists in Linux](https://docs.kernel.org/core-api/list.html)，导言；2026-11-11 核对。
> - 伪共享所需的并发读写条件，以及 `perf c2c` / `pahole` 的定位用途：[Linux 内核 False Sharing](https://docs.kernel.org/kernel-hacking/false-sharing.html)，2026-11-11 核对。
> - `std::vector`（非 `bool`）连续保证与 `std::list` 操作契约：[C++ 工作草案 vector.overview](https://eel.is/c++draft/vector.overview)、[list.overview](https://eel.is/c++draft/list.overview)，2026-11-11 核对。
> - JavaScript 数组的语言级索引语义与 `TypedArray` 对 `ArrayBuffer` 的视图：[ECMAScript 2026 Indexed Collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)，§23.1–23.2；[Structured Data](https://tc39.es/ecma262/2026/multipage/structured-data.html)，§25.1。
> - V8 packed / holey 元素种类：[V8 Elements kinds](https://v8.dev/blog/elements-kinds)，2025-02-28 更新；2026-11-11 核对。
> - PostgreSQL 18 B-tree 的索引页、叶页和有序范围扫描：[B-Tree Indexes](https://www.postgresql.org/docs/18/btree.html)，§65.1.4.1；[REL_18_STABLE 的 nbtree README](https://github.com/postgres/postgres/blob/REL_18_STABLE/src/backend/access/nbtree/README)，扫描部分。该布局说明只适用于 PostgreSQL。
> - 扁平与节点式哈希表的元数据、值布局和地址稳定性：[Abseil Swiss Tables Design Notes](https://abseil.io/about/design/swisstables)，2026-11-11 核对。
## 49. Linux 内核为什么把链表节点嵌入对象？

假设内核要把一个 work item（工作项）放进待处理队列，同时还要把同一对象放进审计队列。Linux 内核的 `struct list_head` 是一对 `next`、`prev` 链接；把它作为成员嵌进工作项，就能让通用链表代码只修改链接，不必为每种关系再分配独立包装节点。

本例中，`ready_items` 与 `audit_items` 本身也是 `struct list_head`，各自充当环形链表的 head（头节点/哨兵）；空表时 head 的两个指针都指向自身。教学地址约定为 A 的基址 `0x1000`、B 的基址 `0x2000`、两个 head 分别为 `0x8000` 和 `0x9000`；因此 A.ready 为 `0x1008`、A.audit 为 `0x1018`，B.ready 为 `0x2008`。链中的指针值指向嵌入的 `list_head` 成员，例如 `0x1008` 是 A 的 `ready_link` 地址，不是外层 A 的起始地址。下图先给出对象布局和成员地址；假设指针为 8 B、`u64` 为 8 B 且结构体无填充，所有地址均为合成值。

![64 位无填充教学模型中 work_item A 的字段地址、成员偏移与 container_of 地址还原](../../engineering-foundations/operating-systems/resources/intrusive-lists-in-linux-object-layout.svg)

### container_of 怎样从钩子找到对象？

Linux 链表节点不是一个含 payload 指针的单独 wrapper。`struct list_head` 本身就放在被链接的结构体内；`container_of(ptr, type, member)` 根据成员偏移，概念上从钩子地址减去 `offsetof(type, member)`，还原出外层对象地址。`list_entry()` 建立在这一机制上，`list_for_each_entry()` 则直接让循环变量指向外层结构体。

~~~c
#include <linux/list.h>
#include <linux/types.h>

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

这要求传入的指针确实指向指定类型中的那个成员；成员名和外层类型必须匹配。`container_of` 做的是地址计算，不会寻找节点，也不消除遍历时读取 `next` 的依赖。它是 Linux 内核提供的宏，不是标准 C 设施；当前 mainline 的 `container_of()` 会丢弃 `const`，新代码应优先使用保留限定符的 `container_of_const()`。链表迭代宏仍使用同一成员偏移关系。

对象入链期间不能改换存放地址：邻接钩子仍会指向旧地址。对已入链对象做浅拷贝也不会把副本加入链表，更不会让邻接节点改指副本。副本逐字段复制原钩子的指针值：例如 A 已入 ready 时，A 的副本会得到 `next=0x2008`、`prev=0x8000`，但 ready 邻居仍指向原 A 的 `ready_link @ 0x1008`。若要独立使用副本，先对副本自己的每个 `list_head` 调用 `INIT_LIST_HEAD`，再分别加入需要的链表。释放原对象前仍要摘掉原对象的全部钩子。

上面的遍历片段是独立示意：`list_for_each_entry` 按 `ready_link` 的成员偏移把每个钩子还原为 `work_item`；走到 `ready_items` head 就停止，所以空表不会进入循环体，head 也不会被当成工作项累加。该片段假设队列在遍历期间不会被并发修改，而且对象始终存活。共享队列的锁定与 A/B 调用顺序见下一个独立示例。

### 插入、遍历和摘除分别改变什么？

下面是独立的内核风格示例：A/B 的 `id` 在对象创建时设好，再初始化两个钩子；之后按 A、B 的顺序尾插 ready，并把 A 插入 audit。两个 head 都用代码中的名字 `ready_items` 和 `audit_items`。调用者必须让传入对象在函数等待互斥锁以及整个调用期间保持存活；锁保护链表和锁内读取，不会替正在等锁的参数保活。

这段 driver 假设两张静态表从空表开始，仅顺序运行这一轮操作，没有其他调用者在步骤之间插入或摘除节点。

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

static bool run_example_once(void)
{
    struct work_item a = { .id = 4 };
    struct work_item b = { .id = 7 };
    u64 before;
    u64 after;

    /* 本次使用新对象；两个新钩子尚未发布，id 已先赋值且示例中保持不变。 */
    init_work_item(&a);
    init_work_item(&b);
    enqueue_ready(&a);
    enqueue_ready(&b);
    record_for_audit(&a);

    before = sum_ready_ids();
    clear_ready_links();
    after = sum_ready_ids();

    /* 此刻 a.ready_link 已摘下，但 a.audit_link 仍挂着；返回前再摘 audit。 */
    mutex_lock(&items_lock);
    list_del_init(&a.audit_link);
    mutex_unlock(&items_lock);

    return before == 11 && after == 0;
}
~~~

调用者在进入 `enqueue_ready(&a)` 之前已经拥有 `a`，并在它取得和释放 `items_lock` 期间一直保留这个对象；若对象可能由别的线程并发销毁，真实接口还需引用计数或等价的所有权协议。`id` 在发布前赋值，示例中不再修改。互斥锁只保证检查和链表更新不会被同一队列的并发操作穿插。

这里的 `list_empty(&item->ready_link)` 利用本例的状态约定：新钩子初始化后自指，已入链钩子则指向相邻项或 head。由于本例的插入和摘除都持有同一把锁，这个检查能避免重复挂入；它不是通用的“该节点属于哪张表”查询。

`run_example_once()` 的 `before` 是 11。`clear_ready_links()` 使用 safe 迭代先摘 A，再摘 B：摘 A 后 ready head 与 B 互相指向，A.ready 自指；摘 B 后 ready head 与 A.ready、B.ready 各自自指，所以 `after` 是 0。清空函数返回时，A.audit 仍接在 audit 环；示例只因随后在同一把锁下也摘掉 A.audit，才可让栈上的 A 离开作用域。

![A 与 B 入队后 ready 和 audit 两个双向环的成员箭头，以及依次摘除 A.ready、B.ready 后的中间与最终状态](../../engineering-foundations/operating-systems/resources/intrusive-lists-in-linux-ring-transitions.svg)

图中每个方框是一个 `list_head`（head 或对象内的钩子）。在多节点环里，蓝色箭头标 `next`，紫色箭头标 `prev`；两节点环里，每个节点的 `next` 与 `prev` 都指向唯一邻居，因此深灰箭头按方向标 `next = prev`。绿色始终表示 head，包括空 ready 环；灰色表示已摘除且自指的钩子。地址写在目标节点旁，可沿箭头核对两项指针字段；A.ready 与 A.audit 是同一个 `work_item A` 内的两个独立成员。

`list_add_tail` 和 `list_del_init` 只需改动固定数量的链接，链表长度不会增加这部分指针操作的数量。但这不是整个操作的耗时保证：调用者可能还要扫描查找节点、取得锁、等待缓存或管理对象本身。`list_del_init` 只把该钩子从队列摘下并重新初始化；它既不释放 `work_item`，也不会摘掉同一对象的 `audit_link`。

`list_for_each_entry_safe` 会在循环体删除当前节点前保存下一游标，因此适合“遍历时删除当前项”；它不保护并发修改，也不能让已保存的下一节点在释放或并发摘除后仍可安全访问。上例用同一把锁保护所有读写；锁的类型与持有范围要符合调用上下文。互斥锁是可睡眠锁，不能用于硬件或软件中断上下文。

### 对象生命周期和并发访问由谁负责？

嵌入链表不会自动管理外层对象的生命周期。释放对象前，需要摘掉所有仍挂入链表的钩子，并确认没有其他读者或引用者还会访问对象。一个工作项在待处理队列中已摘除、但仍留在审计队列时，仍然不能释放。

普通链表操作本身不负责并发安全。多个线程或 CPU 并发修改同一链表时通常要用合适的锁。读多写少时，RCU（read-copy-update，读-复制-更新）可以让读者在 `rcu_read_lock()` 与 `rcu_read_unlock()` 之间用 `list_for_each_entry_rcu()` 遍历，而不持有写者的互斥锁；写者之间仍须用锁或既有协议串行化。Linux RCU 文档的审计规则示例允许读者短暂看到刚删除的规则；若不能接受旧项，内核也展示了用每项 `deleted` 标记和自旋锁拒绝它的做法，因此“容忍陈旧结果”是最简单的 RCU 用法，不是使用 RCU 的唯一条件。

普通清空用 `list_del_init()` 立即把摘下的钩子重置为自指；RCU 清单不能这样做。`list_del_rcu()` 会从当前环中摘除钩子，但保留 `next` 前向链接供已经走到该节点的读者继续前进（当前 mainline 会标记 `prev` 为 poison）。它不会把钩子重置成可再次入链的空钩子，所以在宽限期结束前不能对同一钩子调用 `INIT_LIST_HEAD`、按普通 `list_del_init` 图示自指，或重新插入。`synchronize_rcu()` 会等待先前的读侧临界区结束；`call_rcu()` 只负责登记回调，必须等回调在宽限期后执行，才能回收或复用对象及钩子。若 RCU 版本还要保留本例的 FIFO 尾插顺序，应配对使用 `list_add_tail_rcu()`；`list_add_rcu()` 是插到 head 后面。

RCU 是读侧与生命周期协议，不是把普通 `list_for_each_entry_safe` 换个名字。内核互斥锁是可睡眠锁，不能用于硬件或软件中断上下文。

### 内嵌节点什么时候划算？

当对象由当前模块拥有、地址在入链期间稳定、一个对象需要参加多种频繁更新的关系，且减少独立包装节点的分配和查找有实际价值时，侵入式链表很合适。每种同时存在的关系仍需一个钩子，每个 `list_head` 仍有两个指针；设计并没有消除链接存储成本。

它也不会把对象放到物理连续的内存中。相邻链表节点可能远隔内存，遍历时仍要先取当前节点的 next 指针，再按它到达下一处数据。应把它看作简化关系表示和已知节点更新的办法，不要把它当作解决缓存局部性的办法。主要操作是顺序扫描时，连续数组往往更合适，具体比较见[为什么连续扫描往往比链表遍历快？](#48.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)。

这也不是说所有非侵入式列表都会“给业务对象再包一层指针并分配两次”。C++ 标准规定 `std::list` 的容器语义与操作复杂度，不规定具体节点布局；以 GCC libstdc++ 为例，内部节点把 T 放在节点自带的对齐存储中。那是一个实现样本，不是所有 `std::list` 实现的布局保证。

**相关机制：** [数据结构怎样匹配访问方式，复杂度界何时成立？](#38.%20%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%A6%82%E4%BD%95%E5%8C%B9%E9%85%8D%E8%AE%BF%E9%97%AE%E6%96%B9%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F)说明已知节点与查找前驱的复杂度差别；[内存层次如何改变实际访问成本？](#48.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)比较连续读取与逐节点指针依赖。

> [!info]- 来源
> - 内嵌 `list_head`、`container_of()`、初始化、尾插、遍历和摘除时遍历：[Linux 内核 Linked Lists in Linux](https://docs.kernel.org/core-api/list.html)，Declaring a node / list、Adding nodes、Traversing、Removing nodes、Concurrency considerations；2026-11-11 核对。
> - `list_head { next, prev }` 结构、self-init、`list_add_tail`、`list_del_init` 与 `list_for_each_entry_safe`：[Linux mainline `include/linux/types.h`](https://github.com/torvalds/linux/blob/master/include/linux/types.h)、[`include/linux/list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h)；当前实现，2026-11-11 核对。
> - `container_of()` 的成员类型检查、`offsetof` 地址计算及 `container_of_const()` 的 const 保留：[Linux mainline `include/linux/container_of.h`](https://github.com/torvalds/linux/blob/master/include/linux/container_of.h)；当前实现，2026-11-11 核对。
> - 互斥锁是可睡眠锁及中断上下文限制：[Linux 内核 Generic Mutex Subsystem](https://docs.kernel.org/locking/mutex-design.html)，What are mutexes? / Semantics；2026-11-11 核对。
> - RCU 读者可能看到并发加入/移除的项、写者互相串行化、宽限期后回收及不容忍陈旧项时的每项锁与删除标记：[Linux 内核 Using RCU to Protect Read-Mostly Linked Lists](https://docs.kernel.org/RCU/listRCU.html)，Examples 1、2、4；2026-11-11 核对。
> - `list_add_rcu` 插到 head 后、`list_add_tail_rcu` 尾插；`list_del_rcu` 保留 `next` 供前向 RCU 读者并将 `prev` 标记为 poison，不可立即初始化或复用钩子：[Linux mainline `include/linux/rculist.h`](https://github.com/torvalds/linux/blob/master/include/linux/rculist.h)；当前实现，2026-11-11 核对。
> - `std::list` 标准只规定容器语义与复杂度：[C++ 工作草案 list.overview](https://eel.is/c++draft/list.overview)；GCC 15.2.0 样本的 list node 在节点内用对齐存储保存 T：[libstdc++ `stl_list.h`](https://github.com/gcc-mirror/gcc/blob/releases/gcc-15.2.0/libstdc%2B%2B-v3/include/bits/stl_list.h)。
## 50. 如何让设计原则减少真实的修改成本？

以下用一个完全合成的页面编辑器案例说明：编辑者可以添加标题和按钮节点，编辑器负责校验节点配置、生成画布预览，并保存文档。现在产品提出新增图片节点，规定发布时必须填写非空 alt text（替代文本）。表单尚未填写时仍将字段保留为空字符串，编辑者可以预览并保存草稿；只有发布某个具体修订时，发布门禁才检查这项规则。本例把所有图片都列入这条合成发布政策；真实产品还需区分装饰图，装饰图适合使用空 `alt`。替代文本应随图片用途决定。

假设现有文档格式已能保存新节点的 `type` 与 `props`，不用改存储契约。节点仍保留稳定 `id`、`children`，文档有独立修订号；下面的最小示例只展开展示分发、预览和发布所需字段。若真实存储结构只允许固定类型，新类型也必须纳入存储契约。

设计原则是追踪变化传播的判断工具。先确认本次规则实际会改哪些代码，再看同一次改动是否迫使不相关的调用者、规则或发布单元一起变。抽象只有在它能缩小这种传播、且收益大于新边界的维护成本时才值得保留。

### 单一职责：按共同变化原因聚合

**Single Responsibility Principle (单一职责原则，SRP)** 不是要求一个类只能有一个方法，而是提醒我们不要把会因不同业务要求而变化的规则绑在一起。Robert C. Martin 将它表述为模块只有一个变化理由，并把变化理由连到提出需求的业务方或维护方。

回到编辑器：发布规则可能要求修订中的图片有非空替代文本；设计系统则可能要求画布改变图片圆角和阴影。前者属于指定修订是否可发布的规则，后者属于视觉呈现。如果画布渲染函数也检查发布用的非空 `alt`，未完成的草稿就无法预览；如果保存入口复用发布门禁，草稿也不能保存。按实际变化来源分开草稿结构校验与预览、发布修订的完整性检查，视觉样式改动便不会改变草稿能否编辑或预览。

反过来，不能因为类里有两个名词就机械拆分。若只有一个简单的预览函数，且校验与生成视图总是作为同一次规则变化，拆成数个接口、文件和对象只会增加追踪路径。先列出这次变更由谁提出、哪条保证要同步修改、哪些调用者只依赖其中一部分；只有共同变化的证据出现，职责边界才有依据。

### 开闭：为已知的变化点留扩展位置

**Open/Closed Principle (开闭原则，OCP)** 的目标是让一个相对稳定的模块可以沿已知变化点扩展，尽量不必改动它的核心。它并不要求代码永远不修改，也不能让未预料的需求自动适配。

假设当前渲染入口按 `heading`、`button` 类型分支；新增 `image` 时，这个入口必须再加一个分支。按类型校验也有同样的问题。若“增加组件类型”已成为反复发生的变化，可以把类型定义与校验、渲染行为登记在一个受约束的注册表中。调用方只查找对应定义，不必随着每种类型增加新的中央分支：

注册表为每种类型分别保存 `validateDraft`（草稿检查）、`render`（预览）和 `validatePublish`（发布检查）。统一入口先按 `type` 取定义，再调用当前阶段需要的行为。同一图片节点因此能得到下面两种结果：

| 图片修订 | 草稿检查 | 画布预览与草稿保存 | 发布该修订 |
| --- | --- | --- | --- |
| 13：`alt: ''` | 通过，字段类型完整 | 生成 `<img alt="">` 描述符；文档所有者保存修订 13 | 发布门禁拒绝 13；已发布修订仍为 12 |
| 14：`alt: '页面结构图'` | 通过，字段类型完整 | 预览同一节点的新属性；文档所有者保存修订 14 | 发布门禁接受 14，可切换活动发布版本 |

> [!example]- 注册表如何同时服务草稿预览、保存和发布
>
> ~~~javascript
> const definitions = new Map([
>   ['heading', {
>     validateDraft: node => (
>       typeof node.props.text === 'string' &&
>       Number.isInteger(node.props.level) && node.props.level >= 1 && node.props.level <= 6
>     ),
>     validatePublish: () => true,
>     render: node => ({ tag: 'h' + node.props.level, text: node.props.text }),
>   }],
>   ['button', {
>     validateDraft: node => typeof node.props.label === 'string',
>     validatePublish: () => true,
>     render: node => ({ tag: 'button', text: node.props.label }),
>   }],
>   ['image', {
>     validateDraft: node => (
>       typeof node.props.src === 'string' && typeof node.props.alt === 'string'
>     ),
>     validatePublish: node => node.props.alt.trim().length > 0,
>     render: node => ({ tag: 'img', src: node.props.src, alt: node.props.alt }),
>   }],
> ]);
>
> function definitionFor(node) {
>   if (
>     !node || typeof node !== 'object' || typeof node.id !== 'string' ||
>     typeof node.type !== 'string' || !node.props || typeof node.props !== 'object' ||
>     Array.isArray(node.props) || !Array.isArray(node.children)
>   ) throw new TypeError('invalid node structure');
>
>   const definition = definitions.get(node.type);
>   if (!definition) throw new RangeError('unsupported component type');
>   if (!definition.validateDraft(node)) throw new TypeError('invalid draft node');
>   return definition;
> }
>
> function renderNode(node) {
>   return definitionFor(node).render(node);
> }
>
> function commitDraft(document, node) {
>   definitionFor(node);
>   return {
>     ...document,
>     revision: document.revision + 1,
>     nodes: [...document.nodes, node],
>   };
> }
>
> function saveDraft(document, drafts) {
>   for (const node of document.nodes) definitionFor(node);
>   drafts.set(document.revision, document);
>   return document.revision;
> }
>
> let publishedRevision = 12;
> function publishRevision(revision, drafts) {
>   const document = drafts.get(revision);
>   if (!document) throw new RangeError('draft revision not found');
>   for (const node of document.nodes) {
>     const definition = definitionFor(node);
>     if (!definition.validatePublish(node)) throw new TypeError('publication requirements not met');
>   }
>   publishedRevision = revision;
>   return publishedRevision;
> }
>
> const revision12 = {
>   revision: 12,
>   nodes: [
>     { id: 'heading-1', type: 'heading', props: { text: '首页', level: 1 }, children: [] },
>     { id: 'button-1', type: 'button', props: { label: '报名' }, children: [] },
>   ],
> };
> const imageDraft = {
>   id: 'image-1', type: 'image',
>   props: { src: '/media/diagram.png', alt: '' }, children: [],
> };
> const drafts = new Map();
> const revision13 = commitDraft(revision12, imageDraft);
> const savedRevision13 = saveDraft(revision13, drafts);
> const preview13 = renderNode(imageDraft);
> let publicationError;
> try {
>   publishRevision(13, drafts);
> } catch (error) {
>   publicationError = error.name;
> }
> console.log(JSON.stringify({
>   preview13, savedRevision13, publicationError, publishedRevision,
> }));
>
> const completedImage = {
>   ...imageDraft,
>   props: { ...imageDraft.props, alt: '页面结构图' },
> };
> const revision14 = {
>   ...revision13,
>   revision: 14,
>   nodes: revision13.nodes.map(node => node.id === completedImage.id ? completedImage : node),
> };
> const savedRevision14 = saveDraft(revision14, drafts);
> const preview14 = renderNode(completedImage);
> const acceptedRevision = publishRevision(14, drafts);
> console.log(JSON.stringify({ preview14, savedRevision14, publishedRevision: acceptedRevision }));
> ~~~

`definitionFor` 先确认节点形状与编辑期契约。新增图片只需登记草稿字段规则、预览描述符与发布条件；统一的画布渲染、修订保存和发布遍历都从同一注册表读取定义，不必再增加 `image` 分支。登记仍是代码变更；OCP 的收益是避免修改所有既有调用路径。

草稿结构要求 `alt` 是字符串，因此表单未填写时存为 `''`，而不是缺少字段。`renderNode` 只执行草稿结构检查并返回可预览的 `<img>` 描述符；文档所有者把它保存为修订 13。发布者按修订号读取已保存的 13，再运行发布门禁，所以空 `alt` 会阻止公开，而不会撤销草稿保存。填写替代文本产生修订 14，预览与保存继续成功，发布检查才允许将活动发布修订推进到 14。代码输出中修订 13 的 `publishedRevision` 仍为 12。`drafts` 只是演示按修订读写的内存 Map；本例修改时新建对象，保存后不再改写旧对象。Map 自身不会复制或冻结对象，真实版本保存还需由文档持久化层落实。

本例为突出类型分发而把 `nodes` 写成数组；完整的根节点顺序、ID 索引、样式及树约束见[页面文档和发布快照的数据模型](#53.%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E9%A1%B5%E9%9D%A2%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)。真实服务端仍应对发布请求重新检查其权威修订与输入，不依赖浏览器的即时检查。

如果只有一两个稳定类型，`switch` 通常更直观。注册表也有维护成本：类型、校验器与渲染器必须保持一致，错误处理和注册时机也需要约定。等到类型变更在多个入口重复扩散，再引入边界通常比提前设计插件系统更有证据。

### 里氏替换：子类型不能改变调用者依赖的行为

**Liskov Substitution Principle (里氏替换原则，LSP)** 讨论的是行为契约，而不只是继承关系或相同的方法名。若调用者依赖 `NodeRenderer.render(node)` 对每个满足已登记类型草稿契约的节点（包括未发布草稿）都能同步返回预览描述符，那么子类型也必须满足这份保证。

假设画布按同步的 `NodeRenderer.render(node)` 契约工作，现有实现 `DefaultNodeRenderer` 能为合法远程图片返回预览描述符。若把传给画布的实现换成它的子类型 `ImagePreviewRenderer`，而该子类型要求调用者先下载图片并对同一合法输入抛出“暂不支持”，画布便无法安全地用子类型替代原实现。这个子类型收紧了调用者的前置条件，违反了原契约。若当前仍要求同步返回，图片子类型可以返回 `<img>` 描述符，让画布或浏览器继续加载资源；若产品必须等待加载结果，就要共同修改 `render` 契约为异步结果，并让现有调用者处理加载状态，不能只在子类型里悄悄改变行为。

判断替换关系时，列清前置条件、后置保证、错误结果和状态不变量：子类型不能要求调用者额外准备条件，也不能撤回基类已经承诺的结果。Liskov 与 Wing 的形式化定义把这些可观察行为与类型不变量一并纳入；它帮助识别“看起来像一种节点、实际却不能安全替换”的设计。

### 接口隔离与依赖倒置：按调用者需要定义契约

**Interface Segregation Principle (接口隔离原则，ISP)** 针对调用者被迫依赖自己不用的能力。画布只需把节点渲染成视图；发布流程需要校验文档并持久化；如果两者都依赖一个同时含编辑、渲染、校验、存储和发布方法的大接口，任何一方的变化都可能拉动另一方重新编译、测试或部署。

可以按稳定的调用角色拆分契约，例如让画布依赖 `NodeRenderer`，让发布流程依赖 `DocumentValidator` 与 `DocumentWriter`。这不等于为每个类和每个调用点都新建专属接口；Martin 特别提醒接口也可能切得过细，造成数量和关系难以维护。

**Dependency Inversion Principle (依赖倒置原则，DIP)** 解决的是依赖箭头：发布模块定义自己需要的 `DocumentWriter` 契约，数据库适配器引用并实现它；运行时的组合入口把适配器交给发布流程，发布流程仍只调用 `writer.write(revision)`。依赖方向因此从数据库细节指向发布模块的契约，而不是发布策略直接依赖具体数据库驱动。

**dependency injection (依赖注入)** 可以把 `DocumentWriter` 传给发布流程，但它只是传递依赖的方式，不等于依赖倒置本身。若文档只写入一个很简单的内存对象，既无替换需求，也无测试隔离收益，再包几层接口并不会自动让设计更好。

### DRY、KISS 与 YAGNI 如何约束抽象？

DRY (Don't Repeat Yourself，不重复同一知识)要消除的是同一知识被多处独立维护的风险，不是让长得相似的代码必须合并。标题文本和按钮标签都恰好是字符串，却代表不同配置；把它们合成一个含糊的 `text` 字段可能让调用者更难判断含义。相反，如果“哪些节点可以发布”的同一政策被编辑预览与发布流程各自维护，两个列表就可能逐渐不一致，应找出真正的政策所有者或共同契约。用户端即时提示与服务端权威校验即使内容相似，也可能需要分别执行，因为它们处在不同信任边界。Hunt 与 Thomas 将 DRY 定义为让每份知识在系统中只有一个清楚且权威的表示；如果需求变更必须在多个位置以不同形式同步更新，就出现了重复知识。

KISS (Keep It Simple，保持简单)要求方案与当前变化规模相称。YAGNI (You Aren't Gonna Need It，尚未需要的能力先不实现)提醒我们不要仅凭假想的插件需求预建多层接口。若添加一种固定节点只需一条清楚的分支，直接写分支更易维护；如果同类需求已反复要求同时修改创建、校验和渲染入口，再把这些变化收拢到可验证的扩展点。

### 用变化案例决定边界

现在沿同一图片节点走一遍。草稿结构要求 `alt` 字段存在且是字符串；空字符串可以预览并保存。发布服务按明确修订读取草稿，再检查这项合成产品规则：本例要求每张图片发布时 `alt` 非空。

这条路径中，失败的是针对修订 13 的发布请求，不是编辑提交、画布渲染或草稿保存。浏览器中的即时提示只帮助编辑者尽早发现问题；发布服务仍需对选定修订权威校验，不能信任客户端已运行的检查。`alt` 规则仅为本例政策：装饰图或与邻近文本重复的图片可以用空 `alt`，真实产品应依据图片用途定义发布条件。

谁把通过草稿检查的插入请求提交为新修订？由文档所有者负责，编辑会话只表达变更意图；修订、撤销、保存和发布快照见[页面文档和发布快照的数据模型](#53.%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E9%A1%B5%E9%9D%A2%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)，状态由谁持有见[前端架构怎样划分呈现、交互和数据所有权？](#51.%20%E5%89%8D%E7%AB%AF%E6%9E%B6%E6%9E%84%E6%80%8E%E6%A0%B7%E5%88%92%E5%88%86%E5%91%88%E7%8E%B0%E3%80%81%E4%BA%A4%E4%BA%92%E5%92%8C%E6%95%B0%E6%8D%AE%E6%89%80%E6%9C%89%E6%9D%83%EF%BC%9F)。[页面编辑器何时需要设计模式？](#52.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E4%BD%95%E6%97%B6%E9%9C%80%E8%A6%81%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%EF%BC%9F)再展示工厂、策略和观察者如何落实创建、校验与通知边界。

是否采用注册表，取决于变化轨迹：第一次新增类型且只有一处调用时，直接分支更简单；若多个类型连续要求改动同一批入口，注册表会让校验和渲染扩展集中。继续观察每次新增是否真只需一条定义、是否把一致性问题转移到了注册表和类型声明；当扩展机制本身开始变复杂，就应重新评估边界。

> [!info]- 来源
> - **SRP 的变化理由。** Robert C. Martin, “The Single Responsibility Principle,” 2014-05-08，讨论 Parnas 的变化决策封装和按变化请求来源划分模块：[原文](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html)，尤其是 “What defines a reason to change?” 至结尾。
> - **OCP、LSP、DIP 与 ISP。** Robert C. Martin, “Design Principles and Design Patterns,” 2000，OCP pp. 4–8、LSP pp. 8–12、DIP pp. 12–14、ISP pp. 14–16：[原文 PDF](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。文中把这些原则应用到页面编辑器的注册表、存储边界和调用者契约，是本章的合成工程案例。
> - **行为子类型。** Barbara H. Liskov 与 Jeannette M. Wing, “A Behavioral Notion of Subtyping,” *ACM Transactions on Programming Languages and Systems*, 16(6), 1994, pp. 1811–1841；第 5.2 节的不变量、方法前后置条件与约束规则：[论文 PDF](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf)。
> - **DRY。** Andy Hunt 与 Dave Thomas, *The Pragmatic Programmer: Your Journey to Mastery*, 20th Anniversary Edition, 第 9 节 “The Evils of Duplication”；DRY 要求每份知识在系统中有单一、清楚且权威的表示：[节选 PDF](https://media.pragprog.com/titles/tpp20/dry.pdf)。
> - **客户端与服务端校验。** OWASP *Input Validation Cheat Sheet* 的 “Client-only checks” 指出客户端检查适合即时反馈，但可被绕过；服务端仍须执行权威校验：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)。
> - **装饰图片替代文本。** W3C WAI 的 alt 决策树指出，装饰图或与邻近文字重复的图片可以使用空 `alt`；本例的非空发布规则是产品假设而非通用无障碍要求：[原文](https://www.w3.org/WAI/tutorials/images/decision-tree/)。
> - **YAGNI。** Martin Fowler 将 YAGNI 描述为暂不实现尚未需要的功能，并提醒未使用的扩展点会增加当前复杂度：[原文](https://martinfowler.com/bliki/Yagni.html)。
## 51. 前端架构怎样划分呈现、交互和数据所有权？

以一个合成的页面编辑器为例：资产 `42` 当前是 revision (修订) 12，`section-1` 下有标题 `heading-1` 和报名按钮 `button-1`。为看清树关系，本篇将两个组件放进一个合成分组节点；关键是稳定 ID (标识符)、父子关系与修订边界，而不是这个容器类型。画布显示文档树，检查器修改当前节点，编辑预览读取当前草稿，访客读取已发布页面。架构要回答三件事：哪份状态可保存、谁能提交文档变更、哪些视图消费同一份结果。保存草稿不会发布；发布服务只在编辑者明确请求后校验选定的已保存修订，通过后才切换公开快照。

| 状态 | 初始值 | 生命周期 | 所有者 |
|---|---|---|---|
| 页面文档 | `revision=12`、`rootIds=['section-1']`、`section-1.children=['heading-1','button-1']` | 可保存、可撤销、可作为预览输入 | 文档状态所有者 |
| 编辑会话 | `selectedId=null`、`openPanel='inspector'`、`dragPreview=null` | 当前编辑器会话；不进入页面文档 | 编辑会话状态所有者 |
| 组件局部状态 | 输入焦点、光标与尚未确认的输入缓冲 | 当前组件挂载期间 | 对应输入组件 |
| 公开页面 | 活动指针为 `r12`，指向已发布的不可变快照 | 多个草稿修订并存时仍保持原发布版 | 发布服务与快照存储 |

完整的节点对象、命令、撤销和发布代码见[怎样建模页面文档、编辑会话和发布快照？](#53.%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E9%A1%B5%E9%9D%A2%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)。下面先追一次编辑如何改变文档，再看已保存修订怎样成为公开页面，最后讨论组件、模块与部署边界。

### 单向数据流让修改原因可追踪

**unidirectional data flow (单向数据流)** 让状态所有者把当前数据交给视图，视图通过事件或命令请求变化。检查器不能私下改写自己保存的节点副本；它应发出“把 `heading-1` 的 `text` 改成‘欢迎’”这样的意图，由文档所有者检查并产生新修订。若命令未通过校验，错误返回给发起方，当前文档修订保持不变。

下图的实线表示提交与后续显示，虚线表示读取已有状态。每次只处理一个命令；先改标题得到修订 13，再确认排序得到修订 14，具体值在图后的表中展开。

~~~mermaid
flowchart TD
    Input["用户确认修改<br/>setText / move"] --> Owner["文档所有者<br/>校验命令"]
    Current["当前文档修订"] -.->|作为校验依据| Owner
    Owner -->|通过| New["提交新修订<br/>标题：12 → 13<br/>排序：13 → 14"]
    Owner -->|拒绝| Error["返回错误<br/>文档修订不变"]
    New --> Views["画布 / 检查器<br/>读取当前文档"]
    New --> Preview["编辑预览<br/>只读取当前文档"]
    Session["编辑会话<br/>selectedId<br/>dragPreview"] -.->|辅助界面显示| Views
~~~

同一个修订 12 案例中，选择、输入、拖动预览和已提交修改走不同路径：

| 用户动作 | 会话或组件状态 | 文档结果 |
|---|---|---|
| 选中 `heading-1` | `selectedId` 变成 `heading-1` | 仍为修订 12，标题还是“首页” |
| 在检查器输入但未确认 | 输入组件暂存 `textDraft='欢迎'`，光标留在组件中 | 仍为修订 12 |
| 确认标题文案 | 发出 `setText('heading-1', '欢迎')` 命令 | 所有者校验后提交修订 13 |
| 拖动标题越过按钮 | `dragPreview` 记录 `section-1` 内候选顺序 | 仍为修订 13，树顺序不变 |
| 在画布放下并确认 | 发出移动命令；成功后清除 `dragPreview` | 所有者提交修订 14，子节点顺序变成 `['button-1','heading-1']` |

鼠标移动只改变会话里的候选位置。只有放下后才把命令交给文档所有者，因此撤销历史和保存任务不会记录几十次无意义的指针坐标。画布和检查器随后都从修订 14 读取，而不是分别维护一份副本。撤销也由文档所有者处理；它恢复先前的内容，但仍产生一个新的单调递增修订号，详见数据模型章节。

React 的状态共享指南以“把要协调的状态移动到最近共同父组件”解释了同一所有权思路；它不意味着所有状态都要搬到一个全局对象。其他框架可用不同机制，只要选中项、草稿输入与已提交文档的持有者仍清楚可辨。若浏览器端只是草稿缓存，服务端在保存时还要检查当前修订或版本条件，避免较旧客户端覆盖较新的提交；这一步属于持久化合同，不应由视图自行假定成功。

**从草稿到公开页面。** 编辑者可以保存修订 14，访客此时仍读取活动快照 r12。只有编辑者另外请求发布该已保存修订，发布服务才开始校验；通过后生成不可变快照，再原子切换活动指针。校验拒绝时，已保存草稿和线上页面仍是两份不同状态。

~~~mermaid
flowchart TD
    Saved["已保存 r14<br/>活动快照 r12"] -->|编辑者明确请求发布| Gate{"发布校验"}
    Gate -->|通过| Snapshot["生成不可变快照<br/>r14"]
    Snapshot --> Switch["原子切换<br/>活动指针到 r14"]
    Switch --> Public["访客读取 r14"]
    Gate -->|拒绝| Keep["不切换指针<br/>访客仍读取 r12"]
~~~

### 组件与分层分别解决什么问题？

**component-based architecture (基于组件的架构)** 按可复用视图和交互边界拆分 user interface (用户界面，UI)。`Canvas` 呈现文档树，`Inspector` 编辑选中节点的属性，`NodeView` 呈现一种节点类型。组件接口应说明数据和回调怎样传入，以及选择、修改、删除等意图怎样传出。视图不因被拆成组件就自动得到文档所有权。

分层则按职责分开交互状态、文档命令、持久化适配和视图。这个合成编辑器可先用少数模块：会话控制器持有 `selectedId` 与 `dragPreview`；文档所有者接受命令、校验结构与业务规则、产生修订；存储适配器保存一个指定修订；视图读取会话和文档投影。只有某层确实承载独立规则或依赖边界，才值得拆成独立包或服务。为每个组件都造“控制器—服务—仓库”会增加跨层跳转，却未必减少变化范围。

文档树的逻辑顺序也不等于最终绘制顺序。浏览器会依 CSS stacking context (层叠上下文) 和定位规则绘制；编辑器若要提供“置顶”，必须说明改的是树的兄弟顺序、同一层叠上下文内的层级，还是更高层渲染模型。单独重排 `children` 不保证节点覆盖另一个不同层叠上下文中的元素。

### 何时微前端有实际收益？

**micro-frontend (微前端)** 把前端的一部分按业务或团队边界独立开发、集成和发布。可以在构建时组合、运行时加载，也可以用 iframe 或 Web Components；它们在隔离、依赖共享、导航和样式方面各有成本。

若画布、检查器和资产面板由同一团队一起发布，放在一个模块化应用通常更直接；当前主要问题若是两处各存节点副本，拆成微前端只会把同步问题推到跨应用通信。若组件库、页面编辑器和资产管理由不同团队负责，确有独立发布节奏且集成合同稳定，拆分才可能减少发布协调。与此同时，运行时集成会增加路由、深链、身份传递、样式隔离、依赖版本、可访问性、故障处理和监控等合同；这些成本必须由独立发布带来的收益抵消。

微前端是组织与部署边界，不是把普通组件拆成多个项目的同义词。先解决文档状态由谁持有，再判断是否存在团队自治、独立部署或渐进迁移的实际需求。

### 怎样迁移微前端而不打断深链、身份与回退？

现在从单应用切换到另一种合成部署情境：资产 42 当前仍为修订 12，旧入口 `/editor/assets/42?panel=inspector&node=heading-1#canvas` 要逐步迁到 `/assets/42/edit?panel=inspector&node=heading-1#canvas`。文档字段不变；`node=heading-1` 是可恢复的界面选择，不是文档内容，也不会推进 `revision`。新旧地址先并存，避免旧书签和历史项没有去向。

shell (应用外壳) 可以负责顶级路由、公共导航和错误边界。路由注册表先把两种地址都交给 `EditorV1`，再让 cohort (灰度分组) 中的一小部分用户把新地址路由到 `EditorV2`。这是一个合同选择：也可以让子应用共享同一个路由器或由构建入口组合，但不可让两个互不知情的路由器同时争抢浏览器历史。

| 地址或事件 | 外壳的路由选择 | 子应用输入 |
|---|---|---|
| 旧深链 | 迁移窗口内继续交给 V1 | `assetId=42`、`panel=inspector`、`node=heading-1`、`#canvas` |
| 新地址，未进 cohort | 先交给 V1，不呈现空白占位页 | 同一资源与视图状态 |
| 新地址，进入 cohort | 加载 V2，显示加载或失败状态 | 同一资源与视图状态 |
| 直接打开或刷新 | 完整 URL 匹配后等待所选子应用挂载 | 从 query 恢复选择；目标挂载后按 `#canvas` 定位 |
| Back / Forward | 根据浏览器恢复的完整 URL 重新匹配路由 | 从 query 恢复选择，并在目标挂载后恢复 URL fragment (片段) 定位 |

V1 与 V2 都应声明同一个 `id="canvas"` 目标。直接打开或刷新时，外壳先选定子应用，编辑器等目标节点随视图挂载后，再读取当前 `location.hash` 并定位到目标；不能假定异步加载的画布在浏览器首次处理 fragment 时已经存在。`pushState()` 和 `replaceState()` 只更新历史项和 URL，不会触发浏览器的 fragment 定位，所以发起导航的路由所有者应在视图挂载后调用同一恢复逻辑。Back / Forward 触发 `popstate` 后，应用重新读取完整 URL、恢复选择，并在目标挂载后定位。迁移验收要分别断言 `#canvas` 保留在 URL 中，以及画布确实进入视口；只检查 hash 不足以证明深链可用。

浏览器 History API (历史记录接口) 中，`pushState()` 会新增一条历史项，适合用户主动从旧入口进入新入口；`replaceState()` 替换当前历史项，适合旧路径已成为别名、且不希望 Back 在两个等价地址间循环时使用。应用在历史遍历时响应 `popstate` 并重新读取 URL；发起 `pushState()` 导航的路由所有者也要同步更新自身状态。改写旧路径时保留 query 与 fragment；服务端还要让前端深链回退到 shell HTML，同时继续把 `/api/` 交给 API (应用程序接口) 服务。

每个子应用通过明确的 `navigate()` 或同源链接请求跨边界导航。选中的 `node` 在文档加载后才与该修订的稳定节点 ID 对照；若节点不存在，就清除选择并显示页面，不把参数当成任意资源读取入口。

身份也要在部署边界定义。本例外壳使用同源会话 cookie，设置 `HttpOnly`、`Secure` 与适用的 `SameSite` 属性；给子应用传 `assetId`、非敏感显示数据和受限的数据访问接口，不把会话凭据放入路由、DOM 或共享状态广播。浏览器发出的资源读取与写入仍由服务端逐次验证当前主体是否获准访问该资产。客户端“能否显示该路由”不代替授权；服务端拒绝应以拒绝结果呈现，不要误判成代码加载失败再静默切换到另一版。本例 V1 与 V2 都在 shell 的同一页面运行，仍处在同一浏览器文档信任边界；仅从不同 origin 加载脚本不构成隔离。若子应用运行在另一 origin 的独立文档或 iframe 中，则需要单独设计跨源消息、身份、cookie 属性与 API 访问；它与同一页面加载远程脚本的边界不同。

V1 和 V2 在迁移初期读取、写入相同版本的文档格式。若 V2 将来写入 V1 不认识的新字段，只有 V1 会原样保留它，或路由能确保旧版不再打开这些文档，才可开放；仅忽略未知字段可能让 V1 下次保存时把字段删除。删除或改变字段含义，也要等旧版不再负责读写。若 V2 加载失败发生在用户开始编辑之前，可安全把新地址映射回 V1；编辑开始之后若已有未保存草稿，就先转换并交接草稿，或留在当前编辑器给出错误，不能静默切回并丢失用户修改。

发布按路由逐步改变处理者：先验证 shell 可加载两版并保持同一输入合同；再把新地址的一小组 cohort 交给 V2；检查直接深链与刷新时 hash 保留和画布定位、query、Back / Forward、未授权请求、V2 代码块加载失败、V1/V2 文档兼容与草稿保留，再扩大分流。若 V2 的错误率越过预设门槛，将新地址重新交给 V1。有效回退还要求 V1 代码仍可加载，且 V1 兼容当前数据格式。只有把流量开关拨回去、却没有旧代码或兼容格式，并不能恢复服务。

路由格式是跨应用通信合同，改路径或参数时要更新所有链接来源和消费者。页面构建资源的版本并存与回滚见[构建工具怎样把源码变成可发布产物？](../../frontend/tooling/build-tools.md)；服务端读写仍遵循[如何设计可预期的 HTTP API 契约？](#3.%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F)。

**延伸阅读：** [如何让设计原则减少真实的修改成本？](#50.%20%E5%A6%82%E4%BD%95%E8%AE%A9%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99%E5%87%8F%E5%B0%91%E7%9C%9F%E5%AE%9E%E7%9A%84%E4%BF%AE%E6%94%B9%E6%88%90%E6%9C%AC%EF%BC%9F)、[页面编辑器何时需要设计模式？](#52.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E4%BD%95%E6%97%B6%E9%9C%80%E8%A6%81%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%EF%BC%9F)、[怎样建模页面文档、编辑会话和发布快照？](#53.%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E9%A1%B5%E9%9D%A2%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)。

> [!info]- 来源
> - **共享状态的所有权。** React，“Sharing State Between Components”，状态上提与每份状态唯一所有者：[原文](https://react.dev/learn/sharing-state-between-components)，2026-11-12 核对。
> - **绘制顺序。** W3C CSS 2.2，Appendix E “Elaborate description of Stacking Contexts”，绘制顺序和层叠上下文：[原文](https://www.w3.org/TR/CSS22/zindex.html)，2026-11-12 核对。
> - **独立团队发布的收益与集成成本。** Cam Jackson, “Micro Frontends,” 2019-06-19，Benefits、Integration approaches、Downsides 与 Operational and governance complexity：[原文](https://martinfowler.com/articles/micro-frontends.html)。
> - **路由作为跨应用通信合同。** 同上，“Cross-application communication via routing”：[原文](https://martinfowler.com/articles/micro-frontends.html#Crossapplicationcommunicationviarouting)。
> - **浏览器历史行为。** WHATWG HTML Living Standard，§7.2.5 “The `History` interface” 中 `pushState()`、`replaceState()` 与历史遍历：[原文](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，2026-11-12 核对。
> - **片段定位。** WHATWG HTML Living Standard，“Scrolling to a fragment” 规定 fragment 对应文档中的定位目标；异步子应用须在目标挂载后恢复定位：[原文](https://html.spec.whatwg.org/multipage/browsing-the-web.html#scrolling-to-a-fragment)，2026-11-12 核对。
> - **会话 cookie 属性。** OWASP Session Management Cheat Sheet，`Secure`、`HttpOnly` 与 `SameSite` 说明：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)，2026-11-12 核对。
> - **客户端反馈与服务端校验。** OWASP Input Validation Cheat Sheet，“Client-only checks”：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)，2026-11-12 核对。
> - **跨应用运行时与授权边界。** OWASP Micro Frontend Security Cheat Sheet，“Choose and Enforce Runtime Boundaries”说明远程脚本仍使用宿主页面权限、跨源 iframe 才建立 origin 边界；“Authorize Every Request on the Server”要求每次后端请求重新授权：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Micro_Frontend_Security_Cheat_Sheet.html)，2026-11-12 核对。
## 52. 页面编辑器何时需要设计模式？

案例使用一份合成的页面编辑器文档：当前修订为 12，已有 `heading-1` 和 `button-1`；编辑者从工具栏插入标题，画布与检查器都要看到新修订。**design pattern（设计模式）**给反复出现的对象协作方式命名，但模式不会替系统决定谁拥有文档、哪些规则只在发布时检查，或订阅何时结束。**GoF（Gang of Four，四人帮）**原著也把适用情境、约束、结果和取舍作为模式说明的一部分，并以文档编辑器作案例；它不是可机械套用的类图。

先找出哪种变化正在重复。如果一次普通函数调用或稳定的条件分支已经让修改范围清楚，多加对象、注册步骤和清理责任只会增加跳转。下面三个 JavaScript 代码块按出现顺序在同一模块中运行；工厂产出的 `heading` 会直接交给策略和状态所有者。

### 创建规则变多时，用工厂集中入口

工具栏、粘贴和快捷键都能创建标题。若每个入口都各自填写默认属性、分配 ID（标识符），节点形状会逐渐不一致。此时 **factory（工厂）**适合集中这些创建规则；最初通常只是一个函数。

~~~javascript
const defaults = new Map([
  ['heading', { text: '', level: 2 }],
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
console.log(JSON.stringify(heading));
try {
  createNode('constructor');
} catch (error) {
  console.log(error.name);
}
~~~

这段程序输出一个 `node-1` 标题草稿，文本初始为空、层级为 2；`createNode('constructor')` 输出 `RangeError`。空文本是编辑期默认值，后续策略会检查字段类型和层级，但不把发布要求塞进节点创建。`Map` 只接受显式注册的组件类型，因此不会把对象原型上的同名属性误当作可创建类型。若整个页面只有一处创建固定对象，直接写对象字面量更清楚。

这里的计数器只在本次运行中分配不重复的安全整数。刷新、跨窗口协作或多个写入者并发时，它不能保证全局唯一；持久化系统需由文档状态或专门的 ID 方案处理。对象创建后若未通过后续编辑校验，计数器也可能留下空号，这不影响唯一性。这个简单函数也不是 GoF 中的 **Factory Method（工厂方法）**或 **Abstract Factory（抽象工厂）**：前者让子类决定实例化哪个类，后者创建相关对象族；本例没有这类变化需求。

### 行为可互换时，用策略

当组件类型各自有不同的编辑期结构规则，而且新增规则需要避免挤进一个不断增长的条件块时，可以把校验行为放进类型对应的函数。**strategy（策略）**让调用方通过同一契约使用这些可替换的算法。

~~~javascript
const editableValidators = new Map([
  ['heading', node => {
    const errors = [];
    if (typeof node.props.text !== 'string') errors.push('标题文本必须是字符串');
    if (!Number.isInteger(node.props.level) || node.props.level < 1 || node.props.level > 6) {
      errors.push('标题层级必须是 1 到 6 的整数');
    }
    return errors;
  }],
  ['button', node => (
    typeof node.props.label === 'string' ? [] : ['按钮标签必须是字符串']
  )],
]);

function validateEditableNode(node) {
  const validate = editableValidators.get(node.type);
  return validate ? validate(node) : ['未知组件类型：' + node.type];
}

function previewDraftNode(node) {
  const errors = validateEditableNode(node);
  if (errors.length > 0) throw new TypeError('invalid draft node');
  return { type: node.type, props: { ...node.props } };
}

const invalidHeading = {
  ...heading,
  props: { ...heading.props, level: 8 },
};
console.log(JSON.stringify({
  headingErrors: validateEditableNode(heading),
  invalidHeadingErrors: validateEditableNode(invalidHeading),
  preview: previewDraftNode(heading),
}));
~~~

输出中空标题的编辑错误列表是 `[]`，同一 `node-1` 的 8 级变体返回 `['标题层级必须是 1 到 6 的整数']`；预览保留空文本和 2 级结构。状态所有者会直接调用 `validateEditableNode(node)`，而不是信任调用者另传一个错误列表。来自服务器或外部文件的节点，还要先通过通用结构解析；这里的策略只校验已解析节点的类型特有字段，也不负责授权。

编辑合法性与发布门槛必须由不同流程负责。当前空标题可保存为草稿并预览；本例的产品发布规则另要求标题非空，后面会让发布入口针对某个修订检查它。若类型和规则数量很少且稳定，`switch` 更直接；只有变化确实分散时，策略注册才值得承担额外维护。

### 多个视图订阅同一修订时，用观察者

插入命令传入前两节构造并校验过的同一个 `heading`。状态所有者在拒绝错误节点或接受合法草稿时都会自行调用策略；只有无错误时才创建修订并提交，再把已提交文档交给通知器。画布与检查器因此读到同一修订。**observer（观察者）**让状态主体管理多个接收者；文档仍由状态所有者持有，通知器只持有订阅。

![标题插入先经工厂和编辑策略；有效节点才提交新修订，错误分支保留原修订](../../engineering-foundations/architecture/resources/design-patterns-in-practice-node-insertion.svg)

> [!example]- 状态提交、通知快照与指定修订的发布实现
>
> ~~~javascript
> class DocumentNotifier {
>   #listeners = new Set();
>
>   subscribe(listener) {
>     this.#listeners.add(listener);
>     return () => this.#listeners.delete(listener);
>   }
>
>   notify(document) {
>     const listeners = [...this.#listeners];
>     for (const listener of listeners) listener(document);
>   }
> }
>
> function freezeNode(node) {
>   return Object.freeze({
>     ...node,
>     props: Object.freeze({ ...node.props }),
>     children: Object.freeze([...node.children]),
>   });
> }
>
> function freezeDocument(document) {
>   return Object.freeze({
>     ...document,
>     nodes: Object.freeze(document.nodes.map(freezeNode)),
>   });
> }
>
> const state = {
>   current: freezeDocument({
>     revision: 12,
>     nodes: [
>       { id: 'heading-1', type: 'heading', props: { text: '首页', level: 1 }, children: [] },
>       { id: 'button-1', type: 'button', props: { label: '报名' }, children: [] },
>     ],
>   }),
> };
> const revisions = new Map([[12, state.current]]);
> const notifier = new DocumentNotifier();
> const received = [];
> const unsubscribeCanvas = notifier.subscribe(doc => received.push('canvas r' + doc.revision));
> const unsubscribeInspector = notifier.subscribe(doc => received.push('inspector r' + doc.revision));
> let notifying = false;
> let publishedRevision = 12;
>
> function commitEditableNode(node) {
>   if (notifying) return { ok: false, errors: ['通知期间不能同步提交编辑'] };
>   const errors = validateEditableNode(node);
>   if (errors.length > 0) return { ok: false, errors };
>
>   const exists = state.current.nodes.some(existing => existing.id === node.id);
>   const nodes = exists
>     ? state.current.nodes.map(existing => existing.id === node.id ? node : existing)
>     : [...state.current.nodes, node];
>   const next = freezeDocument({
>     ...state.current,
>     revision: state.current.revision + 1,
>     nodes,
>   });
>   state.current = next;
>   revisions.set(next.revision, next);
>
>   notifying = true;
>   try {
>     notifier.notify(next);
>   } finally {
>     notifying = false;
>   }
>   return { ok: true, revision: next.revision, nodeId: node.id };
> }
>
> function publishRevision(revision) {
>   const document = revisions.get(revision);
>   if (!document) throw new RangeError('draft revision not found');
>   for (const node of document.nodes) {
>     const errors = validateEditableNode(node);
>     if (errors.length > 0) return { ok: false, errors, publishedRevision };
>     if (node.type === 'heading' && node.props.text.trim().length === 0) {
>       return { ok: false, error: '标题发布时不能为空', publishedRevision };
>     }
>   }
>   publishedRevision = revision;
>   return { ok: true, publishedRevision };
> }
>
> console.log(JSON.stringify(commitEditableNode(invalidHeading)));
> console.log(JSON.stringify({ revision: state.current.revision, notifications: received.length }));
> console.log(JSON.stringify(commitEditableNode(heading)));
> console.log(JSON.stringify({
>   preview: previewDraftNode(state.current.nodes.find(node => node.id === heading.id)),
>   revision: state.current.revision,
>   notifications: received.join(', '),
> }));
> console.log(JSON.stringify(publishRevision(13)));
>
> const savedHeading13 = state.current.nodes.find(node => node.id === heading.id);
> const completedHeading = {
>   ...savedHeading13,
>   props: { ...savedHeading13.props, text: '首页标题' },
> };
> console.log(JSON.stringify(commitEditableNode(completedHeading)));
> console.log(JSON.stringify(publishRevision(14)));
> console.log(JSON.stringify({ notifications: received.join(', ') }));
> unsubscribeCanvas();
> unsubscribeInspector();
> ~~~

这段顺序执行的程序先以 8 级标题尝试提交：策略实际返回错误，状态仍是 revision 12，通知数为 0。工厂生成的空标题通过编辑校验，文档所有者才将它提交为 revision 13；画布得到预览描述符，画布和检查器都收到 `r13`。发布流程读取确切的 revision 13，因标题为空而拒绝，公开版本仍是 12。填写同一 `node-1` 后，状态所有者提交 revision 14，两个视图收到 `r14`，发布门禁再允许活动公开版本切换到 14。此处用活动修订号表示发布结果；实际不可变快照的创建与切换由相邻数据模型章节展开。

通知接收者列表在 `notify()` 开始时复制，因此本轮新增或取消订阅只影响后续通知；若回调在本轮中取消别人的订阅，该人仍会收到本轮已排定的通知。副本只固定接收者集合，不会保护文档内容。这里通过不可变更新和 `Object.freeze` 复制并冻结文档、节点、属性与子节点数组；画布和检查器只读修订。同步通知期间再次提交会被状态所有者拒绝，避免嵌套提交导致检查器先看到 `r14`、再看到旧的 `r13`。这段简化代码的属性是字符串和数字，实际含嵌套可变值时也要按其结构复制冻结或采用其他不可变约定。

一个监听器若抛错，异常会向提交调用者传播并停止当前快照中的后续监听器；文档修订已经在通知前提交，`finally` 会解除同步提交保护。若每个视图都必须收到通知，可在通知边界另行定义错误隔离或重试；这会改变当前错误语义，不必为本例另造事件队列。

![通知器把同一不可变修订送给画布和检查器；视图卸载时取消订阅](../../engineering-foundations/architecture/resources/design-patterns-in-practice-observer-lifecycle.svg)

订阅随视图生命周期结束：卸载时调用返回的取消函数。`Set` 本身按插入顺序保存不同监听器；本文使用快照，ECMAScript 的实时迭代规则只解释为何没有复制时删除下一位会跳过它、而新增项可能加入本轮。具体规则见来源条目中的 §§24.2.4.4、24.2.4.17–18 和 24.2.6.1。

浏览器的 `EventTarget` 也让对象直接管理监听器，并支持注册与移除；它是直接观察者式 API 的类比，但还有事件捕获、冒泡和取消语义。页面级事件分发细节见[浏览器怎样查询、更新 DOM 并响应用户输入？](../../frontend/browser-apis/dom-manipulation-and-events.md)；应用层消息总线与监听器重入见[JavaScript 事件总线在监听器中重入时怎样保持顺序？](../../frontend/browser-apis/event-bus-and-observer-patterns.md)。

**publish-subscribe（发布订阅）**把消息按主题交给中介路由；发布者只知道主题，不必知道具体接收者。例如中介可持有 `Map<topic, Set<listener>>`，订阅者收到返回的取消函数后从相同主题集合中移除自己。若多个独立插件要监听 `document:saved`，这种路由可能减少直接引用；但主题字符串和跨模块调用也会让消息来源更难追踪。画布和检查器天然属于这份文档，直接订阅文档通知器更容易沿着对象找到依赖；父子组件只有一个回调时，普通回调就够了。有多个接收者也不意味着必须创建全局事件总线。

### 共享实例有明确范围时，才用单例

若一个编辑器运行时要求所有面板使用同一份组件注册表，必须先说明“一份”指哪个范围。**singleton（单例）**组合了唯一实例与全局访问点；它不能自动保证浏览器所有标签、worker（工作线程）、进程或重复模块副本共享同一对象。

多数编辑器只需由每个应用组合入口创建一个 `EditorRuntime`，再把注册表传给画布、检查器和命令处理器。这样一个应用范围内确实共享同一实例，但测试可以独立创建另一个运行时。JavaScript 模块变量只在该模块实例范围共享；它不等于一个页面只有一个编辑器，更不保证不同模块副本共用实例。全局单例则隐藏依赖，容易让两个编辑器实例或不同测试相互污染。如果类的构造器仍公开，`getInstance()` 访问器也不能阻止调用方 `new` 出额外对象。只有全局访问点本身能解决明确问题时才承担这种耦合；否则显式创建和传递更容易观察生命周期。

### 用设计原则检查模式是否合适

沿着“插入空标题”流程检查责任边界：工厂只负责节点初值与 ID；编辑期策略负责节点结构；状态所有者对策略结果作决定并提交修订；观察者只通知已提交的只读状态；发布服务另行检查指定修订能否成为公开版本。发布失败不会撤销可以保存、预览和继续编辑的草稿。

添加一种新节点类型时，开发者可能仍要修改类型定义、渲染器和发布规则。工厂或策略不会自动兑现开闭原则；只有新变化能在局部扩展，并且调用契约仍稳定，修改范围才真的缩小。观察者省去逐个调用视图的依赖，但订阅清理、文档只读和错误传播仍需明确。上层流程依赖通知契约、下层通知器实现该契约，是依赖倒置的一种接法；模式应配合变化边界，而非成为新的清单。

本篇沿合成 revision 12 插入空标题走到 revision 13；[页面文档和发布快照的数据模型](#53.%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E9%A1%B5%E9%9D%A2%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)则从 revision 12 另行把 `heading-1` 文案从“首页”改为“欢迎”，得到它自己的 revision 13。两次操作是各自独立的教学路径，不表示同一文档连续从 revision 13 改到 revision 13。本篇用 `nodes` 数组聚焦对象协作，完整案例以 `rootIds` 和按 ID 索引的节点表保存文档树；撤销、持久化和发布快照契约见数据模型章节。组件数据由哪些前端对象拥有见[前端架构边界](#51.%20%E5%89%8D%E7%AB%AF%E6%9E%B6%E6%9E%84%E6%80%8E%E6%A0%B7%E5%88%92%E5%88%86%E5%91%88%E7%8E%B0%E3%80%81%E4%BA%A4%E4%BA%92%E5%92%8C%E6%95%B0%E6%8D%AE%E6%89%80%E6%9C%89%E6%9D%83%EF%BC%9F)。

> [!info]- 来源
> - GoF 对模式适用情境、约束、结果与权衡的说明，及文档编辑器案例：[Gamma、Helm、Johnson、Vlissides, *Design Patterns: Elements of Reusable Object-Oriented Software*](https://www.oreilly.com/library/view/design-patterns-elements/0201633612/)。
> - `Set` 删除、默认值迭代入口与迭代器行为：[ECMAScript 2026, Keyed Collections, §§24.2.4.4、24.2.4.17–18、24.2.6.1](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-set-iterator-objects)，2026-11-12 核对。
> - `EventTarget` 的监听列表、注册、移除与事件分发：[WHATWG DOM Standard, §§2.7、2.9](https://dom.spec.whatwg.org/#interface-eventtarget)，2026-11-12 核对。
> - 设计原则与模式的关系：[Robert C. Martin, “Design Principles and Design Patterns” (2000), p. 4](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。
## 53. 怎样建模页面文档、编辑会话和发布快照？

回到前端架构篇的合成页面编辑器起点：资产 42 的页面当前是 revision (修订) 12，访客也从修订 12 的初始快照读取页面。文档里有标题 `heading-1` 和报名按钮 `button-1`。本篇继续用 `section-1` 根节点容纳它们，专门展示父子关系；其他编辑行为沿用同一组稳定 ID (标识符)。编辑者修改标题、重排组件、撤销、保存草稿，并发布审核后的版本。要避免选择或拖动时误写页面，也要让访客明确看到哪个已校验的修订。

三个生命周期分别是：可保存的页面文档、当前编辑会话里的临时状态、从某个文档修订及固定渲染依赖派生的公开快照。

### 文档树和编辑会话记录不同事实

文档保存页面事实：稳定节点 ID (标识符)、组件类型、属性、子节点和顶层顺序。会话保存当前选择、面板和拖动中的候选位置。代码用 `section-1` 作根节点，标题和按钮是它的两个孩子；根 ID 与子节点 ID 分开存放，所以重排兄弟节点只改 `section-1.children`，不必把节点对象从 ID 表里挪来挪去。

~~~javascript
const documentState = {
  schemaVersion: 1,
  revision: 12,
  rootIds: ['section-1'],
  nodes: {
    'section-1': {
      id: 'section-1', type: 'section',
      props: { label: '首页内容' }, children: ['heading-1', 'button-1'],
    },
    'heading-1': {
      id: 'heading-1', type: 'heading',
      props: { text: '首页', level: 1 }, children: [],
      style: { position: 'absolute', top: 100, left: 200 },
    },
    'button-1': {
      id: 'button-1', type: 'button',
      props: {
        label: '报名',
        action: { kind: 'navigate', pageId: 'form' },
      },
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

`rootIds` 表示顶层节点及其顺序；`nodes` 按 ID 索引，便于通过 `heading-1` 定位并局部更新。已提交树采用森林规则：根 ID 不重复，根节点不能同时是孩子；每条父子边只出现一次，每个非根节点只有一个父节点；所有节点能从某个根到达，且没有环。只检查 ID 唯一、引用存在和无环还不够：两个父节点可能同时引用同一个孩子，文档也可能留下无法从根到达的孤儿节点。若产品允许未挂入树中的新节点草稿，可暂存在会话里，提交前才要求完整树满足这些约束；本例没有实现新建节点流程。

较小编辑器也可用嵌套树，避免过早规范化，但仍要保持单父与根归属规则。示例不把光标或 `selectedId` 存进页面：切换选择不推进文档修订、不进入撤销历史，也不影响发布输出。这里选择把 `style` 类布局属性放进文档，因为产品要保存布局；若某种样式只服务于拖动中的临时预览，就应跟 `dragPreview` 一起留在会话。可保存和临时状态的边界取决于产品语义，而不是字段名。

### 稳定身份与命令使修改可追踪

数组下标会因插入和排序改变，不适合作为长期节点身份。稳定 ID 让检查器、历史记录和协作消息指向同一个节点。**command (命令)** 把用户意图表达成可验证操作，例如更新标题文本或移动一个兄弟节点；调用方不能直接修改状态所有者持有的对象。

先停在标题已经改成“欢迎”的 r13，看一次拖动还未提交时的状态。图中“标题”和“按钮”分别是 `heading-1` 与 `button-1`，两者始终属于 `section-1`。

~~~mermaid
flowchart TD
    Doc["文档 r13<br/>标题 → 按钮<br/>撤销深度 1"] -.->|读取已提交内容| View["画布临时投影<br/>按钮 → 标题"]
    Drag["会话 dragPreview<br/>候选：按钮 → 标题"] -.->|只替换本次显示顺序| View
    Drag -->|取消| Cancel["清空候选<br/>文档仍 r13<br/>撤销深度仍 1"]
    Drag -->|松手确认| Command["提交移动命令<br/>相同节点 ID<br/>moveSiblingAfter"]
    Command -->|结构校验通过| R14["文档 r14<br/>按钮 → 标题<br/>撤销深度 2<br/>清空候选"]
~~~

画布的临时投影不会写回文档。取消时清空候选，显示回到 r13 的文档顺序；确认时才由命令生成 r14。若移动命令被拒绝，文档与撤销栈都不变，候选仍留在会话里供处理。下面的表从最初 r12 继续到保存与发布，补齐每一步的状态。


| 用户动作 | 会话与画布 | 文档、历史和访客 |
|---|---|---|
| 初始页面 | `selectedId=null`、`dragPreview=null`；画布顺序为标题、按钮 | 文档 r12，`children=['heading-1','button-1']`；访客活动快照 r12 |
| 确认标题“欢迎” | 输入组件提交 `setText` | 文档到 r13，`heading-1` ID 不变；撤销历史增加一项，访客仍读 r12 |
| 选择标题 | `selectedId='heading-1'` | 文档仍 r13；撤销历史不变 |
| 拖到按钮后方，尚未松手 | `dragPreview` 保存 `section-1`、`heading-1`、`button-1` 和候选顺序；画布暂时按候选顺序预览 | 文档 children 仍是 `['heading-1','button-1']`，仍 r13；历史不变，访客仍读 r12 |
| 取消拖动 | 清空 `dragPreview`，画布回到文档顺序 | 文档 r13、历史和活动快照均不变 |
| 再拖一次并松手确认 | 用 `moveSiblingAfter('section-1','heading-1','button-1')` 提交相同 ID；成功后清空候选 | 文档到 r14，`children=['button-1','heading-1']`；历史增加一项，访客仍读 r12 |
| 撤销后重做 | 会话选择仍指向 `heading-1` | r15 恢复原顺序，r16 恢复重排；两个动作都新增修订，访客仍读 r12 |
| 保存 r16 | 保存该确切修订 | `savedDrafts` 保存 r16；活动快照仍 r12 |
| 明确请求发布 r16 | 发布服务重新校验已保存的 r16 | 通过后才原子切换活动指针 r12→r16，访客读取 r16 |
| 清空标题并提交 | 文档到 r17，活动快照仍为 r16 | 标题为空；撤销历史增加一项，已保存与已发布的 r16 不变 |
| 预览 r17 | 画布显示空标题 | 只读草稿，不改文档、历史或活动快照 |
| 保存 r17 | 保存该确切修订 | 活动快照仍 r16，访客仍读“欢迎” |
| 明确请求发布 r17 | 发布服务重新校验已保存的 r17 | 非空标题规则拒绝；活动快照和访客仍为 r16 |

下面的完整实现按顺序使用上方可见的初始输入。接受的文档命令、撤销和重做会生成新的单调修订号；选择、拖动和取消不会增加修订或修改撤销栈。

> [!example]- 完整可运行实现（需和上面的初始输入一起运行）
> 本实现使用上节可见的 `documentState` 与 `editorSession`。按页面顺序拼接两个 JavaScript 围栏运行；只复制本折叠围栏会缺少初始输入。
>
> ~~~javascript
> function clone(value) {
>   return structuredClone(value);
> }
>
> function freezeDeep(value) {
>   if (value && typeof value === 'object' && !Object.isFrozen(value)) {
>     for (const child of Object.values(value)) freezeDeep(child);
>     Object.freeze(value);
>   }
>   return value;
> }
>
> function validateDocument(document) {
>   const errors = [];
>   if (!document || typeof document !== 'object' || Array.isArray(document)) {
>     return ['document must be an object'];
>   }
>   if (document.schemaVersion !== 1) errors.push('unsupported schemaVersion');
>   if (!Number.isSafeInteger(document.revision) || document.revision < 0) {
>     errors.push('revision must be a non-negative safe integer');
>   }
>   if (!Array.isArray(document.rootIds)) errors.push('rootIds must be an array');
>   if (!document.nodes || typeof document.nodes !== 'object' || Array.isArray(document.nodes)) {
>     errors.push('nodes must be an ID map');
>   }
>   if (errors.length) return errors;
>
>   const ids = Object.keys(document.nodes);
>   const roots = document.rootIds;
>   const rootSet = new Set();
>   for (const id of roots) {
>     if (typeof id !== 'string') {
>       errors.push('rootIds must contain only string IDs');
>       continue;
>     }
>     if (rootSet.has(id)) errors.push('rootIds contains duplicates');
>     rootSet.add(id);
>     if (!Object.hasOwn(document.nodes, id)) {
>       errors.push('rootIds contains an unknown node');
>     }
>   }
>
>   const parents = new Map(ids.map(id => [id, 0]));
>   for (const [key, node] of Object.entries(document.nodes)) {
>     if (!node || typeof node !== 'object') {
>       errors.push(`node ${key} must be an object`);
>       continue;
>     }
>     if (node.id !== key) errors.push(`node key and id differ for ${key}`);
>     if (!Array.isArray(node.children)) {
>       errors.push(`children of ${key} must be an array`);
>       continue;
>     }
>     if (node.style !== undefined) {
>       if (!node.style || typeof node.style !== 'object' || Array.isArray(node.style)) {
>         errors.push(`style of ${key} must be an object`);
>       } else {
>         const allowedStyleKeys = new Set(['position', 'top', 'left']);
>         if (Object.keys(node.style).some(styleKey => !allowedStyleKeys.has(styleKey))) {
>           errors.push(`style of ${key} has an unknown property`);
>         }
>         if (!['absolute', 'relative'].includes(node.style.position)) {
>           errors.push(`style position of ${key} must be absolute or relative`);
>         }
>         for (const coordinate of ['top', 'left']) {
>           if (node.style[coordinate] !== undefined && !Number.isFinite(node.style[coordinate])) {
>             errors.push(`${coordinate} of ${key} must be finite`);
>           }
>         }
>       }
>     }
>     if (node.type === 'section') {
>       if (typeof node.props?.label !== 'string') errors.push(`section ${key} needs a string label`);
>     } else if (node.type === 'heading') {
>       if (typeof node.props?.text !== 'string') errors.push(`heading ${key} needs string text`);
>       if (!Number.isInteger(node.props?.level) || node.props.level < 1 || node.props.level > 6) {
>         errors.push(`heading ${key} level must be an integer from 1 to 6`);
>       }
>       if (node.children.length) errors.push(`heading ${key} cannot have children`);
>     } else if (node.type === 'button') {
>       if (typeof node.props?.label !== 'string') errors.push(`button ${key} needs a string label`);
>       if (node.props?.action?.kind !== 'navigate' || typeof node.props?.action?.pageId !== 'string') {
>         errors.push(`button ${key} needs a navigate action with pageId`);
>       }
>       if (node.children.length) errors.push(`button ${key} cannot have children`);
>     } else {
>       errors.push(`unknown component type for ${key}`);
>     }
>
>     const childSet = new Set();
>     for (const childId of node.children) {
>       if (typeof childId !== 'string') {
>         errors.push(`children of ${key} must contain only string IDs`);
>         continue;
>       }
>       if (childSet.has(childId)) errors.push(`${key} lists child ${childId} more than once`);
>       childSet.add(childId);
>       if (!parents.has(childId)) {
>         errors.push(`${key} refers to unknown child ${childId}`);
>       } else {
>         parents.set(childId, parents.get(childId) + 1);
>       }
>     }
>   }
>
>   for (const id of ids) {
>     const count = parents.get(id);
>     if (count > 1) errors.push(`node ${id} has more than one parent`);
>     if (rootSet.has(id) && count !== 0) errors.push(`root ${id} is also a child`);
>     if (!rootSet.has(id) && count === 0) errors.push(`node ${id} is neither root nor child`);
>   }
>
>   const colors = new Map();
>   function visitForCycle(id) {
>     if (!Object.hasOwn(document.nodes, id)) return;
>     const node = document.nodes[id];
>     if (!node || typeof node !== 'object') return;
>     if (colors.get(id) === 'gray') {
>       errors.push(`cycle reaches node ${id}`);
>       return;
>     }
>     if (colors.get(id) === 'black') return;
>     colors.set(id, 'gray');
>     const children = node.children;
>     if (Array.isArray(children)) {
>       for (const child of children) {
>         if (typeof child === 'string') visitForCycle(child);
>       }
>     }
>     colors.set(id, 'black');
>   }
>   for (const id of ids) visitForCycle(id);
>
>   const reachable = new Set();
>   function visitFromRoot(id) {
>     if (reachable.has(id) || !Object.hasOwn(document.nodes, id)) return;
>     const node = document.nodes[id];
>     if (!node || typeof node !== 'object') return;
>     reachable.add(id);
>     const children = node.children;
>     if (Array.isArray(children)) {
>       for (const child of children) {
>         if (typeof child === 'string') visitFromRoot(child);
>       }
>     }
>   }
>   for (const id of roots) {
>     if (typeof id === 'string') visitFromRoot(id);
>   }
>   for (const id of ids) {
>     if (!reachable.has(id)) errors.push(`node ${id} is unreachable from rootIds`);
>   }
>   return [...new Set(errors)];
> }
>
> let current = freezeDeep(clone(documentState));
> if (validateDocument(current).length) throw new TypeError('invalid initial document');
> const initialPublished = freezeDeep({
>   documentId: 'asset-42',
>   revision: current.revision,
>   schemaVersion: current.schemaVersion,
>   componentRegistryVersion: 'components-v1',
>   rendererVersion: 'renderer-v1',
>   document: clone(current),
> });
> let activeSnapshot = initialPublished;
> const revisions = new Map([[current.revision, current]]);
> const savedDrafts = new Map([[current.revision, current]]);
> const past = [];
> const future = [];
>
> function commit(candidate, label, historyMode = 'command') {
>   const next = clone(candidate);
>   next.revision = current.revision + 1;
>   const errors = validateDocument(next);
>   if (errors.length) return { ok: false, label, errors, revision: current.revision };
>
>   if (historyMode === 'command') {
>     past.push(clone(current));
>     future.length = 0;
>   }
>   current = freezeDeep(next);
>   revisions.set(current.revision, current);
>   return { ok: true, label, revision: current.revision };
> }
>
> function updateHeadingText(id, text) {
>   if (typeof id !== 'string') {
>     return { ok: false, errors: ['node ID must be a string'], revision: current.revision };
>   }
>   if (typeof text !== 'string') return { ok: false, errors: ['text must be a string'], revision: current.revision };
>   const node = current.nodes[id];
>   if (!node || node.type !== 'heading') {
>     return { ok: false, errors: ['heading does not exist'], revision: current.revision };
>   }
>   const next = clone(current);
>   next.nodes[id].props.text = text;
>   return commit(next, `setText(${id})`);
> }
>
> function selectNode(id) {
>   if (typeof id !== 'string' || !Object.hasOwn(current.nodes, id)) {
>     return { ok: false, errors: ['selected node ID must name an existing node'], revision: current.revision };
>   }
>   editorSession.selectedId = id;
>   return { ok: true, selectedId: id, revision: current.revision };
> }
>
> function reorderedSiblingIds(parentId, movingId, afterId) {
>   if (![parentId, movingId, afterId].every(id => typeof id === 'string')) {
>     return { ok: false, errors: ['move IDs must be strings'] };
>   }
>   const parent = current.nodes[parentId];
>   if (!parent || parent.type !== 'section') {
>     return { ok: false, errors: ['section does not exist'] };
>   }
>   const siblings = [...parent.children];
>   if (movingId === afterId || !siblings.includes(movingId) || !siblings.includes(afterId)) {
>     return { ok: false, errors: ['move requires two distinct current siblings'] };
>   }
>   const remaining = siblings.filter(id => id !== movingId);
>   const afterIndex = remaining.indexOf(afterId);
>   remaining.splice(afterIndex + 1, 0, movingId);
>   return { ok: true, children: remaining };
> }
>
> function startDrag(parentId, movingId, afterId) {
>   if (typeof movingId !== 'string' || editorSession.selectedId !== movingId) {
>     return { ok: false, errors: ['select the node before dragging it'], revision: current.revision };
>   }
>   const plan = reorderedSiblingIds(parentId, movingId, afterId);
>   if (!plan.ok) return { ...plan, revision: current.revision };
>   editorSession.dragPreview = { parentId, movingId, afterId, children: plan.children };
>   return { ok: true, dragPreview: clone(editorSession.dragPreview), revision: current.revision };
> }
>
> function cancelDrag() {
>   if (!editorSession.dragPreview) {
>     return { ok: false, errors: ['there is no drag preview to cancel'], revision: current.revision };
>   }
>   editorSession.dragPreview = null;
>   return { ok: true, cancelled: true, revision: current.revision };
> }
>
> function moveSiblingAfter(parentId, movingId, afterId) {
>   const plan = reorderedSiblingIds(parentId, movingId, afterId);
>   if (!plan.ok) return { ...plan, revision: current.revision };
>   const next = clone(current);
>   next.nodes[parentId].children = plan.children;
>   const result = commit(next, `move(${movingId}, after ${afterId})`);
>   if (result.ok) editorSession.dragPreview = null;
>   return result;
> }
>
> function dropDragPreview() {
>   const candidate = editorSession.dragPreview;
>   if (!candidate) {
>     return { ok: false, errors: ['there is no drag preview to commit'], revision: current.revision };
>   }
>   return moveSiblingAfter(candidate.parentId, candidate.movingId, candidate.afterId);
> }
>
> function undo() {
>   if (!past.length) return { ok: false, errors: ['nothing to undo'], revision: current.revision };
>   const target = past.pop();
>   future.push(clone(current));
>   return commit(target, 'undo', 'history');
> }
>
> function redo() {
>   if (!future.length) return { ok: false, errors: ['nothing to redo'], revision: current.revision };
>   const target = future.pop();
>   past.push(clone(current));
>   return commit(target, 'redo', 'history');
> }
>
> function preview(document, session = {}) {
>   const visible = [];
>   function visit(id) {
>     const node = document.nodes[id];
>     if (node.type === 'section') {
>       const order = session.dragPreview?.parentId === id
>         ? session.dragPreview.children
>         : node.children;
>       for (const childId of order) visit(childId);
>     } else if (node.type === 'heading') {
>       visible.push(`heading:${node.props.text}`);
>     } else if (node.type === 'button') {
>       visible.push(`button:${node.props.label}`);
>     }
>   }
>   for (const rootId of document.rootIds) visit(rootId);
>   return visible;
> }
>
> function saveDraft(revision) {
>   const document = revisions.get(revision);
>   if (!document) return { ok: false, error: 'revision not found' };
>   const errors = validateDocument(document);
>   if (errors.length) return { ok: false, errors };
>   savedDrafts.set(revision, freezeDeep(clone(document)));
>   return { ok: true, savedRevision: revision };
> }
>
> function publishRevision(revision) {
>   const document = savedDrafts.get(revision);
>   if (!document) return { ok: false, error: 'publish requires a saved revision', activeRevision: activeSnapshot.revision };
>   const errors = validateDocument(document);
>   if (errors.length) return { ok: false, errors, activeRevision: activeSnapshot.revision };
>   const emptyHeading = Object.values(document.nodes).find(
>     node => node.type === 'heading' && node.props.text.trim().length === 0,
>   );
>   if (emptyHeading) {
>     return { ok: false, error: `heading ${emptyHeading.id} must not be empty at publish`, activeRevision: activeSnapshot.revision };
>   }
>
>   const nextSnapshot = freezeDeep({
>     documentId: 'asset-42',
>     revision,
>     schemaVersion: document.schemaVersion,
>     componentRegistryVersion: 'components-v1',
>     rendererVersion: 'renderer-v1',
>     document: clone(document),
>   });
>   activeSnapshot = nextSnapshot;
>   return { ok: true, publishedRevision: activeSnapshot.revision };
> }
>
> function makeInvalidSharedChildExample() {
>   const invalid = clone(current);
>   invalid.nodes['section-2'] = {
>     id: 'section-2', type: 'section', props: { label: '重复引用' }, children: ['heading-1'],
>   };
>   invalid.rootIds.push('section-2');
>   return validateDocument(invalid);
> }
>
> function makeInvalidCycleExample() {
>   const invalid = clone(current);
>   invalid.nodes['heading-1'].children = ['section-1'];
>   return validateDocument(invalid);
> }
>
> function makeMalformedIdExamples() {
>   const badRoot = clone(documentState);
>   badRoot.rootIds = [{ toString: 0 }];
>   const badChild = clone(documentState);
>   badChild.nodes['section-1'].children = [{ toString: 0 }];
>   return {
>     rootErrors: validateDocument(badRoot),
>     childErrors: validateDocument(badChild),
>   };
> }
>
> function probeTree(mutator) {
>   const candidate = clone(documentState);
>   mutator(candidate);
>   return validateDocument(candidate);
> }
>
> function editorState() {
>   return {
>     selectedId: editorSession.selectedId,
>     dragPreview: clone(editorSession.dragPreview),
>     revision: current.revision,
>     children: [...current.nodes['section-1'].children],
>     undoDepth: past.length,
>     redoDepth: future.length,
>     activeRevision: activeSnapshot.revision,
>   };
> }
>
> console.log(JSON.stringify({
>   initialTreeErrors: validateDocument(current),
>   sharedChildErrors: makeInvalidSharedChildExample(),
>   cycleErrors: makeInvalidCycleExample(),
>   malformedIdErrors: makeMalformedIdExamples(),
> }));
> console.log(JSON.stringify(updateHeadingText('heading-1', '欢迎'))); // revision 13
> console.log(JSON.stringify({ selection: selectNode('heading-1'), state: editorState() }));
> console.log(JSON.stringify({
>   drag: startDrag('section-1', 'heading-1', 'button-1'),
>   canvas: preview(current, editorSession),
>   state: editorState(),
> }));
> console.log(JSON.stringify({
>   cancel: cancelDrag(),
>   canvas: preview(current, editorSession),
>   state: editorState(),
> }));
> console.log(JSON.stringify(startDrag('section-1', 'heading-1', 'button-1')));
> console.log(JSON.stringify({ drop: dropDragPreview(), canvas: preview(current, editorSession), state: editorState() })); // revision 14
> console.log(JSON.stringify(undo())); // revision 15, original order
> console.log(JSON.stringify(redo())); // revision 16, moved order restored
> console.log(JSON.stringify({ state: editorState(), canvas: preview(current, editorSession) }));
> console.log(JSON.stringify({ save: saveDraft(16), activeRevisionAfterSave: activeSnapshot.revision }));
> console.log(JSON.stringify({
>   publishRequest: 16,
>   result: publishRevision(16),
>   activeRevision: activeSnapshot.revision,
> }));
> console.log(JSON.stringify(updateHeadingText('heading-1', ''))); // revision 17
> console.log(JSON.stringify({
>   preview: preview(current),
>   save: saveDraft(17),
>   publishRequest: 17,
>   publish: publishRevision(17),
>   activeRevision: activeSnapshot.revision,
>   publicTitle: activeSnapshot.document.nodes['heading-1'].props.text,
> }));
>
> for (const [branch, mutate] of [
>   ['duplicate-root', doc => doc.rootIds.push('section-1')],
>   ['orphan-node', doc => { doc.nodes['orphan-1'] = { id: 'orphan-1', type: 'section', props: { label: '孤儿' }, children: [] }; }],
>   ['dangling-child', doc => doc.nodes['section-1'].children.push('missing-1')],
>   ['prototype-like-child', doc => doc.nodes['section-1'].children.push('constructor')],
>   ['duplicate-edge', doc => doc.nodes['section-1'].children.push('heading-1')],
>   ['invalid-child-list', doc => { doc.nodes['heading-1'].children = null; }],
>   ['invalid-heading-level', doc => { doc.nodes['heading-1'].props.level = 8; }],
> ]) {
>   console.log(JSON.stringify({ branch, errors: probeTree(mutate) }));
> }
> ~~~

完整实现还验证了多父节点、环、重复根、孤儿、悬空引用和非法字段类型。两个分组同时引用 `heading-1` 会得到多父错误；`rootIds` 或 `children` 中出现对象而非字符串 ID 时，返回结构错误列表。

本例用整份内容快照保存 `past` 与 `future`，实现直观但会随历史长度和文档大小占用更多存储。逆命令或操作日志可减少重复内容，却必须为移动、删除和之后发生的变更正确定义反向操作；协作写入还要说明操作针对哪个基线。示例中的 `style` 是明确选择持久化的布局属性；若它只记录拖动中尚未确认的位置，就应放进会话而不是文档。

在本例中，`past` 与 `future` 保存可恢复的文档内容；每次恢复仍从当前最大修订号加一，所以撤销不会改写过去已保存的修订。保存 16 把确切修订副本放入 `savedDrafts`，但不会切换活动指针；只有显式请求发布 16 且门禁通过，访客才改读 r16。之后填写空标题并提交得到 r17，不会污染已保存的 16；r17 也不能覆盖已发布的 r16。撤销历史只在当前编辑会话中，保存档案与发布快照有独立生命周期；应用重启后恢复撤销能力需要另行持久化历史或命令日志。普通编辑预览调用 `preview(document)`，始终按文档顺序遍历；画布调用 `preview(document, editorSession)`，在拖动期间临时使用 `dragPreview.children` 生成画布描述。两种调用都不改文档，也不模拟浏览器布局或截图渲染。

代码用 `structuredClone` 与深度冻结表达状态所有者不把可变内部对象直接交给视图。快照值限于 JSON 形状；实际框架可以用不可变数据结构、序列化边界或受控更新实现同样的隔离。代码只模拟单个编辑会话，不包含两个编辑器同时写入时的版本比较，因此不能用它推断并发保存已经安全。示例里 `activeSnapshot` 的一次同步赋值只标出切换边界；多进程服务需要用数据库事务或等效的原子更新来切换持久化指针。

### `schema`（结构描述）描述形状，业务规则解释含义

组件注册表可为每种类型提供配置形状、渲染器和校验器。JSON Schema 2020-12 的 `type`、`required`、数组和数值约束可表达很多 JSON 结构条件；上面的 `validateDocument` 展示了跨节点关系，例如树必须只有一个父节点、所有节点要从根可达。这类整体图约束还要由应用代码或专门扩展实现。引用目标是否存在、用户是否有权操作、发布是否允许空标题，也属于结构类型以外的产品和服务端规则。

持久化载入时先解析结构并返回能定位到节点的错误；编辑命令再检查状态变更；发布服务对选定修订重新做结构、引用、权限与资源确认。浏览器里的即时校验能更早提示，但不能替代可信边界上的校验。渲染器也不应把无效节点静默隐藏成空白页，否则读者无法区分“内容本来为空”和“数据已损坏”。本例的编辑规则允许标题文本为空字符串，发布规则另要求非空；空标题可预览和保存，但发布该修订会失败。这个非空条件只是本例产品政策，不是通用页面文档规则。

### 文档顺序不等于全部绘制顺序

`section-1.children` 的顺序可以决定组件在图层面板中的逻辑顺序，但浏览器绘制还受 Cascading Style Sheets (层叠样式表，CSS) 定位、`z-index` 和 **stacking context (层叠上下文)** 影响。本例重排两个同级子节点只改变树顺序；若某组件创建了独立层叠上下文，把它在数组里移到另一个节点后面，不保证视觉上覆盖另一个上下文中的元素。若产品提供“置顶”或“置底”，需明确它改变的是树顺序、同一层叠上下文内的绘制级别，还是另一个独立渲染模型。

### 发布绑定确切修订，避免混入未校验草稿

发布服务先选出具体保存修订，再检查结构与组件属性、引用目标、当前用户权限和需要的外部资源，全部通过后才生成公开版本。草稿修订 17 为空标题时，本例发布入口拒绝它，`activeSnapshot` 仍指向修订 16；访客不会突然看到未通过发布规则的修订。产品可以设计不同的“保存即发布”流程，但要清楚哪些校验在编辑期、保存期和发布期执行，不能让同一条规则在一个入口允许、在另一个入口意外阻断。

下图并列展开先后的两次发布请求。左列开始时活动版是 r12；左列发布完成后，再编辑和保存 r17，才开始右列。保存操作本身都不改变活动指针。

~~~mermaid
flowchart TD
    R16["第一次发布<br/>已保存 r16<br/>标题：欢迎<br/>活动版 r12"] -->|明确请求发布 r16| Check16["校验通过<br/>生成不可变快照<br/>r16"]
    Check16 --> Switch16["原子切换<br/>活动指针<br/>r12 → r16"]
    Switch16 --> Public16["访客读取 r16<br/>标题：欢迎"]
    R17["第二次发布<br/>已保存 r17<br/>标题为空<br/>活动版 r16"] -->|明确请求发布 r17| Reject17["空标题校验失败<br/>不生成新快照<br/>不切换活动指针"]
    Reject17 --> Keep16["访客仍读取 r16<br/>标题：欢迎"]
~~~

快照记录 `documentId`、`revision`、`schemaVersion`、组件注册表版本和渲染器版本。只固定文档修订不足以复现画面：组件渲染代码或引用的外部图片发生变化后，旧修订可能重新渲染出不同内容。系统可固定这些依赖版本，也可保存确切构建产物并固定其外部资源引用。只有待校验的具体修订和所有会影响输出的依赖都确定后，才生成并原子切换活动快照指针。

草稿与公开版可以并存：修订 17 正在编辑，访客仍读取已接受的修订 16。失败发布不删除草稿或改写当前页面；若要回滚，只需把活动指针重新指向一个仍可用的既有快照。撤销则作用在编辑历史里，二者解决的是不同问题。

### 协作、传输与冲突解决需要分别设计

`WebSocket` 能传输编辑事件，却不会自动决定两人同时移动 `heading-1` 时谁先提交。单写者模型可由服务端按顺序处理命令；版本条件或锁能拒绝并发写入，但会增加冲突提示或等待。**operational transformation (操作转换，OT)** 按并发操作调整彼此内容以维护规定的一致性；**conflict-free replicated data type (无冲突复制数据类型，CRDT)** 只有在满足其数据类型的收敛条件后，才能让副本合并并最终收敛。两者仍需定义操作格式、删除与移动语义、版本兼容和树约束。

按离线需求、实时合并要求、服务端排序能力和审计要求选机制。即便采用 OT 或 CRDT，节点类型校验、树的父子约束和发布规则仍然需要执行。具体文档状态由谁持有见[前端架构怎样划分呈现、交互和数据所有权？](#51.%20%E5%89%8D%E7%AB%AF%E6%9E%B6%E6%9E%84%E6%80%8E%E6%A0%B7%E5%88%92%E5%88%86%E5%91%88%E7%8E%B0%E3%80%81%E4%BA%A4%E4%BA%92%E5%92%8C%E6%95%B0%E6%8D%AE%E6%89%80%E6%9C%89%E6%9D%83%EF%BC%9F)；创建、局部校验和通知视图的实现见[页面编辑器何时需要设计模式？](#52.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E4%BD%95%E6%97%B6%E9%9C%80%E8%A6%81%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%EF%BC%9F)。设计模式篇的 `nodes` 数组只是聚焦对象协作的教学简化；本篇和前端架构篇展示完整 `rootIds` 与 ID 索引树。

> [!info]- 来源
> - **JSON 结构校验。** JSON Schema Draft 2020-12，Validation §6 的 `type`、`required`、数组和数值关键词；其用途包括验证 JSON 实例结构：[规范](https://json-schema.org/draft/2020-12/json-schema-validation)，2026-11-12 核对。
> - **绘制顺序。** W3C CSS 2.2，Appendix E “Elaborate description of Stacking Contexts”：[规范](https://www.w3.org/TR/CSS22/zindex.html)，2026-11-12 核对。
> - **前端共享状态。** React，“Sharing State Between Components”，共同所有者与状态上提：[原文](https://react.dev/learn/sharing-state-between-components)，2026-11-12 核对。
> - **客户端反馈与可信边界校验。** OWASP Input Validation Cheat Sheet，“Common Pitfalls · Client-only checks”建议浏览器校验用于即时反馈，服务端仍要校验输入：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html#common-pitfalls)，2026-11-12 核对。
> - **资源授权。** OWASP Authorization Cheat Sheet，“Validate the Permissions on Every Request”要求针对每个请求校验权限：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#validate-the-permissions-on-every-request)，2026-11-12 核对。
> - **副本收敛。** Shapiro 等，*Conflict-free Replicated Data Types*（2011），强最终一致性与状态/操作型 CRDT 的充分条件，§§2–3：[论文](https://perso.lip6.fr/Marc.Shapiro/papers/2011/CRDTs_SSS-2011.pdf)。
> - **并发操作转换。** Sun 等，*Achieving Convergence, Causality Preservation, and Intention Preservation in Real-Time Cooperative Editing Systems*（1998），OT 的一致性性质：[论文](https://www.cs.cityu.edu.hk/~jia/research/reduce98.pdf)。
## 54. Scrum 怎样让团队检查并调整工作？

假设团队正在开发页面编辑器，目标是让用户创建内容并安全发布。产品方向可能需要数月才能实现，单个 Sprint（冲刺周期）只能完成其中一部分；团队需要不断判断工作是否仍有价值、遇到阻碍时是否要调整计划。

Agile（敏捷）是一组强调协作、可用软件、客户合作和响应变化的价值观与原则；Scrum 是用于复杂工作的轻量框架，规定团队职责、事件、工件和承诺。Product Goal（产品目标）、Product Backlog（产品待办列表）、Sprint Goal（Sprint 目标）、Sprint Backlog（Sprint 待办列表）、Increment（增量）与 Definition of Done（完成定义）在框架中共同提供方向与质量边界。框架创造检查与适应的节奏，但不会自动保证估算准确、交付质量或用户价值。

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

例如，Product Goal 可以是“让非开发者安全创建并发布简单页面”。一个 Sprint Goal 可以是“访客能查看含标题的公开发布页面”。这个产品的 Definition of Done 包含权限验证：公开页面可以访问，草稿和受限内容拒绝未授权访问。团队可将内容存储、页面预览和发布校验作为候选工作；只有满足完成定义并整合到产品的部分才是 Increment。一轮 Sprint 中可以形成多个 Increment，只要每个都满足 Definition of Done 并集成到产品。

### Sprint 事件让计划贴近现实

Sprint 是一个月或更短的固定长度事件，包含 Sprint Planning、Daily Scrum、Sprint Review、Sprint Retrospective 和全部工作活动；Sprint 容纳其余四个正式事件。Scrum Guide 不规定两周的固定节奏；团队选择能形成稳定检查与反馈、又不拖慢调整的长度。

Sprint Planning（Sprint 计划）讨论为什么这个 Sprint 有价值、可以做什么、如何完成。全队共同定义 Sprint Goal；Developers 与 Product Owner 讨论后选择本轮纳入的 Product Backlog 项，并制定执行计划。进入 Sprint 后，Developers 可根据新信息调整 Sprint Backlog，并与 Product Owner 澄清和协商范围，以保护 Sprint Goal。

Daily Scrum（每日 Scrum）在 Sprint 的每个工作日举行，是 Developers 检查朝 Sprint Goal 的进展并调整计划的 15 分钟事件。Developers 自行选择形式，以形成下一天的可执行计划；不要求每个人向主管轮流汇报昨日、今日和阻碍。

在页面编辑器案例中，开发者发现公开页面已经能显示标题，但未登录访客也能打开草稿。Daily Scrum 让大家及时看见这个阻碍，并调整后续计划：先补权限校验，再同时复测“公开页面可访问”和“草稿被拒绝”。开发和验证可以持续形成可用成果。

~~~mermaid
flowchart TD
    G["Sprint Goal<br/>访客可查看<br/>公开页面"] --> W["执行计划<br/>构建与验证"]
    W --> D["Daily Scrum<br/>检查进展"]
    D -->|调整后续计划| W
    W --> I["可用 Increment<br/>满足完成定义"]
    I --> U["按需发布"]
~~~


Sprint Review（Sprint 评审）是团队与利益相关者检查结果、讨论环境变化并协作决定下一步的工作会话。它不是发布审批关卡；符合 Definition of Done 的增量可按产品需要在 Review 前发布。Sprint Retrospective（Sprint 回顾）检查人际协作、流程、工具与质量，挑选可落实的改进。

Sprint 临近结束时，Review 先检查产品结果与环境变化，Retrospective 随后检查工作方式并结束本轮 Sprint。两者为下一轮 Planning 提供不同的反馈。本例先通过两项权限复测、满足完成定义并将改动集成到产品；到了 Review，利益相关者试用页面编辑器后提出手机预览需求，Product Owner 据此调整待办优先级。在 Retrospective 中，团队发现权限验证安排得太晚，决定下一轮开发新发布功能时更早检查“允许访问”和“拒绝访问”两种情况；质量要求保持不变，改进的是发现问题的时机。

~~~mermaid
flowchart TD
    R["Sprint Review<br/>检查产品结果"] --> B["按需调整<br/>Product Backlog"]
    R -->|随后| T["Sprint Retrospective<br/>检查工作方式"]
    T --> M["选定改进"]
    B --> P["下一轮 Sprint Planning"]
    M --> P
~~~


### 遇到变化时，保护目标并重谈范围

前面的权限缺陷意味着成果尚未达到 Definition of Done。Developers 应先确认影响、向 Product Owner 说明修复与复测所需工作，再共同判断是否延后非核心样式微调，以在保持质量要求的前提下实现 Sprint Goal。修复后，两种权限结果都通过验证，页面才可以成为可用增量的一部分。若目标本身已失去价值，Product Owner 可取消 Sprint。

常见误区可从工件和事件的用途识别：

- 把 Sprint Backlog 当作冻结合同，会让计划无法反映实际学习。
- 把 Daily Scrum 当作人员考核汇报，会挤掉团队协作和适应计划的机会。
- 把 Sprint Review 当作单向演示或发布审批，会削弱共同检查和调整的目的。
- 只保留仪式名称、忽略透明、检查和适应，会失去框架的工作机制。

若使用 Scrum，应按其定义运行并检查结果；若不适合，也可采用其他匹配产品复杂度、反馈周期和约束的协作方式。

> [!info]- 来源
> - Scrum Guides 官方下载页在 2026-11-11 仍将 2020 年 11 月版列为当前版本；本文按其职责、事件、工件和承诺定义：[The Scrum Guide](https://scrumguides.org/scrum-guide.html)，[官方版本下载页](https://scrumguides.org/download.html)。
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
