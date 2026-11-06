# 异步 FastAPI 接口为什么仍会阻塞？

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

## 从 async def 到运行中的协程，中间发生什么？

调用 async def 函数只会构造并返回协程对象，函数体此时尚未执行；await 它或用 asyncio.create_task() 将它调度为 Task 后，函数体才开始运行。await 在等待一个尚未完成的可等待对象时暂停当前任务，事件循环可以推进其他就绪任务。被创建的任务仍由创建者或结构化并发作用域负责收集结果和等待结束。在 Python 3.11 中，TaskGroup 会在离开作用域前等待组内任务完成。

await 并不保证一定让出线程：若等待的对象已经就绪，代码可以继续推进。time.sleep()、同步数据库驱动或长时间 Python 循环则不会让事件循环调度别的任务。一个同步辅助函数如果从 async def 路由中直接调用，只是普通函数调用，FastAPI 不会自动把它移到线程池。

按驱动来选择接口：有原生 async 数据库或 HTTP 客户端时，在 async 路由中 await 它；若只能使用同步阻塞 I/O，可以把 FastAPI 路由或依赖本身声明为 def，由 Starlette/AnyIO 的同步工作线程池运行；短期兼容阻塞 I/O 时也可用 asyncio.to_thread()。这两者是不同的线程池，独立受限：框架调用的同步路由/依赖走 AnyIO 池，asyncio.to_thread() 走事件循环的默认 executor。应用要分别配置和计入它们的容量。FastAPI 只会对它负责调用的同步路由和依赖做调度，async 路由里直接调用的同步辅助函数仍在当前线程运行。

对纯 Python CPU 工作，CPython 3.11 的 Global Interpreter Lock（全局解释器锁，GIL）通常让多个线程不能同时执行 Python 字节码；to_thread 是避免阻塞事件循环的 I/O 选项，不是通用 CPU 并行开关。进程池或独立 worker 可以并行计算，但会增加序列化、进程启动、内存和排队成本。CPython 3.13 引入实验性的自由线程构建；3.14 起它成为正式支持的可选构建，但不是默认解释器，未适配的扩展还可能重新启用 GIL。运行效果取决于实际解释器和依赖，应测量确认。无论哪种卸载方式，都要限制 worker 数及等待队列。

## 任务取消时，函数、线程和远端操作分别会怎样？

Task.cancel() 会安排在事件循环下一次机会把 CancelledError 注入协程。任务可以在 finally 中释放资源；清理完成后通常应让取消继续传播。TaskGroup 和 timeout scope 也依赖取消传播，不要把 CancelledError 当作普通业务异常吞掉。

asyncio.timeout(秒数) 需要事件循环重新获得调度机会才能送达取消。如果事件循环被同步函数堵住，超时回调无法运行；阻塞调用返回后，若代码在让出控制权前已退出 timeout 上下文，超时甚至可能完全不触发。本机 CPython 3.11.13 中，`asyncio.timeout(0.01)` 包住 `time.sleep(0.05)` 正常退出，耗时约 0.06 秒。对 await asyncio.to_thread(blocking_call)，取消当前 Task 会让调用方停止等待结果，却不能强制停止已经开始运行的线程函数。底层线程可能继续占用文件、连接或 CPU，所以不要在任务已取消时立刻关闭仍被它使用的连接池。

HTTP 客户端超时或断线也不能证明远端副作用已经停止。一次请求超时后，写入可能尚未到达服务、可能回滚，也可能已经提交但响应丢失；耐久 job 需显式取消，并从权威状态确认结果，见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

## FastAPI 的 yield 依赖应何时释放？

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

`/row` 的 function-scope 依赖事件顺序是 `open → read → close`；`/stream` 默认 request scope 的顺序是 `open → body → read → close`。这是依赖和生成器事件 trace，不是对 ASGI response send 次序的测量。0.5 秒 timeout 只是示例预算；真实应用的 session、事务和数据库连接是不同资源，每个请求或 worker attempt 都要有独立短生命周期，不能把同一个 ORM Session 共享给并发 Task。见[如何限定 ORM Session 并排查连接池耗尽？](data-access-and-connection-pools.md)。若流生成器需要游标，依赖的 scope 必须覆盖最后一次游标读取；一个后台 job 则应在自己的执行生命周期内重新取得资源。

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
