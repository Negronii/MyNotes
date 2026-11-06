# 两个请求争夺最后一件库存时，怎样保证只预留一次？

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

## 为什么先读再无条件写会超卖？

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

复合主键保证同一账户、主体和幂等键最多一条操作记录；外键保证预留指向存在的 SKU；CHECK 与 NOT NULL 一起禁止负库存和未知库存。数据库约束如何对所有写入方生效，见[如何用约束保护业务规则并为读取建立索引？](database-constraints-and-indexes.md)。

## 条件更新怎样让两个并发请求竞争？

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

## 提交成功但响应超时，怎样认出原操作？

超时只代表调用方没有收到响应；它无法区分请求未到达、事务回滚、事务仍在进行，或提交后只有响应丢失。每次查询或重放前，服务都要再次校验当前账户和主体有权读取这条操作结果。事务提交后，数据库中库存为 0，且存在 reserve-demo-208 与请求指纹 fingerprint-A 绑定的预留记录。客户端使用同一个操作键查记录或按明确的幂等契约重放；API 比较账户、主体与请求指纹后返回已记录结果而不再次扣减。不能为重试生成新键，否则服务端会把它当成另一次购买。键的作用域、保留窗口与未知结果重试规则由[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)专门解释。

操作键记录必须和库存效果处于同一事务；若先扣库存并提交，之后再单独写操作键，二者之间崩溃仍可能造成“效果已发生但重试认不出”。支付服务或消息队列不在这个本地事务中，不能靠 SQL COMMIT 宣称远端副作用也完成。账户报表的数据库到队列边界会用 transactional outbox（事务型发件箱）延伸这一问题，见[怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

## 同一库存不变量怎样用于抽奖？

抽奖服务对外提供公开只读的 GET /draws/{campaignId}，返回活动规则、时间与可见状态；已认证参与者以 POST /draws/{campaignId}/entries 提交自己的请求。服务端按当前主体检查活动仍开放、资格和一次参与规则，并使用 (campaign_id, principal_id) 唯一约束及作用域幂等键阻止重复参与。活动已关闭应返回明确 campaign-closed 状态；已有参与记录或其他规则冲突应返回明确 conflict，不让浏览器从通用错误猜结果。抽奖随机性和审计规则须符合活动承诺；统计事件不能决定资格或权威中奖结果。

有限奖品应在同一事务里条件扣减并保存参与、抽取结果与待领取状态；若扣减零行，要按活动规则明确返回库存已用完/未中奖等业务结果，不能假定数据库自动替用户重新抽取。GET /draws/{campaignId}/entries/{entryId} 只能向当前结果所有者返回本人结果与领取状态；单独的 POST /prizes/{prizeId}/claims 再验证中奖记录所有者，只收集履约所需资料并写入履约状态。后台活动管理权限应比公开读取和本人参与更严格。抽奖提交也需使用稳定操作键，并按幂等契约定义保留窗口与重放结果，避免超时后重复参与；通用规则见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。原档案的独特接口流、显式关闭/冲突结果和权限分层已迁入本节；旧入口保留导航，见[归档抽奖 API 规则入口](../../archive/front-end/Deprecated_Interview_Notes/prize-draw-api-invariants.md)。

**接下来：** 此处只说明原子库存写入及本地约束。NULL、连接和分组改变报表查询的方式见[NULL、连接与分组如何改变报表 42 的结果？](sql-null-joins-and-aggregates.md)；事务隔离、WAL 和崩溃恢复的保证见[事务隔离与 WAL 能保证什么？](database-transactions-isolation-and-recovery.md)。

> [!info]- 来源
> - 条件扣减的并发重检与事务隔离行为：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1，核对于 2026-11-06；此处并发时序明确标为 PostgreSQL 行为。
> - 主键、唯一、外键、CHECK 和 NOT NULL 的持久约束：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)，§5.5，核对于 2026-11-06。
> - SQLite 事务和外键约束：[SQLite Transactions](https://www.sqlite.org/lang_transaction.html) 与 [Foreign Key Support](https://www.sqlite.org/foreignkeys.html)，核对于 2026-11-06。
