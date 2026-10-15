# Data Access and Connection Pools / 数据访问与连接池

**Core explanation / 核心解释：** An ORM session is a short-lived unit of work that tracks mapped objects and coordinates SQL within a transaction. Its lifetime, the transaction lifetime, and the database connection lifetime are related but distinct: a session may acquire a pooled connection only when it first needs the database, and commit or rollback returns that connection for reuse. / ORM Session 是短生命周期的工作单元，负责跟踪映射对象并协调事务中的 SQL。Session、事务和数据库连接的生命周期彼此相关但并不相同：Session 通常在首次访问数据库时才从连接池取连接，提交或回滚后会将连接归还以便复用。

**Key terms / 关键术语：** ORM mapping / ORM 映射；identity map / 身份映射；unit of work / 工作单元；session / 会话；transaction / 事务；connection checkout / 连接借出；connection pool / 连接池；pool timeout / 连接池等待超时。

## Generalize the existing EF Core example / 推广已有 EF Core 示例

The existing [ASP.NET Core note](../../archive/back-end/ASP.NET-Core.md) is a concrete reference for entity mapping, `DbContext` tracking, dependency-injection scope, and disposal. It shows that a `DbSet<T>` exposes an entity set rather than declaring a table, that the model controls mapping, and that `AddDbContext` is scoped by default in the typical request flow. When the scope ends, its `DbContext` is disposed. The reusable rule is to give each request or job a bounded unit of work, keep its tracked objects local to that unit, and dispose it when the work ends.

Keep four boundaries separate:

- **Session / `DbContext`:** identity map plus change tracking and query coordination for mapped objects. It is not a durable application cache or a database connection.
- **Transaction:** the atomic commit/rollback boundary for statements that must succeed together. A session can span more than one transaction if deliberately reused, so a request scope alone does not define atomicity.
- **Connection:** the driver-level handle used to talk to the database. It is commonly checked out lazily from a pool when a transaction executes SQL.
- **Pool:** process-local reuse and concurrency limit for those connections. Closing a checked-out connection normally returns it to the pool; it need not close the underlying network socket.

## One request, one bounded transaction / 一个请求与一个有界事务

This synchronous SQLAlchemy 2.0 example assumes `Customer` and `Order` are mapped classes. `session.begin()` commits on a clean exit and rolls back if an exception escapes. The outer session context closes the session on both paths.

~~~python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

engine = create_engine(
    database_url,
    pool_size=8,
    max_overflow=2,
    pool_timeout=2,
)

def place_order(customer_id: int, sku: str, quantity: int) -> int:
    with Session(engine) as session, session.begin():
        customer = session.get(Customer, customer_id)
        if customer is None:
            raise LookupError("customer not found")

        order = Order(customer_id=customer_id, sku=sku, quantity=quantity)
        session.add(order)
        session.flush()  # emits the INSERT inside this transaction
        order_id = order.id

    return order_id
~~~

The ORM operation still has an SQL contract: conceptually it emits an insert such as `INSERT INTO orders (customer_id, sku, quantity) VALUES (:customer_id, :sku, :quantity)`. For a report or a database-specific operation, make the SQL explicit and bind values rather than concatenating them:

~~~python
with Session(engine) as session:
    rows = session.execute(
        text("SELECT order_id, amount_cents FROM orders WHERE customer_id = :id"),
        {"id": customer_id},
    ).all()
~~~

Use an ORM for common mapping, relationship loading, and change tracking when its generated queries are clear. Use SQL directly when a bulk operation, specialized SQL feature, or plan shape needs explicit control. Either way, keep parameter binding and the same transaction/constraint rules; inspect generated or handwritten SQL with the selected database's plan tool.

The [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md) note explains SQL result semantics, constraints, query plans, transactions, and isolation independently of the ORM.

## Follow the checkout and cleanup / 跟踪借出与清理

The request path is: create a fresh session → the first query or flush starts database work and checks out a connection → load or change mapped objects → commit on success or rollback on error → return the connection → close the session. SQLAlchemy sessions use autobegin by default, so a read can also open a transaction. A `Session` context manager closes the session; `Session.begin()` frames the transaction and handles rollback before propagating an exception. The official FastAPI SQL database example uses a generator dependency with `with Session(engine)` to provide one session per request.

Avoid holding an active transaction while waiting on a remote API, streaming a slow response, or doing other work that does not need the database. While a connection is checked out, another request may wait for a pool slot. If all slots are busy, the pool waits up to its configured timeout; then the request fails with a pool timeout. A forgotten session, unclosed result/connection, or transaction left open can therefore look like database slowness and eventually exhaust the pool. Observe checkout wait/timeouts, checked-out counts, and long transaction duration; increasing the pool without checking database capacity can move the queue into the database.

For a synchronous SQLAlchemy `QueuePool`, the maximum concurrent connections per process is `pool_size + max_overflow`. If an application has 4 replicas, 3 worker processes per replica, and a pool configured as 8 plus 2 overflow connections, the upper bound is `4 × 3 × (8 + 2) = 120` connections if every process fills its pool. Pools grow on demand rather than pre-opening all those connections. Compare the aggregate with the database's application budget and leave capacity for migrations, administration, and other services. This multiplication assumes each process owns its pool; SQLAlchemy warns against sharing live pooled connections across a process fork.

## Representative answer / 代表性面试回答

**How would you scope an ORM session and diagnose pool exhaustion? / 你会怎样限定 ORM Session 的作用域并排查连接池耗尽？**

Give each request a short-lived session and frame each write unit with one transaction. Commit on success; roll back on an exception; always close the session so checked-out connections return to the pool. The ORM tracks mapped state, while the database transaction defines atomicity and the pool controls concurrent connections. Compute the possible connection total across every replica and worker process, then inspect checkout waits and long-held transactions before changing pool size. Use parameterized SQL for operations where explicit query shape matters.

为每个请求创建短生命周期的 Session，并用一个事务界定每组需要原子完成的写入。成功时提交，异常时回滚，并始终关闭 Session，使借出的连接归还连接池。ORM 负责跟踪映射对象；数据库事务决定原子性；连接池限制并发连接数。先按所有副本和工作进程计算连接总上限，再检查连接等待和长事务，之后再决定是否调整连接池。需要明确查询形态时使用参数化 SQL。

**Sources and verification / 来源与验证：** SQLAlchemy 2.0 [Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) and [Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html), and the FastAPI [SQL (Relational) Databases tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/), checked 2026-10-15. The documented synchronous `Session`/transaction pattern and bounded pool behavior were exercised locally with SQLAlchemy 2.0.44 and SQLite 3.51.0: a successful block committed; an exception rolled back; session close reduced checked-out connections from one to zero; a second checkout against a full one-connection pool timed out, then succeeded after the first connection was returned. The docs page identifies SQLAlchemy 2.0.54 as the current 2.0 docs build; the verification above names the installed runtime version. No network database or asynchronous driver was used.
