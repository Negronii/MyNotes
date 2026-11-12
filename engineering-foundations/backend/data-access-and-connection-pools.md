# 怎样限定对象关系映射会话并排查连接池耗尽？

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

## 会话、事务和连接各自保存什么状态？

`Session` 保存本次工作中加载或新增的 ORM（对象关系映射）对象、identity map（身份映射）和待写入的变更。身份映射确保同一会话中的主键身份对应同一个 Python 对象；它不会缓存任意查询结果，也不适合跨请求共享。一个 `Session` 是可变的事务状态，不可由并发线程共同使用；`AsyncSession` 也不可被多个并发 Task 共享。并发线程各用自己的局部 `Session`，异步 Task 各用自己的局部 `AsyncSession`，不要把线程池里的 Session 留给之后的请求。

事务是数据库原子操作的边界。`flush()`（刷新）把 Session 中待写入的变化发成 SQL，但仍处于当前事务；正常离开 `session.begin()` 时提交，异常离开时回滚。若数据库在 INSERT 时生成主键，flush 后通常能在对象上读到这个 ID；但在提交前回滚，新增行仍不会成为已提交数据。若 flush 异常从 `session.begin()` 向外传播，事务上下文在退出时回滚；若代码捕获异常后还要复用同一 Session，必须先显式回滚，或关闭并丢弃这个 Session。

`Engine` 长期保存数据库方言、连接建立方式和进程内连接池。Session 一般先保存逻辑事务状态，第一次真正需要数据库连接时，才向 Engine 借一条 DBAPI 连接；本例由执行 SELECT 触发，但调用 `Session.connection()` 也可以在业务 SQL 发出前借出。事务结束后连接归还池。一个 Session 可以先后运行多笔事务，但每笔事务都有自己的结束点；本例每段请求读取或 worker 页使用一个新的 Session，并在此后才交付响应或进入下一页。`Session.close()` 会结束未完成的事务并归还连接；关闭 Session 不等于关闭数据库服务器。

仓库中的 [ASP.NET Core 与 EF Core 示例](../../archive/back-end/ASP.NET-Core.md) 用 `DbContext` 展示相近的对象跟踪与请求作用域。换 ORM 后，仍要分别找出对象跟踪、事务提交和驱动连接归还的边界；某框架默认的 Web 作用域不是数据库本身的规则。

## 怎样让每个请求有界地访问数据库？

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

每页各自使用短事务，因此页与页可能看到不同时间点的数据；一个新事件若在前一页之后插入到已经越过的游标之前，后续页不会回头拾取它。稳定排序键只保证给定视图内游标可前进，不等于固定结果集。若产品要求同一数据库快照，需把 `Session` 和事务一起移到页循环外，并让每页查询复用这个 Session；所有页处于同一笔有界的 PostgreSQL `REPEATABLE READ` 事务中，或读取版本化快照。此时连接从第一次借出后一直占到整段循环的事务结束，包括页间处理时间。连接池约束读取并发，数据库主键、索引和事务语义仍由数据库决定，见[库存约束怎样保护一次预留？](../databases/database-fundamentals.md)。

使用 ORM 可清楚表达实体关系和变更跟踪；批量操作或数据库特有查询也可以使用参数化 SQL。应检查 ORM 实际发出的 SQL：数据库针对实际语句选择查询计划，唯一约束和隔离语义仍由数据库决定。

## 长时间持有连接怎样变成池耗尽？

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

**接下来：** 数据访问章节规定回源时何时借用和归还连接；缓存会改变哪些展示读取到达数据库以及返回的版本新旧，见[怎样缓存数据库读取并说明陈旧窗口？](caching-and-redis.md)。若请求超时或需要控制重试总量，见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

> [!info]- 来源
> - SQLAlchemy 2.0 中 Session 的身份映射、工作单元、flush/commit/rollback、close 归还连接，以及 Session/AsyncSession 的并发使用规则：[Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)，对应 `What does the Session do?`、`Flushing`、`Closing`、`Is the Session thread-safe?`，核对于 2026-11-12。`Session` 不做通用查询缓存，见同页 `Is the Session a cache?`。默认提交后过期对象属性与事务边界见 [Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#managing-transactions)；`Session.connection()` 的连接获取时点见 [Session API](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.connection)。
> - `QueuePool` 配置项、按需创建连接、`pool_size + max_overflow` 并发上限以及 fork 时不共享池连接：[SQLAlchemy 2.0, Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)，`Connection Pool Configuration`、`QueuePool` 与 `Using Connection Pools with Multiprocessing or os.fork()`，核对于 2026-11-12。overflow 归还后由空闲队列容量决定保留或关闭，核对 [SQLAlchemy 2.0.44 QueuePool 实现](https://github.com/sqlalchemy/sqlalchemy/blob/rel_2_0_44/lib/sqlalchemy/pool/impl.py#L129-L166)。代码为同步 `create_engine()` 路径；异步 Engine 使用兼容 asyncio 的池实现。
> - 池事件定义：连接成功借出见 [PoolEvents.checkout](https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.PoolEvents.checkout)，归还见 [PoolEvents.checkin](https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.PoolEvents.checkin)，物理连接创建见 [PoolEvents.connect](https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.PoolEvents.connect)；池到达配置上限后的 timeout 见 [SQLAlchemy 2.0 Error Messages](https://docs.sqlalchemy.org/en/20/errors.html#queuepool-limit-of-size-x-overflow-y-reached-connection-timed-out-timeout-z)，两页核对于 2026-11-12。
> - `LIMIT` 查询应有唯一稳定排序：[PostgreSQL 18, LIMIT and OFFSET](https://www.postgresql.org/docs/18/queries-limit.html)，§7.6；`(occurred_at, event_id)` 行值比较按从左到右顺序比较：[PostgreSQL 18, Row Constructor Comparison](https://www.postgresql.org/docs/18/functions-comparisons.html#ROW-WISE-COMPARISON)，§9.25.5；核对于 2026-11-12。
> - PostgreSQL 的 Read Committed 在每条命令开始时取快照，Repeatable Read 在事务内保持同一快照：[PostgreSQL 18, SET TRANSACTION](https://www.postgresql.org/docs/18/sql-set-transaction.html)，`ISOLATION LEVEL`，核对于 2026-11-12。
> - PostgreSQL `pg_stat_activity` 的 `state`、`xact_start`、`wait_event_type` 字段，以及 `idle in transaction`、`Lock` 等等待状态：[PostgreSQL 18, The Cumulative Statistics System](https://www.postgresql.org/docs/18/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW)，§27.2.3，核对于 2026-11-12。
> - 账户范围、job 的时间界限和页数是本例的业务约束。`require_account_permission` 是示意授权边界，不是 SQLAlchemy API。
