# 请求受理后，怎样保证任务最终被执行且不被两个 worker 同时推进？

客户点下“提交”之后，服务要做到两件事：这项任务最终一定有人执行，而且任何时刻只有一个 worker 有权推进它。本章沿用[一次 AI 运行断线或崩溃后，凭什么恢复](run-identity-and-authoritative-state.md)中的退款案例，从客户的提交走到 `run-o73-1` 等待客户确认方案 `Q-204`，对应状态机总图中 `accepted → queued → running → awaiting_approval` 这一段，以及 worker 崩溃时由谁接手。

## 客户的提交怎样变成唯一的 `runId`？

客户端用 `POST /runs` 提交“订单 `O-73` 的商品坏了，请退款”，请求头带 `Idempotency-Key: cli-o73-1`。服务端把四样东西绑定在一起：调用者 `cust-55`、资源范围（订单 `O-73`）、键值 `cli-o73-1`，以及规范化请求内容的摘要 `request_digest`。之后的同一提交按这组绑定处理：

| 再次到达的提交 | 服务端的处理 |
|---|---|
| 同一调用者、同一范围、同一键、同一摘要 | 返回原来的 `run-o73-1`，不新建运行 |
| 同一键，但摘要不同（例如改了订单或诉求） | 返回冲突；不能借用旧运行，也不能新建第二个动作 |
| 换了新键 | 可能创建第二个运行；去重只在客户端沿用原键时成立 |

`request_digest` 只识别原始请求。之后客户确认的退款方案另有 `plan_digest`，两者不能互相代替：同一个请求可能先后生成不同版本的方案。

这项保证不是 HTTP 自带的。`POST` 本身不是幂等方法；同一提交重复到达时返回原运行，是应用为 `POST /runs` 定义的去重契约。两份相同提交并发到达时，由幂等记录上的唯一约束裁决只建出一个 `run-o73-1`，输家读回它，裁决方式见[两个请求争夺最后一件库存时，怎样保证只预留一次？](../../engineering-foundations/data/conditional-writes-and-idempotent-records.md)；方法幂等与幂等键的区别和去重窗口见[写请求超时后，怎样查清结果并安全重试？](../../engineering-foundations/services/deadlines-retries-and-unknown-outcomes.md#方法幂等和幂等键有什么不同？)。

## 返回 `202 Accepted` 之前要存下什么？

服务只在运行记录、请求摘要和待发布的 outbox 事件都持久化之后，才返回：

```text
202 Accepted
{"runId": "run-o73-1", "status": "accepted"}
```

RFC 9110 中的 `202` 只表示请求已被接受处理，不表示处理完成，也不承诺一定成功（与 `201` 的区别见[耗时任务怎样被持久受理？](../../engineering-foundations/services/durable-job-acceptance-and-outbox.md#201%20和%20202%20承诺的是不同的事)）。客户端拿到它，只知道以后可以用 `run-o73-1` 查询；业务去重和入队恢复都由应用自己实现。如果这个回执在路上丢了，客户端连 `runId` 都没有，怎样找回同一个运行，见[用户断线、取消或要回答一个问题时，同一次运行怎样继续](disconnect-cancel-and-user-input.md)。

## 运行记录写了，唤醒消息怎样保证发出去？

运行记录在数据库里，队列消息在消息系统里，分两步写就可能在两步之间崩溃，留下一个永远没人唤醒的运行。这里用 transactional outbox (事务发件箱)：运行记录和待发布事件在同一事务里提交，发布器之后可以反复投递，直到确认送达；各崩溃时点会怎样，见[耗时任务怎样被持久受理，并保证一定会被唤醒？](../../engineering-foundations/services/durable-job-acceptance-and-outbox.md#数据库和消息代理之间的缺口怎样补上？)。

落到运行上有两条约定。发布器先把运行从 `accepted` 条件改为 `queued`，保留待发送事件，再投递消息，所以 worker 收到消息时不会遇到还没入队的 `accepted` 运行。发布器重复投递时，重复消息唤醒的是同一个 `queued` 运行，由下一节的条件领取保证只有一个 worker 能领到。发布确认和消费者确认各证明什么，见[发布确认、消费者确认和业务完成各证明什么？](../../engineering-foundations/services/queue-delivery-and-acknowledgement.md)。

## worker 怎样领取运行，旧 worker 怎样被挡在外面？

队列消息只负责唤醒，执行权由数据库里的条件领取、lease (租约) 和只增不减的代次决定。worker A 收到唤醒后，用一笔条件事务领取运行：只有运行仍是 `queued`、代次等于消息预期的值、且没有有效 lease 时，才把它改为 `running`，代次加一成为 attempt 1，并写入 lease 持有者和到期时间；两个 worker 同时收到重复消息，只有一个能成功。代次就是 fencing token (栅栏令牌)：之后每次写入都以它为条件，新代次一旦被领取，旧 worker 就写不进运行记录。lease 到期不会杀死旧进程，lease 是否有效要在取得行锁之后按数据库的实际时间判断（PostgreSQL 中是 `clock_timestamp()`，不是事务开始时刻的 `CURRENT_TIMESTAMP`）；这些通用规则见[怎样保证一个任务同一时刻只由一个 worker 推进？](../../engineering-foundations/services/job-claims-leases-and-fencing.md)。

运行在这套规则上多了两点。第一，attempt 1 每推进一次本地状态（保存观察、保存检查点、改状态），都要在一笔短事务里重新核验四件事：运行处在预期状态、当前代次仍是 1、lease 尚未过期、运行没有被取消。核验失败就回滚并停止，不再写任何记录。事务要短小，不能在持锁期间等模型或网络。第二，栅栏只挡本地写入，撤不回旧进程已经发出的远端请求，例如一次已经发出的退款；这类效果靠操作账本和对账收尾，见下文扫描器一节。

## 一步做完后，先写检查点还是先确认消息？

先写检查点，再确认消息：确认前崩溃，消息会重投，新 attempt 从检查点继续；先确认后写检查点，确认后崩溃就丢掉这一步。这条“持久化之后才确认”的规则和各崩溃时点见[发布确认、消费者确认和业务完成各证明什么？](../../engineering-foundations/services/queue-delivery-and-acknowledgement.md#consumer%20ACK%20的规则)。

本例中，attempt 1 执行 `call-r1` 读到订单与资格，保存这组观察；模型经 `call-r2` 提出退款，应用核验后生成方案 `Q-204`。接着 attempt 1 在一笔条件事务中核验 `running`、代次 1 和有效 lease，然后一并保存三样东西：不可变的待审方案（含 `plan_digest`）、检查点、`awaiting_approval` 状态，同时结束自己的 lease。这笔事务失败，就没有等待确认的方案；事务成功后，等待确认期间没有任何执行 lease，客户在任何设备上看到的都是同一个 `Q-204`。

`awaiting_approval` 只能由针对当前待审版本的决定唤醒：客户确认时，同一事务写入确认记录、把运行改回 `queued` 并写一条 outbox 唤醒；拒绝写 `rejected`，取消写 `canceled`，都不入队；迟到、重复或针对旧版本的确认不能让运行重新入队。确认事务里还要锁订单、消费 `Q-204` 并保存退款操作 `R-204`，这些写入细节见[退款请求超时后，怎样查清结果而不重复扣款](external-writes-and-reconciliation.md)。

> [!example] 变体：attempt 1 在保存方案前崩溃
> 设 worker A 保存了 `call-r1` 的观察后进程消失，还没来得及保存 `Q-204`。消息未被确认，lease 到期后，扫描器发现这个运行处在 `running`、操作账本里没有任何发送意图，于是条件地把它改回 `queued` 并写一条普通 outbox 唤醒。worker B 收到唤醒，领取 attempt 2，从检查点读到已有的订单观察，接着调用模型生成方案。如果 worker A 之后醒来，它的代次 1 已经过时，任何写入都会被条件事务拒绝。本主线的主路径假设没有这次崩溃，所以发送由 attempt 2 负责。

## 扫描器怎样处理租约过期的运行？

worker 确认消息后才崩溃，就不会再有重投，这时要靠扫描器发现租约过期的运行。核对代次与租约、取消优先、再决定失败或重排，这套通用的恢复顺序见[任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？](../../engineering-foundations/services/job-retries-cancellation-and-cleanup.md#重试与恢复按什么顺序决定？)。运行多出的一条是：扫描器不能把所有过期运行都放回 `queued`，一个已经登记发送意图的运行若被当成普通任务重跑，就可能再发一次退款。它按持久状态分流：

| 过期时的状态 | 扫描器的条件变更 | 之后由谁推进 |
|---|---|---|
| `running`，操作账本中没有任何发送意图 | 改为 `queued`，写普通 outbox | 执行 worker 原子领取下一 attempt，从检查点继续 |
| `effect_in_flight` | 保留原操作键、请求摘要和全部发送意图，改为 `effect_unknown`，写对账 outbox | 对账 worker 领取下一 attempt，只读查询 |
| `effect_unknown`、`provider_pending` 或 `cancel_requested` 中，对账 attempt 的 lease 过期 | 保持原状态，写一条新的对账 outbox | 下一个对账 worker；沿用原键和累计的全部发送意图 |
| `awaiting_input`、`awaiting_approval` | 不处理：这两个挂起状态本来就没有执行 lease | 前者只由答复、超时或取消事务推进，后者只由确认、拒绝或取消事务推进 |

扫描器只做条件状态变更和 outbox 写入。它不领取 lease、不增加代次，也不查询远端；领取永远由收到唤醒的 worker 完成。这样，若原 attempt 恰好在扫描前成功提交，扫描器读到的就是新状态；若扫描和唤醒之后新 worker 先领取，旧 attempt 就会因代次不符而失效。

对账 worker 收到重复唤醒时，只有在运行仍处于该分支、消息预期的代次相符、且按数据库实际时间确认现有 lease 已过期或为空时，才能领取下一代；并发的重复消息只有一条能成功。对账一轮查不出结论时，worker 在确认消息之前，必须持久安排下一次只读处理，或指定一位人工责任人。转人工的项目永远不自动重放。

## 什么时候可以把运行记为 `failed`？

只有在没有任何未知外部效果时。例如 attempt 1 读订单时发现订单不存在，或方案生成反复违反格式而达到上限，且操作账本里没有发送意图，运行可以保存错误并记为 `failed`。一旦登记过发送意图，哪怕请求很可能没发出，也不能把“结果未知”伪装成普通失败，它必须走 `effect_unknown` 的对账路径。

## 只被一个 attempt 推进之后，才轮到外部写入

到这里，客户的一次提交变成了唯一的 `run-o73-1`：outbox 保证它会被唤醒，条件领取和递增的代次保证任一时刻只有一个 attempt 能推进它，扫描器按持久状态把过期运行送回正确的分支。运行停在 `awaiting_approval`，等客户确认 `Q-204`。确认之后，attempt 2 要把这份方案变成一次真正的退款请求，而请求一旦超时，结果就可能不明。怎样在这种情况下查清结果而不重复退款，是[退款请求超时后，怎样查清结果而不重复扣款](external-writes-and-reconciliation.md)的问题。

> [!info]- 来源
>
> - **`202 Accepted` 只表示接受处理；`POST` 不是幂等方法**（“返回 `202 Accepted` 之前要存下什么”“客户的提交怎样变成唯一的 `runId`”）。IETF，[RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，2022，§9.2.2（幂等方法与失败后重试）、§15.3.3（`202 Accepted`），核对日期 2026-11-06。`POST /runs` 的幂等键是应用契约，不是该 RFC 提供的保证。
