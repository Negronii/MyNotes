# 事务能保证什么，并发事务各能看见什么？

前两章已经用一笔事务把库存扣减和预留记录绑在一起，并依赖 Read Committed 的一条行为让并发请求排队。本章把事务本身讲清：它承诺哪几件事、失败时该回滚、重试还是回查，各隔离级别让并发事务看见什么，以及为什么即使快照稳定，跨多行的规则仍会被破坏。库存的并发时序不再重讲，只引用[第一章](conditional-writes-and-idempotent-records.md)的结论：A 先扣减并提交，同一请求的重放 B 等锁、重检、零行，回滚后在新事务读到 A 的记录。SQL 以 PostgreSQL 18 为准。

## ACID 各描述什么边界？

transaction (事务) 把多条语句放进同一次提交或回滚。ACID 是描述这个边界的四个词，每一项都受数据库实现、配置和底层存储约束：

- **atomicity (原子性)**：同一事务里的写入一起提交，或一起被回滚撤销。库存扣减和预留记录要么都在，要么都不在。
- **consistency (一致性)**：合法状态由约束和应用规则定义。事务不会自己发明业务不变量；`available >= 0` 是 `CHECK` 写出来的，不是事务带来的。
- **isolation (隔离性)**：并发事务按隔离级别观察或等待彼此的写入。级别不同，看到的东西不同，下文逐级说明。
- **durability (持久性)**：成功提交能扛住配置与存储所承诺范围内的故障。异步提交或不兑现刷盘的存储会缩小这个范围，见[下一章](write-ahead-logging-and-recovery.md)。

## 一笔事务失败后，该回滚、重试还是回查？

事务失败不是一种情况。三类失败的处置不同，混用会出错，这是本领域的权威规则：

| 失败类型 | 典型信号 | 处置 |
|---|---|---|
| 约束或其他数据库错误 | 唯一冲突、外键违规、CHECK 失败 | 显式 `ROLLBACK`，不能继续 `COMMIT`；按错误类别报告或进入业务裁决 |
| 序列化失败 | SQLSTATE `40001`（Repeatable Read 或 Serializable 下） | 从事务**开头**重试整笔事务，包括最初的读取 |
| 提交结果未知 | `COMMIT` 发出后连接断开或响应丢失 | 不当作失败；保留**原幂等键和原指纹**回查，或沿原来的条件更新与唯一约束路径重试 |

第一类在库存例里已有完整流程：零行或唯一冲突后整笔回滚，新事务按作用域键回查，见[零行或唯一冲突之后怎样下结论？](conditional-writes-and-idempotent-records.md#零行或唯一冲突之后怎样下结论？)。PostgreSQL 报错后事务处于失败状态，再发 `COMMIT` 也只会得到回滚。

第二类必须从头重试，因为整笔事务的决策都建立在旧快照上。只重放失败的那条语句，会沿用已经失效的读取结果。

第三类最容易处理错。`COMMIT` 可能已经在数据库里生效，只是确认没送回来。回查到同键同指纹的记录，就确认它已提交；查不到只说明这次查询没看到提交记录，原事务可能仍在提交中。此时**不能换一个新键**再做一次：新键会让唯一约束把它当成另一项操作，原事务若已提交，就成了两次预留。请求层面怎样在这种状态下停住并稍后重放，见[写请求超时后，怎样查清结果并安全重试？](../services/deadlines-retries-and-unknown-outcomes.md)。

## 各隔离级别挡住哪些并发现象？

隔离级别按“禁止哪些现象”定义：

- dirty read (脏读)：读到另一个事务尚未提交的写入。
- non-repeatable read (不可重复读)：同一事务重读一行，看到别的事务在此期间提交的新值。
- phantom read (幻读)：同一条件的查询再执行一次，满足条件的行集合因别的提交而变了。
- serialization anomaly (序列化异常)：一组都成功提交的事务，其结果无法用任何一种逐个串行执行的顺序解释。

SQL 标准规定每个级别**至少**要防住什么，实现可以更强。PostgreSQL 18 的对照如下：

| 级别 | 脏读 | 不可重复读 | 幻读 | 序列化异常 |
|---|---|---|---|---|
| Read Uncommitted | 不发生（行为等同 Read Committed） | 可能 | 可能 | 可能 |
| Read Committed（默认） | 不发生 | 可能 | 可能 | 可能 |
| Repeatable Read | 不发生 | 不发生 | 不发生（标准允许，PostgreSQL 不发生） | 可能，例如写偏差 |
| Serializable | 不发生 | 不发生 | 不发生 | 不发生 |

## 快照从什么时候开始？

同名级别的行为取决于快照的粒度。PostgreSQL 的两档：

- **Read Committed：每条语句一个新快照。** 语句只看到它开始前已提交的数据。并发更新同一行时，后来者等前者结束；前者提交后，后来者在新行版本上重检 `WHERE`，前者回滚则对原行继续。库存的条件 `UPDATE` 正是靠这一点：B 重检时看到 0，返回零行。
- **Repeatable Read：整笔事务一个快照。** 快照始于事务中第一条非事务控制语句（`BEGIN` 不算）。之后等待别的事务也不会刷新它。若事务要修改的行在它的快照之后已被别的事务提交修改，语句以 `40001` 失败。

同样的库存时序换成 Repeatable Read：B 的 `UPDATE` 等到 A 提交后，不是重检条件，而是直接失败。按上一节的规则，B 从头重试整笔事务；新快照里库存是 0，`UPDATE` 返回零行，后面走回查，结局与 Read Committed 相同，只是多了一次重试。

隔离级别的名字不说明实现。MySQL InnoDB 也有 Repeatable Read，但它的普通读用首次一致性读的快照，`UPDATE` 却读最新版本，同一时序里 B 得到的是“影响 0 行”而不是 `40001`，见 [InnoDB 支线](mysql-innodb-locks-and-logs.md)。

> [!info] MVCC 不等于“读写都不用等”
> multi-version concurrency control (多版本并发控制，MVCC) 让快照读按可见性规则选择行版本。PostgreSQL 更新一行时写入新的 tuple 版本，旧快照仍能读到对它可见的旧版本，因此读不必等写。但写写冲突仍要等：B 更新 A 正在改的库存行时照样排队，Repeatable Read 下还会失败；`FOR UPDATE` 等显式锁和其他资源等待也都还在。旧版本也要清理：PostgreSQL 的 VACUUM 回收不再对任何活动快照可见的旧 tuple，长期持有旧快照会拖延清理。

## 为什么稳定快照仍会破坏跨行规则？

库存规则只涉及一行，条件 `UPDATE` 就够了。规则跨越多行时，即使每个事务看到的都是稳定快照，也会出错，这叫 write skew (写偏差)。下面换一个独立的小例子，因为库存案例只有一行，演示不出它。

排班表里医生甲、乙各一行，规则是同一班次**至少一人值班**。两笔事务各关闭一人，交错如下：

~~~mermaid
sequenceDiagram
    participant T1
    participant DB as 排班表（甲、乙各一行）
    participant T2
    Note over T1,T2: 两笔都是 Repeatable Read，快照里甲、乙都在岗
    T1->>DB: 查在岗人数
    DB-->>T1: 2 人
    T2->>DB: 查在岗人数
    DB-->>T2: 2 人（同样的快照内容）
    T1->>DB: 关闭甲的值班（只改甲行）
    T2->>DB: 关闭乙的值班（只改乙行）
    T1->>DB: COMMIT
    DB-->>T1: 成功
    T2->>DB: COMMIT
    DB-->>T2: 成功：两笔改的是不同行，没有写写冲突
    Note over DB: 结果：没人值班
~~~

`CHECK` 帮不上忙，因为它只看当前这一行。修法取决于规则的形状，这是本领域写偏差修法的权威位置：

**修法一：把规则物化成一行，再用条件写守住。** 给班次加一行值班人数，关闭某人值班时先条件扣减，计数行和医生行在同一事务里更新：

~~~sql
UPDATE shift_coverage
SET on_call = on_call - 1
WHERE shift_id = $1 AND on_call > 1;
-- $1 = 班次 ID。恰好一行才继续更新医生行；零行说明只剩一人，拒绝关闭。
~~~

跨行规则由此变成单行上的条件，两个并发事务在这一行上排队：

~~~mermaid
sequenceDiagram
    participant T1
    participant DB as shift_coverage 计数行
    participant T2
    Note over T1,T2: 修法一，Read Committed：先条件扣减计数行
    T1->>DB: UPDATE ... SET on_call = on_call - 1 WHERE on_call > 1
    DB-->>T1: 1 行（2 → 1），T1 持有行锁
    T2->>DB: 同一条 UPDATE
    Note over DB: T2 在计数行上等待
    T1->>DB: 关闭甲（更新甲行），COMMIT
    DB-->>T2: 在新版本 on_call = 1 上重检条件：0 行
    Note over T2: 拒绝关闭乙
~~~

**修法二：Read Committed 下所有写方先锁同一控制行，再用下一条语句检查。** 关键在 T2 拿到锁之后的**下一条** `SELECT`：

~~~mermaid
sequenceDiagram
    participant T1
    participant DB as 班次控制行与排班表
    participant T2
    Note over T1,T2: 修法二，Read Committed：所有写方先锁同一控制行
    T1->>DB: SELECT 班次行 FOR UPDATE
    DB-->>T1: 取得锁
    T2->>DB: SELECT 班次行 FOR UPDATE
    Note over DB: T2 在锁上等待
    T1->>DB: 查在岗人数（2），关闭甲，COMMIT
    DB-->>T2: 取得锁
    T2->>DB: 下一条 SELECT 取新快照，查在岗人数
    DB-->>T2: 只剩乙 1 人
    Note over T2: 拒绝关闭乙
~~~

这个方案依赖“每条语句一个新快照”，Repeatable Read 的快照不随等待刷新，不能照搬。所有改这条规则的写入路径都必须先锁同一行，漏一条就失效。

**修法三：所有维护这条规则的事务都用 Serializable。** PostgreSQL 会检测到这组事务无法串行解释，让其中一笔以 `40001` 失败，失败方从头重试：

~~~mermaid
sequenceDiagram
    participant T1
    participant DB as 排班表
    participant T2
    Note over T1,T2: 修法三：所有维护这条规则的事务都用 Serializable
    T1->>DB: 查在岗人数（2），关闭甲
    T2->>DB: 查在岗人数（2），关闭乙
    T1->>DB: COMMIT
    DB-->>T1: 成功
    T2->>DB: 继续执行或 COMMIT
    DB-->>T2: 40001：这组事务无法串行解释
    Note over T2: 回滚，从头重试整笔事务<br/>（哪一笔、在哪条语句失败由数据库决定，这里画成 T2）
    T2->>DB: 新事务：查在岗人数
    DB-->>T2: 只剩乙 1 人
    Note over T2: 放弃关闭
~~~

保护只在参与的事务都运行 Serializable 时成立；只重试最后一条 `UPDATE` 会沿用旧决策，仍然错。

| 修法 | 适用 | 代价 |
|---|---|---|
| 物化为单行计数 + 条件写 | 规则能归结为一个数 | 多维护一行，所有写方都要同时更新它 |
| 先锁控制行（Read Committed） | 规则复杂但有自然的“控制行” | 写入在控制行上串行化；每条写路径都要遵守 |
| 全部 Serializable + 整笔重试 | 规则难以物化，写方都可控 | 要处理 `40001` 重试，冲突多时吞吐下降 |

## 事务管不到哪些副作用？

上面的手段都只作用于本数据库。事务里不要做两件事：

- **执行无法撤销的远端操作**，例如调用支付。回滚撤不回远端的扣款，提交结果未知时也不知道远端做了没有。
- **直接发布消息。** 先发后提交，消息可能指向一笔后来回滚的记录；先提交后发，进程可能在两步之间崩溃，消息永远没发。

做法是在同一事务里写一条 outbox 记录，与业务修改一起原子提交，提交后由后台进程投递；投递仍可能重复，消费者要去重。这个机制的完整推导在[耗时任务怎样被持久受理，并保证一定会被唤醒？](../services/durable-job-acceptance-and-outbox.md)，远端操作本身怎样去重和对账，在[写请求超时后，怎样查清结果并安全重试？](../services/deadlines-retries-and-unknown-outcomes.md)。

事务里也不要等长时间的网络调用。事务持有的行锁和连接会在这段时间里一直被占着，其他请求排队，连接池也会被耗尽，见[ORM 会话怎样借用连接，连接池为什么会耗尽？](orm-sessions-and-connection-pools.md)。

## 提交确认之后还剩什么问题？

本章产出：事务失败的三类处置（尤其是提交结果未知时保留原键回查、不换新键）；各隔离级别的快照粒度和它们挡住的现象；写偏差的三种修法；以及“事务只管本库”这条边界。隔离讨论的是并发事务之间的可见性。另一个问题是：数据库已经确认了 `COMMIT`，随即崩溃，这次提交凭什么还在？这是[数据库确认提交后崩溃，靠什么恢复？](write-ahead-logging-and-recovery.md)的问题。

> [!info]- 来源
> - **隔离现象的定义、标准与 PostgreSQL 18 级别对照（Read Uncommitted 等同 Read Committed、Repeatable Read 不发生幻读）、Read Committed 每语句快照与等锁后重检、Repeatable Read 快照起点与 `40001`、Serializable 检测与整笔重试**（“各隔离级别……”“快照从什么时候开始？”“为什么稳定快照……”）：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2、Table 13.1，核对于 2026-11-12。
> - **`COMMIT` 使改动对其他会话可见并按持久策略保留**（“ACID 各描述什么边界？”）：[PostgreSQL 18, COMMIT](https://www.postgresql.org/docs/18/sql-commit.html)；**报错后事务失败、须回滚**：[Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html)，§3.4，核对于 2026-11-12。
> - **MVCC 快照可见性与 VACUUM 清理旧版本**（MVCC 说明）：[PostgreSQL 18, Introduction to MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html)，§13.1；[Routine Vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html)，§24.1.2，核对于 2026-11-12。
> - **InnoDB 同名级别的快照读与锁定读**（“快照从什么时候开始？”的对照）：[MySQL 8.4, Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)，§17.7.2.1，核对于 2026-11-12。
