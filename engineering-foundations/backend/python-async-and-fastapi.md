# 异步 FastAPI 接口为什么仍会阻塞？

**案例：** FastAPI 服务收到账户 acct-17 的报表请求，用异步数据库驱动分三页读取结果。第 1 页还没返回时，处理这个请求的 Task（任务）会挂起；如果此时恰好有一个 `/health` 请求可以处理，同一个 event loop（事件循环）就先处理它。第 1 页返回后，报表 Task 恢复，接着顺序读取下一页。但如果路由直接调用同步的数据库辅助函数，事件循环要一直等到三页同步调用全部返回，其间其他请求即使已经可以处理，也只能排队。本章先解释这种阻塞从何而来，再讨论取消，最后说明数据库会话这类资源要保持打开到它最后一次被使用之后。

![异步等待与直接同步调用对事件循环的影响](resources/python-async-await-scheduling.svg)

## 从 async def 到运行中的协程，中间发生什么？

调用 `async def` 函数时，函数体并不立即执行，而是先得到一个 coroutine object（协程对象）；FastAPI 在为请求创建的 Task 中调用路由，由事件循环驱动这个 Task 运行。Task 是事件循环推进协程的调度单位，同一时刻只有一个 Task 在执行同步代码。只有当 Task 等待尚未就绪的 Future（异步结果对象）或 I/O 而挂起时，事件循环才有机会推进其他就绪的 Task。数据库返回第 1 页时，等待对象就绪，报表 Task 恢复并拿到结果；它处理这一页后再 await 第 2 页。

`await` 表示等待一个可等待对象，但不保证每次都会切换任务：对象已经就绪时，当前任务可以直接继续。`async def` 也不会自动把函数放到其他线程执行。直接调用 `time.sleep()`、同步数据库驱动或耗时很长的 Python 计算时，当前任务不会把控制权交回事件循环，事件循环要等它返回才能处理其他任务。

因此，代码在哪里执行，取决于路由怎样声明、调用的是哪类 API：

| 写法 | 执行位置与适用边界 |
| --- | --- |
| 在 `async def` 中 `await` 原生异步数据库或 HTTP API | I/O 未完成时挂起当前 Task，让事件循环处理其他就绪任务；这是报表分页的主路径。 |
| 在 `async def` 中直接调用同步辅助函数 | 辅助函数在事件循环所在线程上执行；FastAPI 不会拦截你自己直接调用的普通函数。 |
| 把 FastAPI 路由或依赖本身声明为 `def` | FastAPI/Starlette 通过 AnyIO 工作线程执行这些同步代码。线程容量有限，超出容量的调用要排队等待。 |
| 在异步路由中用 `asyncio.to_thread()` 运行短时阻塞 I/O | 由 asyncio 默认 executor（执行器）的线程执行；它的容量与 AnyIO 给同步路由和依赖的限额分开配置。 |
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

`/reports/acct-17` 每次等待一页时，都给事件循环留出处理其他任务的机会；`/blocking/acct-17` 在路由里直接执行三次同步读取，事件循环要等约 3 × 60 = 180 毫秒的合成阻塞结束后，才能处理 `/health`。`/offloaded` 在 asyncio 默认 executor 中运行同一个同步函数；`/sync-route` 则由 FastAPI/Starlette 调度到 AnyIO 工作线程。后两条路径都让事件循环可以继续运行，但它们各自占用不同的线程容量；把工作挪到线程上，也不会减少下游数据库或文件操作本身的开销。

`/reports` 路由还通过 `Depends(load_settings)` 接收一个普通 `def` 依赖。由 FastAPI 负责调用的同步依赖会进入 AnyIO 工作线程；这和在 `async` 路由里自己直接调用同步辅助函数是两种不同的调用方式。

Starlette 文档说明，AnyIO 默认的工作线程限额（worker thread limiter）有 40 个并发令牌（token），FastAPI 的同步依赖和 Starlette 的部分内部同步操作也共用这份容量；在本机 AnyIO 4.12.1 上实际读到的默认值同样是 40。它是并发上限，不是需要填满的目标。调高上限会让更多线程同时执行，线程本身和下游资源的压力都可能上升，所以仍要按每个进程的线程与连接预算来评估。asyncio 默认 executor 不受这个限额约束。另外，执行并发上限只限制同时运行的调用数，不限制排队的调用数；排队长度要另外按资源预算设限，并在入口做准入控制。

在本章使用的 CPython 3.11 上，Global Interpreter Lock（全局解释器锁，GIL）使多个普通 Python 线程通常不能同时执行 Python 字节码。因此，把 CPU 密集的纯 Python 函数放进 `asyncio.to_thread()`，虽然不再直接占住事件循环，却通常得不到多核并行；这类工作更适合交给进程池或独立的 worker 进程。CPython 3.13 起提供可选的 free-threaded（自由线程）构建，3.14 起它进入正式支持阶段，但仍是需要单独选择的构建，默认构建依然带 GIL；某些扩展库还可能重新启用 GIL，实际收益和线程安全要按所用解释器及依赖逐一验证。

回到报表分页：`await fetch_page(...)` 仍在当前请求的 Task 里一页一页顺序读取；`await` 不会自动创建并发任务。若一个请求要并发查询多个页面，需要用 `asyncio.create_task()`，或 Python 3.11 引入的 TaskGroup（任务组）的 `create_task()`，显式创建子 Task；创建者仍要负责收集结果、等待它们结束，TaskGroup 会在退出 `async with` 块前等待组内任务全部完成。不要留下无人管理的后台 Task，也不要让并发 Task 共用同一个 ORM `AsyncSession`；每个 Task 都要有自己的会话。请求或 worker 执行尝试也应各自持有短生命周期会话，数据库连接池的等待与上限见[怎样限定 ORM Session 并排查连接池耗尽？](data-access-and-connection-pools.md)。

## 任务取消时，函数、线程和远端操作分别会怎样？

前面说明了工作在哪里执行；客户端断开、超时或关停时，还要知道正在进行的工作能否停下。`Task.cancel()` 只是发出取消请求：事件循环在下一次调度这个 Task 时，向协程内部抛入 `CancelledError`。协程可以在 `finally` 中关闭游标、会话或临时文件；清理完后通常应让取消继续向外传播，使调用方按“已取消”处理。如果捕获 `CancelledError` 后正常返回，调用方看到的可能是正常结果而不是取消；如果吞掉的是 `asyncio.timeout()` 发出的取消，超时作用域也可能正常退出，而不抛 `TimeoutError`。TaskGroup 也可能因此把子任务当作正常完成，打乱调用方预期的取消流程。

`asyncio.timeout(秒数)` 同样依靠事件循环来调度取消。如果一个同步函数堵住了事件循环，截止时间到了，负责取消的回调也无法运行。在本机 CPython 3.11.13 上验证：用 `asyncio.timeout(0.01)` 包住 `time.sleep(0.05)`，代码约 0.05 秒后正常离开作用域，没有抛出 `TimeoutError`。只有当阻塞调用返回后，协程还在作用域内等待某个尚未就绪的异步操作时，迟到的取消才有机会生效：本机验证中，紧接着 `await asyncio.sleep(0)` 仍然正常退出，换成等待一段正时长的异步操作才观察到 `TimeoutError`。所以超时不是中断任意同步函数的机制。

如果取消的是正在等待 `asyncio.to_thread(blocking_call)` 的 Task，只是异步调用方不再等待。函数若已在线程中运行，Python 不会强行杀掉这个线程；只有还在 executor 队列里尚未开始的工作，才可能在执行前被取消。线程可能仍在使用文件、连接或其他资源，所以释放连接池、关闭共享句柄之前，要先确认线程已经结束。对 `asyncio.to_thread()`，可以传入一个 `threading.Event` 作为停止信号，让函数定期检查；在 AnyIO 工作线程中，则可以调用 `from_thread.check_cancelled()` 做协作式检查。

客户端超时或断线也不证明远端副作用已停止：写操作可能没到服务端、可能已回滚，也可能已提交但响应丢失。对于持久化的报表 job（后台任务），应通过权威状态查询结果，显式请求取消并确认 worker 已停止；不要把一次 HTTP 断线当成 job 终态。完整的重试与状态确认边界见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

## FastAPI 的 yield 依赖应何时释放？

取消之外，资源还有一个“该何时关闭”的问题。带 `yield` 的依赖适合把资源的打开和清理写在一起，例如异步数据库会话或游标：`yield` 之前打开资源，`yield` 之后（通常在 `finally` 中）清理。这类依赖默认使用 request scope（请求作用域）：FastAPI 在调用路由前解析依赖时打开资源，在应用发送完响应正文后清理。这里的“发送完”指 ASGI（Asynchronous Server Gateway Interface，异步服务器网关接口）的最后一个 `http.response.body` 事件已经发出，不代表客户端已经从网络收齐全部字节。若写成 `Depends(scope="function")`，则使用 function scope（函数作用域），在路由函数返回之后、响应发送之前清理。

依赖的 `scope` 参数从 FastAPI 0.121.0 起支持；下面的行为在 FastAPI 0.128.0、Starlette 0.47.2 上核对过（截至 2026-11，PyPI 上的 FastAPI 已到 0.163.x，本章未在新版本上重放）。

两种作用域的差别，在响应体生成方式不同时才显现：返回小型 JSON 时，路由函数内已读完所需数据；返回较大的 CSV（comma-separated values，逗号分隔值）流时，数据要在路由返回后才被逐块读取。下图比较两种情况下资源最后一次被使用的时间点。

![FastAPI yield 依赖作用域与响应正文的关系](resources/python-fastapi-yield-lifetimes.svg)

CSV 路由可以先返回 `StreamingResponse`，再由正文生成器逐块读取数据库游标。如果依赖使用 `scope="function"`，路由一返回资源就被关闭，正文生成器随后的读取会失败。所以流式响应应让 request scope 覆盖整个正文发送过程；无论正文正常发完、流被中止还是出错，依赖的退出逻辑都要在 `finally` 中清理资源。反过来，若路由已经读完资源并生成完整 JSON，function scope 可以在应用发送响应前释放它，减少资源占用时间。

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

在用合成 `Store` 记录的 ASGI 事件顺序（trace）中，/row 的顺序是 `open → read → close → 发送 JSON`；/stream 是 `open → 发送 CSV 表头 → 读取 Store → 发送正文结束 → close`。路由返回 `StreamingResponse` 时，正文生成器还没开始读行；默认的 request scope 让 `Store` 一直保持打开，直到应用发出最后一帧正文。反过来，把 `/stream` 的依赖改成 `Depends(get_store, scope="function")` 再运行，顺序变成 `open → close → response.start(200) → CSV 表头 → read 抛 RuntimeError`，最后一帧正文也不会发出：路由函数一返回就关闭了生成器还要读取的资源。

直接流式响应把连接、游标和请求生命周期绑在一起，正文尚未发完时会继续占资源；客户端断开也不是可查询的持久任务结果。若报表要由后台可靠生成、稍后再下载，本仓库的报表案例会在同一个数据库事务中受理 job、写入 outbox（待发消息表）并占用一个等待槽，事务提交后返回 `202 Accepted`。后台 worker 在自己的每次执行（attempt）中重新获取会话和连接，先完成 CSV 私有对象写入，再在任务仍为 `running`、attempt 匹配且未请求取消的条件下提交结果引用与 `succeeded` 终态；这和请求内的 StreamingResponse 是两种生命周期。job 的持久流程见[怎样设计一个可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

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
