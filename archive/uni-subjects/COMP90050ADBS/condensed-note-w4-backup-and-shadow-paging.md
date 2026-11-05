# How do remote backup and shadow paging handle failure? / 远程备份与影子分页如何处理故障？

A backup must distinguish a failed primary from a network partition before promotion. Commit-safety modes trade acknowledgment delay against which commits may be missing at failover. Shadow paging copies changed pages and publishes a durable new root, trading log work for copying and fragmentation costs. / 远程备份在提升前必须区分主节点故障与网络分区。提交安全模式权衡确认延迟与故障切换时可能缺失的提交。影子分页复制变更页并持久发布新根，以复制和碎片化成本换取较少日志工作。

## Remote Backup System
Remote backup systems provide high availability by allowing transaction processing to continue even if the primary site is destroyed

- Detection of failure: **Backup site must detect when primary site has failed**
  - Heartbeats detect loss of contact but cannot by themselves distinguish a failed primary from a network partition. A safe promotion also needs fencing or an agreed quorum/ownership rule to prevent two primaries.
- Transfer of control
  - To take over control, **backup site first perform recovery using its copy of the database and all the log records it has received from primary**. Thus, completed transactions are redone and incomplete transactions are rolled back
  - After safe promotion, the backup becomes the new primary.

### Remote Backup System
- Time to recover
  - To reduce delay in takeover, backup site periodically processes the redo log records (don't do undo)
  - In effect, it performs a **checkpoint**, and can then delete earlier parts of the log
- Hot-Spare configuration permits very fast takeover:
  - Backup continually processes redo log record as they arrive, applying the updates locally
  - When failure of the primary is detected, the backup rolls back incomplete transactions, and is ready to process new transactions

### Remote Backup System
Ensure durability of updates by delaying transaction commit until update is logged at backup. But we can avoid this delay by permitting lower degrees of durability. i.e. delay commits until the log is committed in backup

- One-safe: acknowledge commit when its commit record is durable at the primary, without waiting for the backup. A primary-site loss before log transfer can lose an acknowledged commit.\
  (A primary-site failure can occur before the latest log records arrive at the backup.)
- Two-very-safe: acknowledge commit after the commit record is durable at both primary and backup. This reduces the risk of losing an acknowledged commit but reduces availability if either site is unavailable.
  (Acknowledgments wait for both sites, so a failure of either site can reduce commit availability.)
- Two-safe: use the two-site acknowledgment rule while both sites are active; if only the primary remains, acknowledge after the primary commit record is durable. This improves availability but has a failover scenario in which the backup may not contain a primary-only acknowledged commit.\
  (This improves availability over two-very-safe but can lose a primary-only acknowledged commit if failover uses a stale backup.)

## Shadow Paging
Shadow Paging

- Idea: maintain two page tables during the lifetime of a transaction, i.e., the current page table, and the shadow page table
- To start with, both the page tables are identical. Only current page table is used for data item accesses during execution of the transaction
- Whenever any page is about to be written
  - A copy of this page is made onto an unused page
  - The current page table is then made to point to the copy
  - The update is performed on the copy
- To commit a transaction
  1. Flush all modified pages in main memory to disk
  2. Output current page table to disk
  3. Make the current page table the new shadow page table
- Once the new root-page-table pointer is atomically and durably published, the transaction is committed; the modified pages and page table must already be durable.

Advantages of shadow-paging over **log-based schemes**

- No overhead of writing log records
- Recovery is trivial - new transactions can start right away, using the shadow page table.

Disadvantages

- Copying the entire page table is very expensive when the page table is large
- Commit overhead is high - Need to flush every updated page, and page table
- Data gets fragmented (related pages get separated on disk)
- Hard to extend algorithm to allow transactions to run concurrently

### In Practice
Strategy plan based on:

- Goals and requirement of your organization/task
- The nature of your data and usage pattern
- Constraint on resources

Design backup strategy:

- Full disk backup vs partial - Are changes likely to occur in only a small part of the database or in a large part of the database?
- How frequently data changes - If frequent: use differential backup that captures only the changes since the last full database backup
- Space requirement of the backups – depends on the resource
- Multiple past instances of backup – useful if point-in-time recovery is needed
