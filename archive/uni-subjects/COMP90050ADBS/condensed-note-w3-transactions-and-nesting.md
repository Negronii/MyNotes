# 扣款成功但入账失败时，事务边界与局部回滚怎样保护业务？

Alice 向 Bob 转 100 元：系统先从 Alice 账户扣款，再向 Bob 账户入账。若两条更新各自提交，扣款提交后进程就崩溃，数据库可能留下只扣款未入账的结果；若航班预订的第三段路线失败，整笔重做又很浪费。本章沿着这两个场景说明事务怎样界定原子工作、保存点怎样撤销局部尝试，以及课程的嵌套事务模型与数据库保存点怎样处理局部失败和根提交。

## 为什么转账必须由一个事务包住？

假设 Alice 与 Bob 转账前分别有 500 元、200 元。成功后应同时成为 400 元、300 元；任一步失败，数据库中的两行都应回到 500 元、200 元。transaction（事务）把这组数据库操作作为一个逻辑工作单元，由根事务的提交或回滚决定其结果。

ACID 四个性质回答不同问题：

- atomicity（原子性）：这组数据库更新要么一起提交，要么一起撤销，不留下只扣款或只入账的半笔转账。
- consistency（一致性）：事务从满足约束的状态出发，并以满足声明约束和业务规则的状态结束。例如数据库可检查余额非负；数据库不会替应用补上未声明的规则，事务逻辑本身也必须正确。
- isolation（隔离性）：并发事务能观察到什么中间状态，由所选隔离规则限制。隔离本身不把两条独立更新自动组合成一个事务；原子边界仍需由事务提供。
- durability（持久性）：数据库确认提交后，更新按它承诺的故障范围保留。应用若没收到提交确认，不能仅凭客户端超时断定事务已回滚。

> [!example] 谁能看见 400/200 这个中间状态？
> 将两次更新放在同一事务中：扣款后，该事务自己的查询可读到 Alice=400、Bob=200；它接着入账，才变成 400/300。以 PostgreSQL 的 Read Committed (读已提交) 为例，另一会话在根提交前发出的同一条查询仍读到 500/200。若根事务中止，两次修改都不保留；若提交成功，之后的新查询读到 400/300。总额 700 不变是业务不变量，未提交的中间状态不等于最终持久状态。

若扣款位于银行服务、入账位于另一套数据库，单个本地事务通常只保护本库。要把多个资源管理器纳入一个原子决定，需要参与方共同支持分布式事务协议；若外部动作不支持这样的协调，就要设计可重试的交付或补偿。`ROLLBACK` 不能让已经发出的航班或通知从未发生。

## 哪些动作能回滚，哪些只能补偿？

protected action（受保护动作）是在结果对外生效前受事务系统控制、能随事务撤销的数据库更新。real action（外部真实动作）一旦执行通常不能物理倒退，例如已经寄出的包裹或已经发送的通知。回滚本地记录不等于撤销外部世界中的变化。

因此要分别记录本地提交状态和外部交付状态。常见流程是先把待办事项与业务变更写入同一数据库事务，再由独立发送者重试交付；如果外部系统可能重复接收，请求应带稳定标识并由接收方去重，或在业务上提供补偿。选择哪种流程取决于外部系统能力，但本地回滚不能冒充远程撤销。

## 嵌入式 SQL 怎样表达事务边界？

embedded SQL（嵌入式 SQL）允许在宿主语言代码中嵌入 SQL。下面是 PostgreSQL Embedded SQL in C（C 中的嵌入式 SQL，ECPG）片段：开始事务、执行两次更新、检查各自影响一行，再请求提交。样例假定连接已建立、当前没有外层事务、源和目标账户不同、金额为正且两账户存在；真实服务还需有余额约束和稳定的业务操作标识。

```c
#include <stdio.h>
EXEC SQL INCLUDE sqlca;

EXEC SQL BEGIN DECLARE SECTION;
long from_account;
long to_account;
long amount;
EXEC SQL END DECLARE SECTION;

int transfer(long from_id, long to_id, long cents) {
    from_account = from_id;
    to_account = to_id;
    amount = cents;

    EXEC SQL WHENEVER SQLERROR GOTO sql_error;
    EXEC SQL BEGIN WORK;
    EXEC SQL UPDATE accounts
        SET balance = balance - :amount
        WHERE account_id = :from_account;
    if (sqlca.sqlerrd[2] != 1) goto rollback;

    EXEC SQL UPDATE accounts
        SET balance = balance + :amount
        WHERE account_id = :to_account;
    if (sqlca.sqlerrd[2] != 1) goto rollback;

    EXEC SQL COMMIT WORK;
    return 0;

sql_error:
    fprintf(stderr, "database error: %s\n", sqlca.sqlerrm.sqlerrmc);
    /* 下面的 ROLLBACK 即使失败也不要再次跳回本标签。 */
    EXEC SQL WHENEVER SQLERROR CONTINUE;
rollback:
    EXEC SQL ROLLBACK WORK;
    return -1;
}
```

宿主变量声明在 `BEGIN DECLARE SECTION` 与 `END DECLARE SECTION` 之间，SQL 中的冒号（如 `:amount`）表示 C 主机变量。ECPG 预处理器先把 `.pgc` 变成 C，再由 C 编译器编译。`WHENEVER SQLERROR` 是按源码位置生效的预处理指令，会为后续嵌入 SQL 生成错误处理；它不是 C 异常机制。PostgreSQL ECPG 还区分 `NOT FOUND`：成功执行但影响零行不是 SQL 执行错误，默认不会走 `SQLERROR` 分支。这里显式读 `sqlca.sqlerrd[2]`，所以任一账户缺失时也会走回滚路径。

这里返回 `0` 表示收到了成功提交的确认；`-1` 既可能表示已撤销，也可能表示结果无法确认。若 `COMMIT` 已在数据库成功，而确认在网络中丢失，客户端看到的错误并不能证明提交失败；后续 `ROLLBACK` 也可能因连接断开而无法确认。调用方应使用稳定的业务操作 ID 查询既有结果，避免把未知提交当成可盲目重试的新转账。如何识别未知结果并安排安全重试，见[未知结果与安全重试](../../../engineering-foundations/reliability/api-reliability-and-async-delivery.md)。这个代码展示边界和诊断，不是完整的生产转账服务。

> [!example] 课程购货函数怎样加入外层事务
> 课程里的 `BuySomething()` 先向购货历史表插入记录，再扣减账户余额，并以 `SELECT ... INTO` 取回扣款后的余额。外层 `process_purchase()` 负责 `BEGIN WORK`，调用函数后检查业务结果，再决定 `ROLLBACK WORK` 或 `COMMIT WORK`。函数不会自动创建独立事务；它的写入归调用者拥有的根事务。`SELECT ... INTO` 预期一行；多行结果应使用游标或其他多行接口。

flat transaction（平面事务）只有一个提交层级：根提交时一同持久化，根回滚时一同撤销。它适合边界明确的一组工作；当大流程有可选步骤时，保存点可以撤销局部尝试，而不必丢弃标记前的工作。

## 航线的中间方案失败后怎样保留已完成部分？

用户要从墨尔本飞往都柏林：先安排墨尔本—新加坡，再安排新加坡—伦敦和伦敦—都柏林。若伦敦方案校验不可用，系统想保留第一段，撤销伦敦两段后改走巴黎。savepoint（保存点）是在当前事务中标记一个位置；回滚到该标记会撤销其后的数据库操作，但事务仍可继续。

![课程保存点图：回滚到 work 2 后改走新动作，再以 work 5 回滚后续动作](./save-points.png)

这张课程图使用通用动作编号，并未标出城市。`ROLLBACK WORK(2)` 撤销 Action 3–7，同时删除之后建立的 `SAVE WORK 3`，保留 Action 1–2。右侧接着执行 Action 8–11，并建立 work 4、work 5；第二次回滚到 work 5 时只撤销 Action 12–13，保留 Action 8–11。蓝色箭头表示回滚后继续尝试新动作。保存点记法表达局部恢复，不表示这些动作已经独立提交；下面的 SQL 再把它落实到具体航线。

假设同一数据库中的明细表为 `booking_segments(booking_id, segment_no, origin, destination)`。下面只更新本地预订记录，不向外部航司出票。这里把伦敦路线不可用作为应用层校验结果；若保存点之后的 SQL 语句本身报错，则 PostgreSQL 当前事务会进入错误状态，需先回滚到该保存点才能继续；没有可用标记或决定放弃整个流程时，应回滚整笔事务。

```sql
BEGIN;
INSERT INTO booking_segments VALUES (42, 1, 'Melbourne', 'Singapore');
SAVEPOINT after_singapore;
INSERT INTO booking_segments VALUES (42, 2, 'Singapore', 'London');
INSERT INTO booking_segments VALUES (42, 3, 'London', 'Dublin');
-- 应用校验判定伦敦路线不可用：
ROLLBACK TO SAVEPOINT after_singapore;
INSERT INTO booking_segments VALUES (42, 2, 'Singapore', 'Paris');
INSERT INTO booking_segments VALUES (42, 3, 'Paris', 'Dublin');
RELEASE SAVEPOINT after_singapore;
COMMIT;
```

`ROLLBACK TO SAVEPOINT` 丢弃标记之后的更改并保留标记；在 PostgreSQL 中回滚后该标记仍可再次使用。`RELEASE SAVEPOINT` 删除标记，把保留的更改并入外层事务，既不提交也不对其他事务公开。本例第一次局部回滚后只剩墨尔本—新加坡；改走巴黎并释放保存点后，本事务中有三段航线，但外部还看不到新记录。若此时改为根 `ROLLBACK`，三段一起撤销；执行最后的 `COMMIT` 成功后，三段才一起提交，当前事务也就结束了。

## 课程中的嵌套事务与保存点有什么不同？

课程的 closed nesting（封闭嵌套）把根事务和调用的子事务表示成事务树：根可启动子事务，子事务还能启动自己的孩子。

![课程封闭嵌套事务树的父子调用示意图](./nestedTransaction.png)

在这个课程模型里，子事务可读取父事务产生的临时状态；子事务结束后可把暂定结果交给父事务，但子提交不独立持久，也不对根事务之外的观察者公开。子事务或祖先中止时，属于它的未最终提交后代结果也被撤销；只有根提交才最终生效。子事务中止后，父事务可以选择替代动作继续，也可以自行中止，使更大的子树一同撤销。课程假设父事务不会与自己的子事务并行运行，兄弟子事务可以并行；如果兄弟操作共享数据，其协调规则仍需由并发控制定义。

PostgreSQL 的 `SAVEPOINT` 实际会启动 subtransaction (子事务)，多个层级同样可以形成树。局部回滚后父级可继续、子结果只有随根提交才持久，这些都是它与 closed nesting 的共同点。区别在于本课模型还讨论兄弟子事务的并行和独立调度；同一 PostgreSQL 连接上依次执行 `SAVEPOINT`、`ROLLBACK TO`、`RELEASE`，并不会因此并行运行两个兄弟任务。

## 事务处理监视器怎样协调多层业务系统？

transaction processing monitor（事务处理监视器，TP monitor）是课程对协调客户端、应用服务器和资源管理器的中间件角色的分类。课程举出的职责包括：把请求分配给服务器并管理事务，协调参与者对事务结果的处理，跟踪远程通信与恢复状态，以及管理终端、会话和表现层交互。这是课程中的职责集合，不表示每个当代平台都实现同一套功能。

IBM TXSeries/CICS 是一个具体参照：官方文档描述 CICS region 接收请求、校验通信与授权、将请求分派为 task，由 application server 执行程序，并由 region 管理任务使用的数据和资源。这个例子说明 TP monitor 类产品会提供怎样的协调运行环境，不把产品特性当作通用定义。

two-phase commit（两阶段提交，2PC）可协调多个支持该协议的资源管理器对一笔事务作出提交或中止决定。它不替代业务不变量检查，也不会自动纳入任意 HTTP 服务或不可逆真实动作；外部交付还需独立设计重试、去重或补偿。

> [!info]- 来源与核对范围
> - 事务、ACID、并发和恢复的课程背景：Silberschatz、Korth、Sudarshan，《Database System Concepts》第 7 版第 17、18、19 章，2019 年课程幻灯片：[Transactions](https://www.db-book.com/slides-dir/PDF-dir/ch17.pdf)、[Concurrency Control](https://www.db-book.com/slides-dir/PDF-dir/ch18.pdf)、[Recovery System](https://www.db-book.com/slides-dir/PDF-dir/ch19.pdf)。
> - 封闭嵌套的子提交、根提交与父子调度：[Moss, Log-Based Recovery for Nested Transactions](https://people.cs.umass.edu/~moss/papers/vldb-1987.pdf)，1987，§3；[Moss, Open Nested Transactions: Semantics and Support](https://people.cs.umass.edu/~moss/papers/wmpi-2006.pdf)，2006，§II 的 Closed Nesting。
> - 读已提交下每条查询的可见状态：[PostgreSQL 18 §13.2.1 Read Committed Isolation Level](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-READ-COMMITTED)。
> - PostgreSQL 保存点启动子事务及其提交树：[PostgreSQL 18 §67.3 Subtransactions](https://www.postgresql.org/docs/18/subxacts.html)。
> - 2PC 的参与者和决定协议：《Database System Concepts》第 7 版第 23 章，[Parallel and Distributed Transaction Processing](https://www.db-book.com/slides-dir/PDF-dir/ch23.pdf)。
> - ECPG 主机变量、预处理指令、`WHENEVER`、`sqlca.sqlerrd[2]` 和 `NOT FOUND`：PostgreSQL 18 文档第 34 章，[ECPG 概念](https://www.postgresql.org/docs/18/ecpg-concept.html)、[错误处理](https://www.postgresql.org/docs/18/ecpg-errors.html)、[WHENEVER](https://www.postgresql.org/docs/18/ecpg-sql-whenever.html)，按 PostgreSQL 18.7（2026-11-12 发布）文档核对，访问于 2026-11-13。
> - 保存点只在当前事务内起作用，回滚后可继续，释放后保留更改但仍未提交：[SAVEPOINT](https://www.postgresql.org/docs/18/sql-savepoint.html)、[ROLLBACK TO](https://www.postgresql.org/docs/18/sql-rollback-to.html)、[RELEASE SAVEPOINT](https://www.postgresql.org/docs/18/sql-release-savepoint.html)，PostgreSQL 18，访问于 2026-11-13。
> - TP monitor 产品参照：[CICS transaction processing environment](https://www.ibm.com/docs/en/txseries/11.1.0?topic=processing-cics-transaction-environment) 与 [Life cycle of a CICS transaction](https://www.ibm.com/docs/en/txseries/11.1.0?topic=processing-life-cycle-cics-transaction)，IBM TXSeries 11.1 文档，访问于 2026-11-13。
> - 课程原图 `save-points.png` 与 `nestedTransaction.png` 保留原路径和字节；其在 700px 预览可读，故仍用于正文。
> - 运行核对使用 PostgreSQL/ECPG 14.24：成功转账、缺失账户、约束失败、保存点恢复、提交确认丢失与进程级崩溃恢复。PostgreSQL 18 文档用于语义核对；运行版本与文档版本分开记录。
