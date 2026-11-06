# 怎样限定对象关系映射会话并排查连接池耗尽？

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

## 会话、事务和连接各自保存什么状态？

ORM Session（ORM 会话）是一段短期工作单元：它保留本次加载或新建的映射对象、identity map（身份映射）以及待同步的更改。它不是跨请求可共享的对象缓存，也不等于一条数据库连接。修改映射对象后，Session 在查询或提交前可能 flush（刷新）这些更改为 SQL；flush 只是把语句交给当前事务执行，不等于提交已持久化。例如 `add()` 一个新对象后 `flush()`，本事务可以读取数据库生成的 ID；若随后在 `commit()` 前异常并回滚，新增行不会留下。

transaction（事务）划定一组 SQL 的 commit / rollback 边界。Session 可以在不同事务间继续存在，因此“每请求一个 Session”不会自动说明这一请求中哪几条语句必须原子提交。connection（连接）是数据库驱动通信资源；Session 通常等到第一次真正执行 SQL 时才向 Engine 借出。pool（连接池）由进程内 Engine 管理可复用连接和并发借出上限，归还连接一般是把资源放回池中重用，而不是关闭底层 TCP socket。

仓库的 [ASP.NET Core 与 EF Core 例子](../../archive/back-end/ASP.NET-Core.md) 展示了同一组生命周期在另一套 ORM 中的写法：DbSet<T> 表示实体集合；DbContext 模型决定实体怎样映射到表；默认依赖注入作用域通常为一次 Web 请求创建 DbContext，请求结束后 dispose。换成其他框架时，仍要分清对象跟踪、事务提交和驱动连接归还，不要把一种 ORM 的默认作用域当成数据库本身的规则。

## 怎样让每个请求有界地访问数据库？

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

使用 ORM 处理常见实体读写、关系装载和变更跟踪，前提是生成的查询形态清楚。批量更新、数据库特有语法或需要明确计划时，直接写参数化 SQL 也合适；无论由哪一层生成，主键、事务、约束与查询成本都由数据库语义决定。参见[两个请求争夺最后一件库存时，怎样保证只预留一次？](../databases/database-fundamentals.md)。

## 长时间持有连接怎样变成池耗尽？

典型路径是：请求创建 Session；第一次 SELECT 或 flush 才借连接并开始事务；事务执行查询或写入；提交或回滚后驱动连接归还；工作结束后 Session 关闭。SQLAlchemy 默认 autobegin（自动开始事务）：第一次访问数据库会开启事务，即使随后只是读。若在连接仍借出时等待第三方 HTTP API、流式发送长正文、排队或执行与事务无关的 CPU 工作，慢环节会占住一个连接，让后续请求等待空闲槽位。

当所有连接都被借出时，新请求在 pool_timeout 设定时间内等待；无连接归还就会超时。漏关 Session、遗留结果游标或事务、锁等待、每次请求做 N+1 查询、把慢远端调用放在事务内，都可能拉长 checkout 时长。排查时分别看 checked-out 数量、借出等待时间、池超时、事务持续时间和 SQL 耗时。直接加大池可能把等待从应用池转移到数据库，也可能突破数据库总连接预算。

对明确配置的 SQLAlchemy `QueuePool`，单进程可同时借出的连接上限为 `pool_size + max_overflow`，通常按需建立而非启动时全部打开。作为一个独立部署估算，假设 4 个副本、每个副本 3 个工作进程，每进程设置 8 个池连接和 2 个 overflow，则总上限是 `4 × 3 × (8 + 2) = 120`。这是另一个配置示例，不是账户报表架构的 200 连接预算；报表容量须把 API、worker 和其他连接使用者放进同一总预算。任何池上限都不保证数据库一定接受这些连接；每个进程通常拥有自己的池，也不应在进程 fork 后共享已打开的连接。

> [!example] 一个连接如何被占住
> 若 `QueuePool` 只有一个连接、`max_overflow=0` 且 `pool_timeout=2` 秒，请求 A 在 t=0 借到连接并在事务未结束时等待远端服务 3 秒。请求 B 在 t=0.1 到达，虽然自己的 SQL 只需 10 毫秒，但到 t≈2.1 池等待先超时，B 尚未发出 SQL；A 在 t=3 归还连接也来不及挽救 B。把远端等待移到事务外并缩短数据库工作，才能释放这个槽位。

**接下来：** Session/事务决定一次数据库访问怎样借用连接；缓存则影响哪些读取到达数据库以及读到的版本新不新。见[怎样缓存数据库读取并说明陈旧窗口？](caching-and-redis.md)。请求截止时间与拒绝/重试预算见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

> [!info]- 来源
> - Session 的身份映射、工作单元、flush、事务边界与首次连接借用：[SQLAlchemy 2.0, Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)，示例以 2.0 API 编写；官网在 2026-11-06 同时列出 2.1.8 为当前版本、2.0.57 为 2.0 维护版本。当前版本文档见 [SQLAlchemy 2.1, Session Basics](https://docs.sqlalchemy.org/en/21/orm/session_basics.html)。
> - QueuePool、pool_size、max_overflow、等待和进程 fork 边界：[SQLAlchemy 2.0, Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)；当前版本对应的 [SQLAlchemy 2.1, Connection Pooling](https://docs.sqlalchemy.org/en/21/core/pooling.html)。
> - LIMIT 分页需要唯一排序，且不同页的排序必须稳定：[PostgreSQL 18, LIMIT and OFFSET](https://www.postgresql.org/docs/18/queries-limit.html)。
> - 每请求 Session 的 Web 模式：[FastAPI, SQL (Relational) Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)，核对于 2026-11-06。
> - QueuePool 1 槽的等待/超时复现与 flush 回滚验证使用 SQLAlchemy 2.0.44、SQLite 3.51.0；另在 PostgreSQL 14.24、SQLAlchemy 2.0.44 和 psycopg2 上执行本页两条读取路径，验证账户隔离、同时间戳跨页、季度边界和连接归还。
> - 归档 EF Core 示例只用于对照对象/请求作用域：[ASP.NET Core 与 EF Core 示例](../../archive/back-end/ASP.NET-Core.md)。
