# 怎样让模型 API 调用在限额、失败和截止时间内有界？

一个调用是否结束不只取决于 SDK 返回结果。请求可能在应用队列中等待，可能撞上请求数或 Token 速率限制，可能收到临时过载，也可能在服务端已经处理后才遇到网络超时。若每一层都自行重试，一个用户动作会变成许多实际 HTTP 请求。

本章用公开、合成的 CI 手册分块说明两类任务：离线为 40 个手册块生成 embedding，以及在线为一条报表问题生成回答。前者可排队、晚些完成；后者要在用户截止时间前返回。两者共用模型服务限额，但重试次数、队列和截止时间要分别控制。

## 一次调用经过哪些闸门？

请求先通过有界队列和限额准入，再占用并发槽位并发出一次 HTTP 请求。若应用层负责重试，每个重试可以重新经过限额闸门；SDK 在应用调用内部自动重试时，应用层看不到每次发送，需关闭 SDK 重试或把准入放到逐次 HTTP 请求可见的传输层。

~~~mermaid
flowchart TD
    A["到达：任务、Token 估算、绝对截止时间"] --> B{"队列有空间吗？"}
    A -->|截止或取消| I
    B -- 否 --> X["拒绝或让调用者稍后重试"]
    B -- 是 --> C["有界队列"]
    C -->|截止或取消| I
    C --> D{"并发槽位与请求数 / Token 预算可用？"}
    D -- 否 --> C
    D -->|截止或取消| I
    D -- 是 --> E["一次 HTTP 请求"]
    E -- 成功 --> F["记录用量、结果与请求 ID"]
    E -- 永久错误 --> G["失败并返回可行动原因"]
    E -- 可恢复且预算仍足 --> H["等待服务端重试提示或退避抖动"]
    E -- 可恢复但尝试数或时间预算不足 --> G
    H --> D
    E -- 超时、取消或截止到期 --> I["停止排队、等待和重试；若请求已发出，远端结果可能未知"]
    H -->|截止或取消| I
~~~

并发槽位、请求速率、Token 速率和截止时间限制不同的东西。只有队列长度有限，不能保证发送速率；只有并发上限，也不能保证 Token 消耗落在配额内。

## 队列、并发和请求配额怎样分工？

有界队列限定尚未启动的工作数量，保护进程内存，也决定过载时是否背压或拒绝。并发上限限定同时在途的 HTTP 调用数；它主要影响连接与服务端工作量。若平均每次调用需 0.5 秒，进程允许 4 个同时在途请求，粗略吞吐上限约为 8 次/秒；这仍未考虑 Token 限额、尾部时延和突发窗口。

RPM 限制单位时间内可发起的请求数，TPM 限制同一时段模型可处理的 Token 数。短请求可能先撞上 RPM；批量 embedding 则可能只有少数 API 请求，却先撞上 TPM。提供方还可能按模型、组织、项目或共享模型组分别计限，也可能设置请求骤增的爬坡限制。实际限额和时间窗以当前账户与 API 响应头为准。

> [!example] 同一批工作受哪一个限额约束？
> 假设教学服务每分钟允许 60 个请求与 12,000 个 Token。某在线模型请求预计含 900 个输入 Token，并设置 300 个输出 Token 的上限。若该服务按输入量加输出上限估计配额，一个请求预留 1,200 Token，于是固定分钟窗口的算术上限为 min(60, 12,000 / 1,200) = 10 次；只看 60 RPM 会把容量高估六倍。
>
> 这只是固定窗口例子。提供方可能用更细时间窗、不同 Token 估算或其他计量方式；某些接口的计数规则也不同。实现前要看对应模型、端点和账户的限额文档，并以响应头、usage 和实际错误核对估算。

离线 embedding 可以把多个输入合并成一个请求以减少 RPM 消耗，但这个批次仍消耗对应输入 Token，且受单请求上限约束。先按当前模型允许的单条与批量 Token 上限切批，再把批次放入队列。在线生成则设置有界输出 Token 上限，并把交互队列与后台索引队列分开；若二者仍共用全部在途槽，后台索引仍可能占满槽位，需让调度器优先处理交互任务或给在线请求保留槽位。并发槽只由正在进行的 HTTP 请求占用；调用完成或进入退避时释放它，下一次尝试再回到并发与速率准入。

单进程可以用信号量限制并发，用 Token bucket（令牌桶）或滑动窗口限制自身发送速率；这只能约束该进程。若多个 worker 共用项目限额，各进程的本地计数并不等于共享预算。要跨进程一致准入，须在共享协调层原子预留 RPM 与 Token 额度，或由集中调度器发放额度；本章假客户端不实现分布式限流器。

每次调用前估算输入 Token 和可能的输出额度并预留内部预算，响应后按接口返回的 usage（用量）对账。若提供方的速率计量规则允许根据 usage 归还预留差额，才把差额放回本地速率预算；账单 usage 与服务端 RPM/TPM 计数可能不是同一口径。失败尝试是否消耗额度、额度多久恢复，应按提供方规则处理，不能因为没有收到内容就假定请求完全免费。速率限制响应头中的剩余额度和重置时间比应用自己的平均值更接近服务端状态。

## 哪些错误可以重试，实际请求会有多少次？

应用尝试是应用代码调用 SDK 一次；实际 HTTP 请求数是网络上真正发到 API 的次数。开启 SDK 内部自动重试后，这两个数字可能不同。应用设 max_attempts=3 是总共最多三次尝试，包含第一次；SDK 设 max_retries=2 则可能是一次初始请求加两次内部重试。

先依据错误类型、错误码和响应头决定是否有恢复可能，而不是只看 HTTP 状态码：

| 观察到的结果 | 典型处理 | 是否再占用一次请求预算 |
|---|---|---:|
| API Key、权限、请求格式、模型不可用等稳定错误 | 失败并修正配置或请求；同一输入立刻重发不会改变原因。 | 否 |
| 额度耗尽、账单或项目支出上限 | 停止自动重试，先处理账户限制。某些此类错误也是 HTTP 429。 | 否 |
| 临时速率限制、流量骤增或服务过载 | 若有有效 Retry-After（最早重试时间提示），至少等待该值；否则用带抖动的退避，再按剩余截止时间有限重试。 | 是 |
| 临时网络中断、响应超时或 5xx | 先确认是否可能已处理或计费；仅在调用类型、总预算和截止时间允许时重试。 | 通常按一次新的线上请求预算 |
| 取消、用户离开或总截止时间已过 | 取消排队项；不要再开始新尝试。对于已发出的请求，远端是否停止要另外确认。 | 不再新增 |

Retry-After 是最早何时再试，不是建议忽略的提示。没有有效值时，可按 min(cap, base × 2^(attempt−1)) + random_jitter 退避；若有提供方给出的最小等待时间，则等待不少于该值，并加入少量抖动，避免许多 worker 同时重发。只有应用逐次发出请求的重试才可在此处重新申请 RPM/TPM 额度；若 SDK 内部重试仍打开，应用层的限额闸门只包住整次 SDK 调用，不会在 SDK 的每次 HTTP 发送前再次检查。要准确限制逐次发送，应关闭 SDK 重试，或把限额控制移到逐请求可见的 HTTP 传输层。无论等待多短，都须同时限制尝试数和总耗时。

重试层叠会乘大请求数。例如，应用允许最多 3 次 SDK 调用，而每次 SDK 调用内部最多重发 2 次，那么每层都遇到可重试错误时，理论上界为 3 × (1 + 2) = 9 个线上请求；若底层 HTTP 客户端还有额外重试，上界更高。一个主要重试层更易审计：若应用负责退避和逐请求限额，就在 SDK 中设 max_retries=0；若保留 SDK 重试，需按其退避、总请求数与每个 HTTP 请求的 Token 预算作保守计数，或在 SDK 下层限流。上界只限制总次数，不保证这些请求落在正确的 RPM/TPM 窗口。

~~~mermaid
flowchart LR
    A["应用尝试：最多 3 次"] --> S["每次调用 SDK"]
    S --> H0["初始 HTTP 请求"]
    H0 -->|SDK 判断可重试| H1["内部重试 1"]
    H1 -->|仍可重试| H2["内部重试 2"]
    A -."下一次应用尝试".-> S
~~~

以下轨迹使用 `max_retries=0` 的假客户端，一次 `create` 对应一次 HTTP 请求；迟到响应例外见下节。

| 合成调用轨迹 | `max_attempts` | 实际 HTTP 请求 | 结束状态 |
|---|---:|---:|---|
| 429 后成功 | 3 | 2 | 恢复成功 |
| 连续 503 | 3 | 3 | 达应用尝试上限 |
| `Retry-After=2s`，总截止只余 0.05s | 3 | 1 | 不启动下一次请求 |
| 请求开始后用户取消 | 3 | 1 | 停止本地等待与重试 |
| 10ms 单次时限，底层取消清理 40ms | 3 | 1 | 本地约 50ms 后拒收迟到响应，不再重发 |

截至 2026-11-09，OpenAI 官方 Python SDK 文档列出的默认重试包括若干连接错误、408、409、429 和 5xx，构造器默认 `max_retries=2`。响应状态 429 本身不足以判定可重试：官方文档区分 `slow_down` 这种临时速率错误与需要处理的额度、账单限制。错误码和请求 ID 应进入结构化日志，敏感提示词正文不应为了排障复制进日志；部署时要核对实际 SDK 版本和调用路径。

> [!warning] 生成请求的超时结果可能未知
> 客户端发送请求后若断线或超时，服务端可能仍在完成计算。再发一次可能生成不同答案、重复费用或重复触发后续业务步骤。只有纯生成阶段且产品接受重复成本时，才考虑重试这类不确定结果；工具副作用应先走可核对的操作状态或幂等契约。取消本地任务不能证明远端计算已停止；异步客户端还须响应取消，传输层时限也要覆盖 SDK 等待。

## 可选：用假客户端复算请求数

> [!example]- 完整可运行的异步假客户端
> 下面的 Python 代码只演示应用级尝试预算：假客户端每次 create 对应一次模拟 HTTP 请求，不含 SDK 内部重试、RPM/TPM 队列或共享配额协调。真实客户端需把可恢复错误映射成同一异常，并明确 SDK 自动重试策略。
>
> ~~~python
> import asyncio
> import random
>
>
> class ApiError(Exception):
>     def __init__(self, status, code, *, retry_after=None, retryable=False):
>         super().__init__(f"{status} {code}")
>         self.status = status
>         self.code = code
>         self.retry_after = retry_after
>         self.retryable = retryable
>
>
> class DeadlineExceeded(TimeoutError):
>     pass
>
>
> class OutcomeUnknown(TimeoutError):
>     pass
>
>
> class LateResponse(TimeoutError):
>     pass
>
>
> class FakeAPI:
>     """每次 create 调用恰好计为一次模拟 HTTP 请求。"""
>     def __init__(self, outcomes):
>         self.outcomes = list(outcomes)
>         self.requests = 0
>
>     async def create(self, payload):
>         self.requests += 1
>         await asyncio.sleep(0)
>         if not self.outcomes:
>             raise AssertionError("假客户端没有预设响应")
>         outcome = self.outcomes.pop(0)
>         if isinstance(outcome, BaseException):
>             raise outcome
>         return outcome
>
>
> class SlowCleanupAPI:
>     """模拟收到取消后仍需 40ms 清理才返回的 transport。"""
>     def __init__(self):
>         self.requests = 0
>
>     async def create(self, payload):
>         self.requests += 1
>         try:
>             await asyncio.sleep(10)
>         except asyncio.CancelledError:
>             await asyncio.sleep(0.04)
>             return {"late": True}
>
>
> async def bounded_call(
>     client,
>     payload,
>     *,
>     max_attempts,
>     total_timeout_s,
>     attempt_timeout_s,
>     base_delay_s=0.05,
>     max_delay_s=1.0,
>     jitter_s=0.02,
>     rng=None,
> ):
>     if max_attempts < 1:
>         raise ValueError("max_attempts 必须至少为 1")
>     if total_timeout_s <= 0 or attempt_timeout_s <= 0:
>         raise ValueError("超时必须为正数")
>
>     rng = rng or random.Random()
>     loop = asyncio.get_running_loop()
>     deadline = loop.time() + total_timeout_s
>
>     for attempt in range(1, max_attempts + 1):
>         remaining = deadline - loop.time()
>         if remaining <= 0:
>             raise DeadlineExceeded("总截止时间已过，未开始下一次请求")
>
>         attempt_deadline = min(deadline, loop.time() + attempt_timeout_s)
>         try:
>             response = await asyncio.wait_for(
>                 client.create(payload),
>                 timeout=max(0.0, attempt_deadline - loop.time()),
>             )
>         except asyncio.CancelledError:
>             # 用户取消或上游 Task 被取消：停止等待和重试。
>             raise
>         except ApiError as exc:
>             if loop.time() >= attempt_deadline:
>                 raise LateResponse(
>                     "底层在单次时限后抛出错误；不自动重试"
>                 ) from exc
>             if not exc.retryable or attempt == max_attempts:
>                 raise
>
>             remaining = deadline - loop.time()
>             if exc.retry_after is not None:
>                 # Retry-After 是最短等待时间。
>                 delay = max(exc.retry_after, 0) + rng.uniform(0, jitter_s)
>             else:
>                 backoff = min(max_delay_s, base_delay_s * (2 ** (attempt - 1)))
>                 delay = backoff + rng.uniform(0, jitter_s)
>
>             if delay >= remaining:
>                 raise DeadlineExceeded(
>                     "截止时间内没有空间等待后再开始下一次请求"
>                 ) from exc
>             await asyncio.sleep(delay)
>         except TimeoutError as exc:
>             # 请求可能已经到达服务端；示例默认不自动重发不确定结果。
>             raise OutcomeUnknown("单次请求超时；远端结果可能未知") from exc
>         else:
>             if loop.time() >= attempt_deadline:
>                 # wait_for 会等待底层协程处理取消；迟到响应不算按时成功，也不自动重发。
>                 raise LateResponse("底层协程在单次时限后才返回；不自动重发")
>             return response
>
>     raise AssertionError("循环只会返回或抛错")
>
>
> async def demo():
>     success_api = FakeAPI([
>         ApiError(429, "slow_down", retry_after=0.001, retryable=True),
>         {"chunk_id": "handbook-17", "embedding": [0.2, -0.1]},
>     ])
>     success = await bounded_call(
>         success_api,
>         {"text": "synthetic public CI rule"},
>         max_attempts=3,
>         total_timeout_s=1,
>         attempt_timeout_s=0.5,
>         jitter_s=0,
>     )
>     print("recovered:", success, "HTTP requests:", success_api.requests)
>
>     failed_api = FakeAPI([
>         ApiError(503, "server_is_overloaded", retryable=True),
>         ApiError(503, "server_is_overloaded", retryable=True),
>         ApiError(503, "server_is_overloaded", retryable=True),
>     ])
>     try:
>         await bounded_call(
>             failed_api,
>             {"text": "synthetic public CI rule"},
>             max_attempts=3,
>             total_timeout_s=1,
>             attempt_timeout_s=0.5,
>             base_delay_s=0.001,
>             max_delay_s=0.01,
>             jitter_s=0,
>         )
>     except ApiError as exc:
>         print("failed:", exc, "HTTP requests:", failed_api.requests)
>
>     deadline_api = FakeAPI([
>         ApiError(429, "slow_down", retry_after=2, retryable=True),
>     ])
>     try:
>         await bounded_call(
>             deadline_api,
>             {},
>             max_attempts=3,
>             total_timeout_s=0.05,
>             attempt_timeout_s=0.5,
>             jitter_s=0,
>         )
>     except DeadlineExceeded as exc:
>         print("deadline:", type(exc).__name__, "HTTP requests:", deadline_api.requests)
>
>     class SlowAPI:
>         def __init__(self):
>             self.requests = 0
>             self.started = asyncio.Event()
>
>         async def create(self, payload):
>             self.requests += 1
>             self.started.set()
>             await asyncio.sleep(10)
>
>     slow_api = SlowAPI()
>     task = asyncio.create_task(
>         bounded_call(
>             slow_api,
>             {},
>             max_attempts=3,
>             total_timeout_s=1,
>             attempt_timeout_s=0.5,
>         )
>     )
>     await slow_api.started.wait()
>     task.cancel()
>     try:
>         await task
>     except asyncio.CancelledError:
>         print("cancelled locally; started HTTP requests:", slow_api.requests)
>
>     late_api = SlowCleanupAPI()
>     loop = asyncio.get_running_loop()
>     started_at = loop.time()
>     try:
>         await bounded_call(
>             late_api,
>             {},
>             max_attempts=3,
>             total_timeout_s=0.5,
>             attempt_timeout_s=0.01,
>         )
>     except LateResponse as exc:
>         elapsed_ms = (loop.time() - started_at) * 1000
>         print(
>             "late result rejected:", type(exc).__name__,
>             "local wait ms:", round(elapsed_ms),
>             "HTTP requests:", late_api.requests,
>         )
>
>
> if __name__ == "__main__":
>     asyncio.run(demo())
> ~~~
>
> 假客户端依次得到 429 与成功响应，所以总共调用两次；连续三次 503 后停止，模拟请求数为三，恰好等于 max_attempts。收到 429 后若 Retry-After=2 秒而总截止时间只剩 0.05 秒，示例检查后立刻停止，不等待、不启动第二次请求。取消示例在请求开始后只停止本地协程；真实服务端可能仍继续工作。代码不验证 provider header 格式、不实现并发池或分布式速率限制，也不处理 SDK 例外类型；生产适配器要接入这些细节，不能把示例包装器称作完整限流器。慢清理假客户端的单次时限为 10ms，收到取消后清理 40ms；包装器本地约 50ms 后拒收迟到成功值，只发 1 次 HTTP 请求；迟到的可重试 API 错误也会被拒收，不进入重试。

## 截止时间、取消和流式输出怎样相互作用？

在入口收到请求时创建单调时钟截止点 D。排队、等待并发槽、等待 RPM/TPM、每次 HTTP 调用和退避都消耗同一个预算；从队列取出时用 D - now 算剩余时间，再把剩余预算交给调用层。不要在每次重试时重置为“再等 30 秒”，否则总耗时没有上界。

Python 的 `asyncio.wait_for` 到时会向被等待协程发出取消，再等待它处理取消；取消是协作式的，底层清理可能让本地等待越过 attempt 或总截止点。本例对迟到成功值和迟到的可重试 API 错误都抛出 `LateResponse`，不记作按时成功，也不自动重发；这仍不能保证 `bounded_call` 恰好在 D 返回。生产适配器要传播 `CancelledError`，并给 HTTP transport 配置自己的连接、读写时限。若用户界面必须在 D 前结束等待，由外层请求处理器在 D 返回超时状态，并把本地清理和远端结果核对放入独立、可追踪的生命周期；本例没有强制取消或后台任务管理器。

队列中尚未发出的任务被取消时，可以直接移除，不占用后续额度。已经开始的异步网络任务收到取消后，应用应停止等待和后续重试；但取消是否抵达提供方、提供方是否中止生成，以及已经使用的额度怎样结算，取决于接口和传输协议。业务层应把“已取消”“已完成”“结果未知”作为不同状态。若截止时间到期时还没有可靠响应，返回明确超时或可恢复状态，而不是伪造空答案。

非流式请求失败且没有输出时，新请求仍可能重新计费。流式请求以首个面向用户的内容片段交付为界；协议可能先发送建连或元数据事件，这些不代表已有内容交付。首段内容交付前的 HTTP 错误可按错误类型和剩余预算处理；已有部分内容交付到用户后若自动从头重试，会重复片段并混合两次生成。部分输出应保留为未完成状态，由界面显示中断并让用户明确选择继续、放弃或新建重试；是否可继续取决于当前 API 的会话/响应契约。应用应记录首个用户可见内容时间、结束事件、取消请求、调用尝试和服务端响应 ID。

离线批处理、在线请求重试和任务失败后的人工重跑不是一回事。[RAG 的分块与索引流程](../rag/rag-architecture-and-implementation.md)负责确定哪些文本被编码、索引与验证；本章只确定单个模型请求能否排队、占用配额、重试以及何时停止。[时延与成本测量](ai-latency-and-cost-optimization.md)记录所有尝试和失败费用，再以通过验收的成功任务作单位成本分母。供应商 Batch API 是可以延迟完成的独立作业接口，不会自动为在线调用补上上述截止时间和重试预算。

## 相关笔记

- [怎样从授权文档中检索并核验回答依据？](../rag/rag-architecture-and-implementation.md)：确定文档来源、embedding 契约和 RAG 证据流程。
- [如何测量并降低 AI 应用的时延与成本，同时守住任务质量？](ai-latency-and-cost-optimization.md)：统计时延、缓存和所有尝试的成功任务成本。
- [如何选择 AI 部署方式并安全回滚？](ai-deployment-patterns.md)：把测得的容量、尾延迟和成本交给部署决策。

> [!info]- 来源
> - **RPM、TPM、不同错误码和提供方响应头。** OpenAI，[Rate limits](https://developers.openai.com/api/docs/guides/rate-limits) 与 [Error codes](https://developers.openai.com/api/docs/guides/error-codes)，核对于 2026-11-09；当前说明速率限制可能按组织、项目和模型生效，响应头可提供剩余额度与重置时间，临时 slow_down、server_is_overloaded 与账户额度错误需要不同处理。文中的固定 60 RPM / 12,000 TPM 是合成算术例子。
> - **Python SDK 重试。** OpenAI，[Python SDK README](https://github.com/openai/openai-python#retries) 与 [API reference](https://developers.openai.com/api/reference/python)，核对于 2026-11-09；当前官方文档说明构造器默认 `max_retries=2`，常见可重试错误包括连接问题、408、409、429 和 5xx。版本、错误集、超时参数和 server hint 处理会变更，生产配置应查看部署版本。
> - **SDK 请求超时。** [OpenAI Python SDK README](https://github.com/openai/openai-python#timeouts)，核对于 2026-11-09；一次 SDK 请求的默认和细分连接/读写等待不等于涵盖排队、限流等待与重试的应用总截止时间。
> - **Python 协程超时的取消语义。** [Python 3.11 `asyncio.wait_for`](https://docs.python.org/3.11/library/asyncio-task.html#asyncio.wait_for)，核对于 2026-11-09；超时会请求取消被等待协程，并等待其处理取消，因此总等待可能超过配置时限。
> - **Retry-After 的协议语义。** IETF，[RFC 9110 §10.2.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3)，2022；字段表示服务端建议的最早等待时长或日期，本章按最小等待要求处理。
