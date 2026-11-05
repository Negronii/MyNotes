# How long should a FastAPI dependency stay open during a response? / FastAPI 依赖应在响应期间保持多久？

A yielded dependency is a resource scope: FastAPI enters it before using the route, then runs its cleanup after the chosen scope ends. With request scope, cleanup waits until the response body has been sent, so a streaming body can keep using the resource. With function scope, cleanup runs after the route function returns but before the response is sent; use it only when serialization and streaming no longer need the resource. / yield 依赖定义了资源作用域：FastAPI 在路由使用它之前进入依赖，并在所选作用域结束时清理资源。request scope 会等到响应体发送后再清理，因此流式响应可以继续使用该资源。function scope 在路由函数返回后、响应发送前清理资源；只有序列化和流式传输不再需要该资源时才适用。

**Key terms / 关键术语：** yield dependency / yield 依赖；request scope / 请求作用域；function scope / 函数作用域；streaming response / 流式响应；cleanup / 清理；disconnect / 连接断开。

~~~mermaid
    participant F as FastAPI
    participant R as Route
    participant D as Yield dependency
    participant B as Streaming body
    F->>D: Enter and acquire resource
    F->>R: Call route with resource
    R-->>F: Return response object
    alt function scope
        F->>D: Run cleanup before sending response
        F->>B: Send response body
    else request scope
        F->>B: Generate and send response body
        B->>D: Continue using resource
        F->>D: Run cleanup after response body
    end
~~~

## Choose scope from the last use / 按最后一次使用选择作用域

FastAPI 0.128.0 defaults yielded dependencies to request scope. An explicit function scope closes the dependency after the path operation function returns but before the response is sent. A streaming response that consumes a yielded dependency while its body is produced needs request scope; closing it at function return would end the resource too early.

The dependency's finally block runs during ordinary cleanup and when explicit task cancellation reaches the ASGI application. A network disconnect is not guaranteed to cancel every server task in the same way. Verify the behavior of the chosen ASGI server, response class, and deployment mode rather than inferring it from a client timeout.

The executable FastAPI smoke check in [Python Async and FastAPI Request Lifecycle / 为什么异步 FastAPI 接口仍会阻塞？](python-async-and-fastapi.md) compares function-scope cleanup, request-scope streaming, and explicit cancellation. It checks FastAPI 0.128.0, Starlette 0.47.2, and HTTPX 0.28.1; its explicit task cancellation case does not claim to cover every real disconnect path.

**Sources / 来源：** FastAPI [yield dependency scopes](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/) and [advanced dependencies and streaming responses](https://fastapi.tiangolo.com/advanced/advanced-dependencies/); version-pinned FastAPI [0.128.0 dependency resolver](https://github.com/fastapi/fastapi/blob/0.128.0/fastapi/dependencies/utils.py), checked 2026-10-15. The dependency scope and disconnect behavior are version and server specific.
