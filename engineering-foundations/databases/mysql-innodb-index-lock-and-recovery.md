# InnoDB 怎样用索引记录、旧版本与日志处理库存事务？

**案例：** 合成库存中，SKU-7 全局只剩一件。两个会话都尝试为 acct-17 预留；会话 A 先读到 available=1，会话 B 更新并提交后，A 的普通 SELECT 仍可能读到旧值。要正确理解结果，需要沿着 InnoDB 索引定位行、多版本并发控制（MVCC）可见版本、当前写锁和崩溃日志各走一遍。

本文使用 MySQL 8.4、InnoDB、autocommit=1；并发例显式设为 REPEATABLE READ。持久性演算假设 binary log（二进制日志）已启用、innodb_flush_log_at_trx_commit=1、sync_binlog=1，且操作系统与存储设备正确兑现 flush（刷入持久存储）。它们是推演条件，不是本机 MySQL 实测。本仓库的通用事务页使用 PostgreSQL 例子；该页的 SQL 并发与日志描述不能直接当作 InnoDB 的锁范围。

~~~mermaid
flowchart TD
    SQL[SQL 谓词] --> Index[索引访问路径]
    Index -->|普通 SELECT| Snapshot[快照版本：read view 与 undo]
    Index -->|UPDATE| Update[当前读]
    Index -->|SELECT FOR UPDATE| LockingRead[当前读]
    Update --> Lock[按访问路径取得索引锁]
    LockingRead --> Lock
    Lock -->|UPDATE 修改记录| Page[写页修改并记录 redo]
    Page --> Commit[提交：prepare、binlog 决策、InnoDB 完成]
    Page -. 提交前意外退出 .-> Crash[崩溃恢复：redo 前滚，再保留或撤销]
    Commit -. 提交期间或之后意外退出 .-> Crash
~~~

## 查询先走哪棵 InnoDB 索引？

先创建最小的全局 SKU 库存与预留表。SKU-7 的 available=1 是全局库存，预留记录才带 acct-17；所以 acct-17 是这次预留的账户，不是 SKU 库存归属。其它几行只用于展示一次范围锁。MySQL 8.4 中 InnoDB 表的主键是 clustered index（聚簇索引），叶子节点保存完整行。secondary index（二级索引）的叶子项保存二级键列和主键值；若查询需要的列不都在二级索引中，存储引擎再用主键回到聚簇索引取行。

~~~sql
CREATE TABLE inventory (
    sku_id INT NOT NULL PRIMARY KEY,
    warehouse_id VARCHAR(16) NOT NULL,
    available INT NOT NULL CHECK (available >= 0),
    note VARCHAR(64) NOT NULL
) ENGINE = InnoDB;

CREATE INDEX inventory_by_warehouse_stock
    ON inventory (warehouse_id, available);

CREATE TABLE reservations (
    request_key VARCHAR(64) NOT NULL PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL,
    sku_id INT NOT NULL,
    status VARCHAR(16) NOT NULL,
    FOREIGN KEY (sku_id) REFERENCES inventory(sku_id)
) ENGINE = InnoDB;

INSERT INTO inventory VALUES
    (7,  'W-1', 1, 'last unit'),
    (10, 'W-1', 5, 'synthetic range row'),
    (11, 'W-1', 4, 'synthetic range row'),
    (13, 'W-2', 2, 'synthetic range row'),
    (20, 'W-2', 1, 'synthetic range row');
~~~

~~~mermaid
flowchart LR
    Q[SQL 谓词] --> Index[选择索引访问路径]
    Index -->|主键| Clustered[聚簇索引记录即完整行]
    Index -->|二级键| Secondary[二级项含键列和主键]
    Secondary -->|还要其他列| Clustered
~~~

WHERE sku_id = 7 用主键唯一定位 SKU-7 的完整行。若查 WHERE warehouse_id='W-1' AND available >= 1，可能先走 inventory_by_warehouse_stock 的有序范围，再用每个二级项中的 sku_id 回到聚簇索引取 note。若投影的列都包含在二级索引和主键中，计划可能覆盖查询而省去回表；最终索引是否被使用仍由优化器和实际统计信息决定。

## 普通读为什么能看见已过时库存？

在 REPEATABLE READ（InnoDB 默认级别）下，同一事务里的普通非锁定 SELECT 使用由第一次一致性读建立的 read view。它为查询判断哪些已提交版本可见，不会锁住被读记录。若某行后来被其他事务更新，undo 保存了重建旧版所需的信息，普通读可以沿版本链还原到快照值。它还会看见本事务自己已经写入的变更。

~~~mermaid
flowchart LR
    Read[普通 SELECT] --> View{最新行版本对 read view 可见?}
    View -->|是| CurrentVersion[直接读取该版本]
    View -->|否| Undo[沿 undo（回滚日志）重建可见旧版]
    Undo --> OldVersion[读取重建出的快照版本]
~~~

下面的两会话顺序明确指定版本；SQL 推演以 SKU-7 初值 1 开始：

~~~sql
-- 会话 A
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT available FROM inventory WHERE sku_id = 7;
-- 第一次一致性读建立快照，结果 1。

-- 会话 B
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
UPDATE inventory
SET available = available - 1
WHERE sku_id = 7 AND available > 0;
-- 更新 1 行，自己的当前值变为 0。
INSERT INTO reservations VALUES
    ('reserve-42', 'acct-17', 7, 'reserved');
COMMIT;
~~~

会话 B 提交后，会话 A 再执行：

~~~sql
-- 会话 A，仍在原事务和原 read view 内
SELECT available FROM inventory WHERE sku_id = 7;
-- 普通一致性读仍是 1；undo 提供快照所需旧版。

SELECT available FROM inventory
WHERE sku_id = 7
FOR UPDATE;
-- 锁定读是 current read，看到最新已提交值 0，并锁定该记录。

UPDATE inventory
SET available = available - 1
WHERE sku_id = 7 AND available > 0;
-- 条件不再成立，影响 0 行；不会把库存扣成负数。
-- 影响 0 行就不插入预留记录；只有扣减 1 行的事务才创建 reservation。
COMMIT;
~~~

普通 SELECT 得到 1 并不说明数据库允许 A 继续按 1 扣减。UPDATE 和 FOR UPDATE 是 current read（当前读）/写操作，围绕可写的当前记录协调锁；A 的更新条件会在实际写入处对当前值求值，结果为零行。若 B 尚未提交而 A 先申请 SKU-7 的排他锁，A 会等待持锁事务提交或回滚，再按可用的当前版本继续处理。普通读的快照与当前写路径是两种视图，混在同一事务时要清楚自己正在用哪一种。

## 唯一命中与范围扫描为什么锁不同？

锁落在索引记录和索引间隙上，不是抽象的 SQL 行集合上。本例用完整主键精确找到已存在的 SKU-7；这次搜索只锁该主键记录，不需要锁它前面的间隙：

~~~sql
START TRANSACTION;
-- 唯一命中：SKU-7 的主键记录锁
SELECT available FROM inventory
WHERE sku_id = 7
FOR UPDATE;
COMMIT;
~~~

完整唯一键命中现有行时，搜索不需要锁索引记录前方的间隙；若排他锁定通过二级索引搜索，InnoDB 还会锁对应的聚簇索引记录。REPEATABLE READ 下，范围搜索和索引扫描可以使用 next-key lock（临键锁）：它把一个索引记录锁与该记录之前的 gap lock（间隙锁）组合起来。这里用两个新会话明确观察事务锁；上一个例子已经结束并提交，不再持有任何锁。A 明确开启事务并锁住主键范围，B 再插入该范围内的新行：

~~~mermaid
flowchart LR
    Write[UPDATE] --> Current[current read（当前读）]
    LockingRead[SELECT FOR UPDATE] --> Current
    Current --> Lock[按访问路径取得索引锁]
~~~

~~~sql
-- 会话 A；明确使用 REPEATABLE READ，autocommit=1
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- 显式事务一直保持到 COMMIT/ROLLBACK
START TRANSACTION;
SELECT sku_id FROM inventory
WHERE sku_id BETWEEN 10 AND 20
FOR UPDATE;
-- 结果包含 10、11、13、20；记录 20 的前间隙 (13, 20) 受保护，A 暂不结束事务。

-- 会话 B；明确使用 REPEATABLE READ，单条 INSERT 在 autocommit=1 下执行
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
INSERT INTO inventory VALUES (15, 'W-1', 2, 'insert in protected gap');
-- 因 A 仍持有范围锁而等待。

-- 会话 A
COMMIT;
-- A 释放锁后，B 的 INSERT 才能继续并提交。
~~~

这段演算以 REPEATABLE READ 和主键范围访问为前提；sku_id 是主键，优化器可用该索引定位范围。sku_id=15 落在受记录 20 的 next-key lock 保护的前间隙 (13, 20)，所以 B 等 A 结束后才能插入。若 A 回滚也会释放锁，B 随后继续。间隙锁的用途是阻止匹配范围出现幻行，不代表该 SQL 已锁住整张表。

唯一索引的部分复合键不等于完整唯一命中；若 UNIQUE 是 (warehouse_id, sku_id)，只给 warehouse_id 条件仍须扫描多个条目，可能锁范围。实际锁范围还取决于执行计划选中的索引、谓词和隔离级别，因此排查等待要先用 EXPLAIN 看访问路径，再检查 InnoDB 锁信息；不能仅凭 SQL 文本里的 WHERE 子句推断只锁住命中的业务行。READ COMMITTED 下搜索扫描通常不使用这些 gap locks，但外键与重复键检查仍可能使用。

## 崩溃时 redo 和 undo 各做什么？

redo 记录数据页修改的恢复信息，让启动恢复能把尚未写回表空间的变更前滚。undo 保存旧行值或回滚所需信息：一致性读用它重建快照版本；事务回滚和崩溃后回滚未提交事务也用它撤销未完成工作。它们服务的方向不同：redo 解决页修改怎样恢复，undo 解决旧版本可见性与未提交变化怎样撤销。

崩溃演算从独立状态开始：SKU-7=1，且没有 reserve-42。要判断事务是否成功，MySQL 8.4 不只看客户端是否收到 COMMIT 响应。InnoDB 先准备事务，服务器把完整事务及 XID 写入并按 `sync_binlog=1` 同步 binlog，再让 InnoDB 完成提交。若此时崩溃，启动恢复从 binlog 找到已持久的完整提交决策，并完成相应的 prepared 事务；若没有该决策，未提交事务会回滚，已 prepare 的事务也会因 binlog 中没有其 XID 而回滚。因此“客户端没收到响应”仍可能恢复为已提交，决策边界是可恢复的 binlog 提交记录。

~~~mermaid
flowchart LR
    Write[UPDATE] --> Redo[redo 记录页修改]
    Commit[COMMIT 请求] --> Prepare[InnoDB prepare]
    Prepare --> Binlog[写入并同步 binlog 提交决策]
    Binlog --> EngineCommit[InnoDB 完成提交]
~~~

假设这一事务把 SKU-7 从 1 扣到 0，并在同一事务插入 reserve-42：

| 崩溃前的恢复决策 | 数据页可能已写入的内容 | 恢复后结果 |
| --- | --- | --- |
| binlog 中有完整、可恢复的持久提交决策，即使客户端没收到响应 | redo 可恢复未全部刷入表空间的页修改 | 保留为已提交；若仍 prepared 则完成，available=0 且有 reserve-42 |
| binlog 中没有完整、可恢复的提交决策 | redo 可能先恢复部分页修改 | 回滚未提交事务（已 prepare 的事务也因无 XID 而回滚），available=1 且无 reserve-42 |

~~~mermaid
flowchart TD
    Crash[意外退出] --> RedoRecover[redo 前滚页修改]
    RedoRecover --> Recover{恢复时的 InnoDB 事务状态}
    Recover -->|已提交| KeepCommitted[保留已提交状态]
    Recover -->|未 prepare 且未提交| Rollback[用 undo 回滚未提交事务]
    Recover -->|仍 prepared| BinlogCheck[按完整 binlog XID 检查提交决策]
    BinlogCheck -->|XID 存在| FinishPrepared[完成 prepared 事务]
    BinlogCheck -->|XID 不存在| Rollback
~~~

所以 redo 不等同于“只记录已经提交的业务行”：恢复可能先应用页变更，再根据 binlog 的提交决策完成 prepared 事务或用 undo 回滚。设置 `innodb_flush_log_at_trx_commit=1` 后，InnoDB 在每个事务提交时写并把 redo 刷入持久存储；`sync_binlog=1` 让 binlog 在提交前同步。两者共同确定这里使用的耐久性边界，但仍依赖操作系统、文件系统、控制器与设备兑现刷盘；它们不替代备份，也不保证整个磁盘或故障域丢失后还能恢复。时间点恢复还需要适用的备份和连续二进制日志。

若要看库存不变量如何在单条条件更新和幂等记录中原子成立，见[两个请求争夺最后一件库存时，怎样保证只预留一次？](database-fundamentals.md)；隔离级别与 WAL 的通用概念也在[事务隔离与 WAL 能保证什么？](database-transactions-isolation-and-recovery.md)中。

> [!info]- 来源
> - MySQL 8.4 REPEATABLE READ 的第一次一致性读快照、普通读不加锁：[InnoDB Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html)，§17.7.2.3，核对于 2026-11-09。
> - undo 用于构造旧版本；聚簇与二级索引的记录结构：[InnoDB Undo Logs](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html)，§17.6.6；[InnoDB Row Formats](https://dev.mysql.com/doc/refman/8.4/en/innodb-row-format.html)，§17.10，核对于 2026-11-09。
> - 完整唯一键命中、gap 与 next-key 的边界以及 REPEATABLE READ 范围扫描：[InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)，§17.7.1；按二级索引排他搜索时也锁对应聚簇记录：[Locks Set by Different SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)，§17.7.3；显式事务中的 `FOR UPDATE` 锁持续到 COMMIT/ROLLBACK：[Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html)，§17.7.2.4；隔离级别与锁定语句：[Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)，§17.7.2.1，核对于 2026-11-09。
> - redo 前滚、未提交事务回滚：[InnoDB Recovery](https://dev.mysql.com/doc/refman/8.4/en/innodb-recovery.html)，§17.18.2；启用 XA 两阶段提交与 `sync_binlog=1` 后以 binlog 中完整 XID 决定恢复时完成 prepared 事务：[The Binary Log](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html)，§7.4.4；每事务 flush 的 innodb_flush_log_at_trx_commit 与复制配置的 sync_binlog：[InnoDB System Variables](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html)，innodb_flush_log_at_trx_commit，核对于 2026-11-09。
