# 任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？

前两章讲了顺利的路径：条件领取、fencing (栅栏)、成功提交、ACK。本章处理三类不顺利的情况，并回答它们共同的问题：由谁、按什么顺序把 job 推到终态或下一轮，怎样保证不重复执行，也不留下没人管的对象。三类情况是：attempt (执行尝试) 遇到可重试的错误；用户对 `/v1/jobs/job-demo-731` 发了 `DELETE`；worker 失联、租约到期。沿用主线四的导出案例和[持久受理一章](durable-job-acceptance-and-outbox.md#job%20状态机与%20outbox%20各有自己的生命周期)的状态机：五个状态，`cancel_requested` 是标志，每个 job 最多 3 次 attempt（含首次）。

## 谁来决定 job 的下一步？

有三个角色可能改变一个已受理 job 的命运：

- **持有当前 attempt 的 worker**：遇到错误或看到取消请求时；
- **租约恢复器**：一个独立的进程，扫描租约已过期的 `running` job，取得竞争接管的资格；
- **API**：处理用户的取消请求。

它们之间没有消息往来，只通过同一行 job 竞争。每个角色的每次写入都带着它看到的状态和 attempt 作为条件，谁先提交谁说了算，后来者更新零行、重读再决定。这就是[领取与栅栏一章](job-claims-leases-and-fencing.md#栅栏：怎样挡住醒来的旧%20worker？)的栅栏原理用在收尾上。

恢复器也需要最小权限：它只读扫描和竞争所需的 job 标识、状态、attempt、租约到期时间和取消标志，能做条件接管、预留等待槽、写恢复用的 outbox (事务发件箱) 意图或终态；它不读报表内容，也不直接向 broker (消息代理) 发布。网络、身份与数据权限的分层见[服务该跑在哪种运行时上](../practice/production-runtime.md)。

## 重试与恢复按什么顺序决定？

worker 遇到可重试的暂时错误并停止当前工作之后，或者恢复器发现租约过期之后，都按**同一个顺序**判断，第一条成立就停下：

1. **核对当前 attempt。** 锁住 job 行，确认它仍是 `running`，attempt 仍是自己看到的那一代（恢复器还要用 `clock_timestamp()` 确认租约确实已过期）。不是，就说明别人已经做了决定，自己什么都不写，重读后按新状态处理手上的消息。
2. **有取消请求，落 `cancelled`。** 取消优先于任何重试。同时提交对已上传对象的清理或保留决定（见本章最后一节）。
3. **永久错误或 attempt 已到上限，落 `failed`。** 不可重试的业务错误写对应的有限错误码；`attempt >= max_attempts` 写 `attempts_exhausted`。
4. **否则，只有预留到等待槽才能重排。** 在同一个事务里：占一个等待槽，把 job 改回 `queued`，写入退避后的 `available_at`，清掉旧租约，插入一条新的 `pending` outbox 意图。等待槽已满，就落 `failed` 加 `capacity_exhausted`。

第 4 步的事务如下（第 1 步已在同一事务里 `SELECT ... FOR UPDATE` 锁住 job 行并完成前三项判断）：

~~~sql
-- 占一个等待槽；返回零行说明 240 个槽已满，改走 capacity_exhausted
UPDATE admission_budget
SET waiting_count = waiting_count + 1
WHERE pipeline = 'report-export' AND waiting_count < 240
RETURNING waiting_count;

UPDATE report_jobs
SET status = 'queued',
    available_at = clock_timestamp() + :backoff,
    lease_expires_at = NULL,
    holds_waiting_slot = true
WHERE job_id = :job_id AND status = 'running' AND attempt = :observed_attempt;

INSERT INTO report_outbox(job_id, state) VALUES (:job_id, 'pending');
COMMIT;
~~~

`:backoff` 用带上限的指数退避加全抖动计算，公式和参数含义见[重试要等多久、最多试几次](deadlines-retries-and-unknown-outcomes.md#重试要等多久、最多试几次？)。重排只占等待槽，不消耗新 job 的速率令牌：令牌限制的是新逻辑 job 的到达速度，重排不是新 job。等待槽怎样计数见[容量章](capacity-admission-and-backpressure.md)。

提交之后，才可以 ACK 旧的那条投递：新的可执行时间、槽位和唤醒意图都已持久，新一轮有了自己的唤醒。relay (中继) 按 `available_at` 到期再发布新意图；如果旧消息或别的重复消息提前到达，领取条件 `available_at <= clock_timestamp()` 会拦住它。只有到期唤醒已持久安排好，早到的重复消息才可以被确认。

用三个具体走向检查这个顺序：

- attempt 1 遇到暂时错误，停下业务操作，预留到槽并写退避唤醒；attempt 2 成功。job 最终 `succeeded`。
- attempt 1、2、3 依次失败或失联。第三次之后的判断走到第 3 步，写 `failed / attempts_exhausted`，不再预留第四次。
- attempt 1 失联时 240 个槽恰好占满。恢复器走到第 4 步拿不到槽，写 `failed / capacity_exhausted`。这是一个持久终态，可以查询，而不是靠 broker 无限重投把压力变成看不见的积压。

“最多 3 次”限制的是**启动**次数，不保证旧 attempt 立刻停下。被栅栏的 attempt 仍可能占着资源运行一段时间；限制这种重叠持续多久的，是每页读取和上传的 deadline 以及可观察的停止路径。

这套顺序还有一个活性前提：relay、broker、worker、数据库在故障之后最终会恢复并取得进展，租约扫描持续在跑。任何一个组件长期不可用，job 都无法推进；已排队的 job 继续占着等待槽，槽满之后 API 在受理前拒绝新 job。

## 为什么重试不能靠把消息退回队列？

最直接的“重试”做法，是处理失败时把当前投递退回 broker（例如 RabbitMQ 的 `nack(requeue=true)`），指望它再来一次就变成下一次 attempt。这行不通：

- job 仍是 `running`，下一次投递到来时，条件领取要求 `status = 'queued'`，会拒绝它；
- 快速退回、快速重投，会形成热循环，把 broker 和 worker 一起拖慢；
- 它绕过了上一节的全部判断：不检查取消，不累计 attempt，不占等待槽，没有退避。

正确的做法就是上一节的持久重排：先在数据库里决定并提交下一步，再 ACK 旧投递。其他几种错误的处置：

- **不可重试的业务错误**：以 job 仍是自己这一代的 `running` 且未请求取消为条件，提交 `failed` 和有限错误码，然后 ACK。如果条件不成立（取消已被请求，或别的转移先提交了），重读 job，走对应的分支。
- **格式错误、或对应不到有效 job 的消息**：不能无限重排，隔离到配置好的 dead-letter queue (死信队列)，或走会触发告警的拒绝路径。

退回投递只适合一种情况：worker 手上有一条**还没开始处理**的预取投递，要把它还给 broker（见[prefetch 一节](queue-delivery-and-acknowledgement.md#prefetch%20限制的是什么？)）。

## 恢复器先提交时会走哪条分支？

租约到期之后，恢复器和原 worker 可能同时动作。如果原 worker 的成功事务先提交，job 就是 `succeeded`，恢复器读到终态后什么都不做。如果恢复器先提交，按上面的决策顺序，`job-demo-731` 会落进下面某一行：

| 恢复器读到的情况 | 持久状态变化 | 等待槽与 outbox | 旧投递 |
| --- | --- | --- | --- |
| 有取消请求 | `running → cancelled`，同时提交对象清理或保留决定 | 不占槽 | 决定提交后可 ACK |
| attempt 已到 3 | `running → failed`，`error_code = 'attempts_exhausted'` | 不占槽、不写 outbox | 提交后可 ACK |
| 未取消、还有额度，但 240 个槽已满 | `running → failed`，`error_code = 'capacity_exhausted'` | 不占槽、不写 outbox | 提交后可 ACK |
| 未取消、还有额度、有空槽 | `running → queued`，清除旧租约，写退避后的 `available_at` | 预留一个槽，插入新的 `pending` outbox | 三者都提交后可 ACK |

最后一种情况之后，新的 worker B 领取 attempt 2；A 若再醒来提交 attempt 1 的结果，会因状态或 attempt 不匹配而更新零行（时序见领取与栅栏一章）。恢复器不需要“杀死” A，也做不到：它只改变 A 能写进数据库的东西。

## 取消和领取同时发生，谁赢？

用户的 `DELETE /v1/jobs/job-demo-731` 表达的是“请求停止”。服务怎样处理，取决于 job 此刻处于哪个状态，以及取消和领取谁先提交。规则如下：

- **job 还是 `queued`。** API 用一个条件事务把它改成 `cancelled`，提交对象的清理或保留决定（之前的 attempt 可能已上传过对象），并**只归还一次**它占着的等待槽。此后无论有多少条唤醒消息到达，worker 只会读到终态，不会领取、也不会增加 attempt。
- **领取先提交了。** 等待槽已在领取时归还，API 不能再还一次。它只能对 `running` 的 job 写 `cancel_requested = true`，返回的表示里状态仍是 `running`，带 `cancelRequested: true`。
- **取消先提交了。** worker 的领取条件 `status = 'queued'` 不再成立，更新零行。

两种写入落在同一行上，由行锁和提交顺序选出唯一的胜者。API 的处理可以写成两条条件语句，按顺序尝试：

~~~sql
-- 1. queued 分支：取消并归还等待槽（同一语句，两处修改要么都生效要么都不生效）
WITH cancelled AS (
  UPDATE report_jobs
  SET status = 'cancelled', terminal_at = clock_timestamp(), holds_waiting_slot = false
  WHERE job_id = :job_id AND status = 'queued'
  RETURNING job_id
), released AS (
  UPDATE admission_budget
  SET waiting_count = waiting_count - 1
  WHERE pipeline = 'report-export' AND EXISTS (SELECT 1 FROM cancelled)
)
SELECT count(*) FROM cancelled;

-- 2. 上一条零行时：job 可能已被领取，只能登记取消请求
UPDATE report_jobs
SET cancel_requested = true
WHERE job_id = :job_id AND status = 'running';
~~~

两条都零行，说明 job 已经是终态（或在两条语句之间又被重排回 `queued`）：重读一次，已终态就原样返回当前状态，不改写；若又回到 `queued`，再走第 1 条。

**运行中的取消由谁落终态？** 持有当前 attempt 的 worker 在每个有限的工作步骤之间、以及成功提交之前检查取消标志。看到 `cancel_requested = true`，就以 job ID、`status = 'running'`、自己的 attempt 和取消标志为条件提交 `cancelled` 及清理或保留决定。它不归还等待槽（领取时已经还过），只在停止执行后释放自己的物理执行槽。

**worker 在提交取消之前失联了。** 取消请求留在数据库里，租约到期后由恢复器代写 `cancelled` 和同样的清理决定（上表第一行）。恢复器不会为了取消去抢等待槽。在这个决定持久化之前，旧投递不能 ACK：`cancel_requested` 只是请求，不是终态，也不是确认许可。

**取消和成功同时发生。** 仍由提交顺序决定唯一终态。取消标志先写入，成功提交的条件 `cancel_requested = false` 不成立，更新零行，worker 转去提交取消；成功先提交，取消端读到 `succeeded`，返回现有的成功状态，不改写终态。

## 什么能证明旧 attempt 已经停下？

下面这些事件**都不**证明旧 attempt 已经停止：

- 用户请求了取消；
- 进程收到了停止信号；
- 租约到期；
- 数据库已经栅栏了旧 attempt。

它们只改变“旧 attempt 能写进数据库什么”，不改变旧 attempt 的进程是否还在读数据、上传对象、占着连接。物理执行槽要等这个 attempt 真正停止、释放了它的连接、游标和上传句柄之后才归还；同一个 worker 进程可以继续运行别的 attempt，不必整个退出。“取消只是请求，完成信号只证明本层”这条原则见[一份工作该交给进程、线程还是异步 I/O](../runtime/processes-threads-and-async-io.md)；进程关停时怎样停止领取、不确认未完成的投递，见[服务进程收到停止信号后怎样排空工作](../runtime/graceful-shutdown.md)。

## 孤儿对象什么时候才能删？

对象存储不在数据库事务里。上传成功、数据库提交却失败（或更新零行），就会留下一个没有任何已提交 job 引用的对象，即孤儿。为了让孤儿可以安全识别和删除，先约定两件事：

- **对象键按 attempt 区分，且不可覆盖。** 例如 `reports/job-demo-731/attempt-1.csv` 与 `attempt-2.csv`。A 迟到的上传只会写到自己的键上，不会替换 B 的结果，也不会被用户下载。
- **逐个键检查引用，而不是看 job 有没有结果。** B 的键已经成为 job 的结果，A 的键仍是需要清理的孤儿；“job 已有结果”不能推出“这个 job 的所有对象都在用”。

真正难的是**什么时候删**。清理的计时起点，是数据库提交“该 attempt 已不是当前 attempt”（栅栏）或 job 终态的时刻，而不是租约到期的时刻。然后分三种情况：

| 运行环境能保证什么 | 清理方式 |
| --- | --- |
| 旧 attempt 在栅栏之后不会再发起新的上传，且栅栏生效时已在进行的上传有最长耗时上限 | 等过这个上限、对象存储的传播余量和安全宽限，再做一次清扫 |
| 停顿的旧进程仍可能在栅栏之后才开始上传 | 单次扫描不够。先撤销旧进程的写入权限或等它过期，再从它最后可能开始上传的时刻起，等过最长上传时间和宽限，做最终清扫 |
| 写入权限没有失效时间 | 持续重扫候选键 |

无论哪种情况，**每次删除之前都要重新确认**这个键没有被任何已提交的结果引用。还有一个例外：成功提交的 `COMMIT` 结果未知时，对象的结局未决，不能当孤儿删。

当前 attempt 确认停止、和异步回收孤儿是两项独立的责任。回收由独立的清理任务做，不需要为它继续占着 worker 的执行槽。

> [!info] 实例：S3 的条件写
> Amazon S3 支持带 `If-None-Match: *` 的条件写，同名对象已存在时拒绝写入，可以作为“按 attempt 区分的键不可覆盖”的存储侧保险。它只认对象名，不知道谁是当前 attempt，替代不了数据库栅栏；换别的对象存储时，按它自己的条件写语义设计。（核对于 2026-11-12）

## 本章产出与下一步

现在每条不顺利的分支都有确定的落点：可重试的失败按“attempt → 取消 → 永久错误或上限 → 等待槽”的顺序持久重排或终结；取消和领取由同一行上的条件写选出唯一胜者，等待槽只还一次；栅栏和租约都不证明旧 attempt 已停，物理槽跟着实际停止归还；孤儿对象按引用和写入时限分情况回收。

这些分支反复用到同一个资源：等待槽。重排要占槽，槽满就 `capacity_exhausted`，受理时槽满就在 202 之前拒绝。那么一条异步管线到底该有多少槽、多少执行槽、多快的准入速率？见[一条异步管线能接多少工作，超出时在哪里拒绝](capacity-admission-and-backpressure.md)。

> [!info]- 来源
> - 手动确认下未确认投递在 channel/connection 关闭后重新入队、自动确认在发出时视为已交付、`basic.nack`/`basic.reject` 的 `requeue`：[RabbitMQ 4.4, Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)，核对于 2026-11-12；这些是 RabbitMQ 的行为，其他 broker 须按自身契约核实。
> - Read Committed 下行锁与并发条件更新的重检：[PostgreSQL 18, Transaction Isolation §13.2.1](https://www.postgresql.org/docs/18/transaction-iso.html)、[Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html)，核对于 2026-11-12。本章的重排与取消 SQL 在 PostgreSQL 14.25 本地实跑。
> - S3 条件写：[Amazon S3, Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)，核对于 2026-11-12。
> - 重试决策顺序、取消竞争规则、孤儿清理条件是本主线的应用合同；3 次上限、240 个等待槽为本例取值，不是框架默认。
