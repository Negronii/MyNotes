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

这项保证不是 HTTP 自带的。`POST` 本身不是幂等方法；同一提交重复到达时返回原运行，是应用为 `POST /runs` 定义的去重契约。幂等键的一般设计见[请求超时后如何确认结果并安全重试](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md)。

## 返回 `202 Accepted` 之前要存下什么？

服务只在运行记录、请求摘要和待发布的 outbox 事件都持久化之后，才返回：

```text
202 Accepted
{"runId": "run-o73-1", "status": "accepted"}
```

RFC 9110 中的 `202` 只表示请求已被接受处理，不表示处理完成，也不承诺一定成功。客户端拿到它，只知道以后可以用 `run-o73-1` 查询；业务去重和入队恢复都由应用自己实现。如果这个回执在路上丢了，客户端连 `runId` 都没有，怎样找回同一个运行，见[用户断线、取消或要回答一个问题时，同一次运行怎样继续](disconnect-cancel-and-user-input.md)。

## 运行记录写了，唤醒消息怎样保证发出去？

运行记录在数据库里，队列消息在消息系统里。如果分两步写，进程可能恰好在两步之间崩溃：运行记录已经存在，却永远没有 worker 被唤醒。

常见做法是 transactional outbox（事务发件箱）：在同一个数据库事务里写入运行记录和一条待发布的 outbox 事件。之后由发布器把事件投递到队列：

1. 发布器先把运行从 `accepted` 条件改为 `queued`，保留待发送事件，再投递消息。这样 worker 收到消息时，不会遇到还没入队的 `accepted` 运行。
2. 若发布器在投递前崩溃，重启后仍能找到这条未发送的事件，重新投递。
3. 若在投递之后、标记“已发送”之前崩溃，同一条消息会被再投一次。重复消息唤醒的是同一个 `queued` 运行，由下一节的条件领取保证只有一个 worker 能领到。

如果运行记录和 outbox 无法放进同一个事务，就需要等价的可恢复入队协议，再加一个扫描修复任务。消息系统的发布确认和消费者确认各证明什么，见[报表任务的发布确认、消费者确认与业务完成各证明什么](../../engineering-foundations/reliability/queue-delivery-and-acknowledgement.md)。

## worker 怎样领取运行，旧 worker 怎样被挡在外面？

队列消息只负责唤醒，真正的执行权由数据库里的租约决定。worker A 收到唤醒后，用一笔条件事务原子地领取运行：只有运行仍是 `queued`、代次等于消息预期的值、且没有有效 lease 时，才把它改为 `running`，代次加一成为 attempt 1，并写入 lease 持有者和到期时间。两个 worker 同时收到重复消息，只有一个能让这笔条件更新成功。

领取只是开始。之后 attempt 1 每推进一次本地状态（保存观察、保存检查点、改状态），都要在一笔短事务里重新核验四件事：运行处在预期状态、当前代次仍是 1、lease 尚未过期、运行没有被取消。核验失败就回滚并停止，不再写任何记录。事务要短小，不能在持锁期间等模型或网络。

代次只增不减，这正是它能当 fencing token（栅栏令牌）的原因：一旦有新代次被领取，持有旧代次的 worker 写不进运行记录。但 lease 也有两件事做不到：它不会杀死旧进程，也撤不回旧进程已经发出的远端请求。

“核验 lease 尚未过期”要用数据库在取得行锁之后读到的实际时间，下面的实例说明为什么。

> [!example] 实例：PostgreSQL 14 上怎样核验租约
> PostgreSQL 的 `CURRENT_TIMESTAMP` 是事务开始时刻，`clock_timestamp()` 才是调用时的实际时间。在 PostgreSQL 14.24 上复现时，直接执行 `UPDATE ... WHERE lease_until > clock_timestamp()`，即使这条语句等待过行锁，仍可能推进一个已经过期的租约。可靠的写法是先取得这一行的更新权，再读时钟并核验：
>
> ```sql
> BEGIN;
> -- 1. 先取得这一行的更新权（可能要等别的事务释放行锁）
> SELECT status, attempt, lease_until, cancel_requested
>   FROM runs WHERE run_id = 'run-o73-1' FOR UPDATE;
> -- 2. 锁到手之后，再读数据库的实际时间
> SELECT clock_timestamp();
> -- 3. 应用核验：status = 'running'、attempt = 1、
> --    lease_until 晚于刚读到的时间、未取消；任一不符就 ROLLBACK 并停止
> UPDATE runs SET status = 'awaiting_approval', lease_owner = NULL, lease_until = NULL
>  WHERE run_id = 'run-o73-1';
> COMMIT;
> ```
>
> 这段 SQL 是本例的示意，表名和列名由应用约定。它只保证本地持久状态的推进次序，不提供任何远端副作用保证。

## 一步做完后，先写检查点还是先确认消息？

先写检查点，再确认消息。若 worker 在确认前崩溃，消息会被重投，新的 attempt 从检查点继续，不会丢失已经完成的工作；若反过来先确认、后写检查点，确认后崩溃就会丢掉这一步。

本例中，attempt 1 执行 `call-r1` 读到订单与资格，保存这组观察；模型经 `call-r2` 提出退款，应用核验后生成方案 `Q-204`。接着 attempt 1 在一笔条件事务中核验 `running`、代次 1 和有效 lease，然后一并保存三样东西：不可变的待审方案（含 `plan_digest`）、检查点、`awaiting_approval` 状态，同时结束自己的 lease。这笔事务失败，就没有等待确认的方案；事务成功后，等待确认期间没有任何执行 lease，客户在任何设备上看到的都是同一个 `Q-204`。

`awaiting_approval` 只能由针对当前待审版本的决定唤醒：客户确认时，同一事务写入确认记录、把运行改回 `queued` 并写一条 outbox 唤醒；拒绝写 `rejected`，取消写 `canceled`，都不入队；迟到、重复或针对旧版本的确认不能让运行重新入队。确认事务里还要锁订单、消费 `Q-204` 并保存退款操作 `R-204`，这些写入细节见[退款请求超时后，怎样查清结果而不重复扣款](external-writes-and-reconciliation.md)。

> [!example] 变体：attempt 1 在保存方案前崩溃
> 设 worker A 保存了 `call-r1` 的观察后进程消失，还没来得及保存 `Q-204`。消息未被确认，lease 到期后，扫描器发现这个运行处在 `running`、操作账本里没有任何发送意图，于是条件地把它改回 `queued` 并写一条普通 outbox 唤醒。worker B 收到唤醒，领取 attempt 2，从检查点读到已有的订单观察，接着调用模型生成方案。如果 worker A 之后醒来，它的代次 1 已经过时，任何写入都会被条件事务拒绝。本主线的主路径假设没有这次崩溃，所以发送由 attempt 2 负责。

## 扫描器怎样处理租约过期的运行？

worker 确认消息后才崩溃，就不会再有重投，这时要靠扫描器发现租约过期的运行。扫描器不能把所有过期运行都放回 `queued`：一个已经登记发送意图的运行，若被当成普通任务重跑，就可能再发一次退款。它按持久状态分流：

| 过期时的状态 | 扫描器的条件变更 | 之后由谁推进 |
|---|---|---|
| `running`，操作账本中没有任何发送意图 | 改为 `queued`，写普通 outbox | 执行 worker 原子领取下一 attempt，从检查点继续 |
| `effect_in_flight` | 保留原操作键、请求摘要和全部发送意图，改为 `effect_unknown`，写对账 outbox | 对账 worker 领取下一 attempt，只读查询 |
| `effect_unknown`、`provider_pending` 或 `cancel_requested` 中，对账 attempt 的 lease 过期 | 保持原状态，写一条新的对账 outbox | 下一个对账 worker；沿用原键和累计的全部发送意图 |
| `awaiting_approval` | 不处理：这个状态本来就没有执行 lease | 只由确认、拒绝或取消事务推进 |

扫描器只做条件状态变更和 outbox 写入。它不领取 lease、不增加代次，也不查询远端；领取永远由收到唤醒的 worker 完成。这样，若原 attempt 恰好在扫描前成功提交，扫描器读到的就是新状态；若扫描和唤醒之后新 worker 先领取，旧 attempt 就会因代次不符而失效。

对账 worker 收到重复唤醒时，只有在运行仍处于该分支、消息预期的代次相符、且按数据库实际时间确认现有 lease 已过期或为空时，才能领取下一代；并发的重复消息只有一条能成功。对账一轮查不出结论时，worker 在确认消息之前，必须持久安排下一次只读处理，或指定一位人工责任人。转人工的项目永远不自动重放。

## 什么时候可以把运行记为 `failed`？

只有在没有任何未知外部效果时。例如 attempt 1 读订单时发现订单不存在，或方案生成反复违反格式而达到上限，且操作账本里没有发送意图，运行可以保存错误并记为 `failed`。一旦登记过发送意图，哪怕请求很可能没发出，也不能把“结果未知”伪装成普通失败，它必须走 `effect_unknown` 的对账路径。

## 只被一个 attempt 推进之后，才轮到外部写入

到这里，客户的一次提交变成了唯一的 `run-o73-1`：outbox 保证它会被唤醒，条件领取和递增的代次保证任一时刻只有一个 attempt 能推进它，扫描器按持久状态把过期运行送回正确的分支。运行停在 `awaiting_approval`，等客户确认 `Q-204`。确认之后，attempt 2 要把这份方案变成一次真正的退款请求，而请求一旦超时，结果就可能不明。怎样在这种情况下查清结果而不重复退款，是[退款请求超时后，怎样查清结果而不重复扣款](external-writes-and-reconciliation.md)的问题。

> [!info]- 来源
>
> - **`202 Accepted` 只表示接受处理；`POST` 不是幂等方法**（“返回 `202 Accepted` 之前要存下什么”“客户的提交怎样变成唯一的 `runId`”）。IETF，[RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，2022，§9.2.2（幂等方法与失败后重试）、§15.3.3（`202 Accepted`），核对日期 2026-11-06。`POST /runs` 的幂等键是应用契约，不是该 RFC 提供的保证。
> - **事务时间与实际时间、行锁等待**（“实例：PostgreSQL 14 上怎样核验租约”）。PostgreSQL 14，[Date/Time Functions](https://www.postgresql.org/docs/14/functions-datetime.html) 区分事务开始时的 `CURRENT_TIMESTAMP` 与调用时读取实际时间的 `clock_timestamp()`；[Explicit Locking](https://www.postgresql.org/docs/14/explicit-locking.html) 说明竞争事务会等待行锁。取锁后复核的时序在 PostgreSQL 14.24 上复现过；这是本地持久状态事务的实现依据，不是远端副作用保证。
