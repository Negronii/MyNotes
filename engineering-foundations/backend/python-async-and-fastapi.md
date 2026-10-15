# Python Async and FastAPI Request Lifecycle / Python异步与FastAPI请求生命周期

**Core idea / 核心模型：** `asyncio` lets one event-loop thread make progress on other tasks while the current task waits for asynchronous I/O. An `async def` declaration alone does not make blocking work asynchronous: choose `def` for synchronous libraries that block, and `async def` when awaited libraries can suspend. Tie every acquired resource to a clear cleanup boundary, and treat cancellation as a cooperative request to stop. / `asyncio`让事件循环线程在当前任务等待异步I/O时推进其他任务。仅仅声明`async def`不会让阻塞操作异步：使用同步阻塞库时可选择`def`，使用能通过`await`挂起的库时选择`async def`。资源应绑定明确的清理边界；取消是要求任务协作停止，而非强制终止。

**Key terms / 关键术语：** coroutine function / 协程函数；coroutine object / 协程对象；awaitable / 可等待对象；task / 任务；event loop / 事件循环；cooperative scheduling / 协作式调度；blocking I/O / 阻塞I/O；deadline / 截止时间；cancellation / 取消；yield dependency / `yield`依赖；worker thread / 工作线程。

## From `async def` to a running task / 从`async def`到运行中的任务

An `async def` **coroutine function** describes work. Calling it creates a **coroutine object**; it does not run the body. `await coro()` drives that coroutine as part of the current task. `asyncio.create_task(coro())` schedules it as a separate **Task**, so it can progress concurrently with other tasks. Keep and await created tasks; starting work without collecting its result makes failures and shutdown hard to control. In Python 3.11, `asyncio.TaskGroup` is a structured way to create related tasks and wait for them together.

An **awaitable** is any object accepted by `await`, including coroutine objects, Tasks, and Futures. During an incomplete await, the current task suspends and the event loop can run another ready task or service I/O. This is cooperative: code runs until it reaches a suspension point. A synchronous call such as `time.sleep()`, a blocking database driver, or a long CPU loop prevents the event-loop thread from serving other tasks during that call.

An `async def` function containing `yield` is an **async-generator function**; calling it returns an **async-generator object**, not a coroutine object. FastAPI manages that object's dependency lifecycle to run cleanup after yielding the resource.

## Choose the boundary by the library you call / 按所调用的库选择边界

For an awaited database or HTTP client, use an `async def` route and await its I/O. A synchronous `def` route or dependency that FastAPI calls is run in its worker thread pool, so a legacy synchronous client can fit that boundary. Conversely, a synchronous helper called directly from inside an `async def` route is just a normal function call; FastAPI does not automatically move that nested call to a thread.

`asyncio.to_thread()` is useful for blocking I/O that cannot yet be replaced, and it keeps the event loop available while the thread waits. It is not a general CPU-parallelism switch: in CPython, the GIL usually limits simultaneous execution of pure-Python CPU work. A process pool or separate worker can run CPU work in parallel, with serialization, startup, memory, and queueing costs. Native extensions that release the GIL and other Python implementations can differ; measure the actual workload. Bound thread/process concurrency so offloading does not merely move an unbounded queue.

## Cancellation, deadlines, and cleanup / 取消、截止时间与清理

`Task.cancel()` arranges for `CancelledError` to be raised in the task at a later opportunity, commonly at an `await`. Use `try/finally` to release resources and normally let cancellation propagate after cleanup. Do not catch `BaseException` or suppress `CancelledError` as a generic error; structured concurrency and timeout scopes rely on cancellation being visible.

In Python 3.11, `asyncio.timeout(seconds)` cancels the current task when its time budget expires and raises `TimeoutError` outside the context manager. It is cooperative: a blocking synchronous function prevents the event loop from delivering that cancellation until the function returns. A timeout around `await asyncio.to_thread(...)` stops waiting in the coroutine but cannot forcibly stop a thread function already running. A client timeout also does not prove that a remote operation stopped or had no side effect. Pass remaining request budget to supported downstream calls and use the broader [API reliability guidance](../reliability/api-reliability-and-async-delivery.md) for end-to-end deadlines and unknown outcomes.

For a FastAPI dependency using `yield`, FastAPI owns the exit path. In the verified FastAPI 0.128.0 behavior, the default yield dependency scope is `"request"`: cleanup runs after the response body is sent. `scope="function"` closes it after the route function returns but before the response is sent, which is suitable only when response serialization and streaming no longer need the resource. A stream that consumes a dependency during body generation needs request scope. A `finally` block in the dependency runs on ordinary completion and on an explicit task cancellation that reaches the ASGI app; a real network disconnect is not guaranteed to cancel every server task in the same way, so verify the chosen server and response mode. The test below checks explicit cancellation, not every disconnect path.

## Runnable request example / 可运行的请求示例

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

## Python and runtime versions / Python与运行时版本

`async`/`await` syntax is part of Python; `asyncio` is a standard-library API. This example was checked with **CPython 3.11.13**, FastAPI **0.128.0**, Starlette **0.47.2**, and HTTPX **0.28.1**. `asyncio.timeout()` and `asyncio.TaskGroup` require Python 3.11; `asyncio.to_thread()` requires Python 3.9+. CPython is one Python implementation, so GIL statements above are explicitly CPython-specific. Verify framework lifecycle options against the installed FastAPI version: newer live documentation may describe behavior absent in an older release.

## Interview answers / 面试回答

**Why can an `async def` endpoint still stall other requests? / 为什么`async def`接口仍会拖慢其他请求？** An async function only yields when it awaits an operation that actually suspends. Calling a synchronous network/file helper or doing a long CPU loop inline keeps the event-loop thread busy. I would use an async driver, a sync route/dependency that FastAPI can offload, or a bounded thread/process worker chosen for the workload; then I would measure queueing and latency.

异步函数只有在等待一个确实会挂起的操作时才让出执行权。在函数内直接调用同步网络/文件操作，或执行很长的CPU循环，都会占住事件循环线程。我会使用异步驱动、由FastAPI代为卸载的同步路由/依赖，或根据工作负载选择有界线程/进程工作池，并测量排队与延迟。

**What happens when a request is cancelled while it owns a resource? / 请求持有资源时被取消会怎样？** Cancellation is delivered cooperatively, so I put release logic in `finally` and let `CancelledError` propagate. For FastAPI `yield` dependencies I choose request scope if response streaming still consumes the resource, and function scope if cleanup should happen before sending the response. I would not assume a client timeout or disconnect proves remote work stopped; I would keep downstream deadlines and side-effect handling explicit.

取消通过协作方式传递，因此我会把释放逻辑放进`finally`并让`CancelledError`继续传播。若响应流仍要使用FastAPI的`yield`依赖，我会选择request scope；若资源应在响应发送前关闭，则选择function scope。我不会因为客户端超时或断开就认定远端工作已停止；下游截止时间与副作用处理仍需显式定义。

**Sources / 来源：** Python 3.11 [asynchronous generator functions](https://docs.python.org/3.11/reference/expressions.html#asynchronous-generator-functions), [`asyncio` tasks, cancellation, timeouts, and threads](https://docs.python.org/3.11/library/asyncio-task.html), [asyncio development guidance](https://docs.python.org/3.11/library/asyncio-dev.html), and [executor cancellation behavior](https://docs.python.org/3.11/library/concurrent.futures.html); FastAPI [async and sync route behavior](https://fastapi.tiangolo.com/async/), [yield dependency scopes](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/), and [streaming dependency lifetime](https://fastapi.tiangolo.com/advanced/advanced-dependencies/); version-pinned FastAPI [0.128.0 dependency resolver](https://github.com/fastapi/fastapi/blob/0.128.0/fastapi/dependencies/utils.py), checked 2026-10-15. Related: [Python Fundamentals / Python基础](python-fundamentals.md), [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../reliability/api-reliability-and-async-delivery.md), [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md), and [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md). [HTTP API Contracts / HTTP API契约](http-api-contracts.md) defines the request, response, and error shapes used by these handlers. [Data Access and Connection Pools / 数据访问与连接池](data-access-and-connection-pools.md) expands the resource example into database-session, transaction, and pool-lifetime choices.
