# Crash Recovery and Distributed Databases / 崩溃恢复与分布式数据库

核心概念：持久日志与检查点帮助系统在崩溃后重建事务和脏页状态；ARIES 按 analysis、redo、undo 恢复，WAL 要求相关日志先于数据页持久化。分布式提交的原子决议（2PC）不等同于隔离；CAP 只讨论网络分区下线性一致性与逐请求可用性的模型取舍。

## Crash Recovery / 崩溃恢复
Recover from a failure either when a single-instance database crashes or all instances crash.  
Crash recovery restores a usable state after a crash: preserve the effects of committed transactions, and undo incomplete transactions (or finish recovery of transactions that had already aborted).

### ACID properties
Recovery manager guarantees Atomicity and Durability.

- Atomicity - All changes to data are performed as if they are a single operation. That is, all the changes are performed, or none of them are.
- Consistency - Data is in a ‘consistent’ state when a transaction starts and when it ends – in other words, any data written to the database must be valid according to all defined rules (e.g., no duplicate student ID, no negative fund transfer, etc.)
- Isolation controls interactions among concurrent transactions. Serializable isolation is equivalent to some serial order; weaker isolation levels permit defined anomalies, and product guarantees vary ([PostgreSQL isolation documentation](https://www.postgresql.org/docs/18/transaction-iso.html)).
- Durability means acknowledged commits survive the failures covered by the engine's durability configuration and failure model.

### Desired behaviors when crash happens
![](./desiredCrash.png)
The graph shows T1, T2, and T3 committed before the crash; T4 and T5 were incomplete; T6 had aborted. Recovery preserves the committed updates, undoes T4 and T5, and ensures T6's abort is reflected if its undo was not yet complete.

### Data Access
![](./dataaccess.png)
Two types of data blocks

- **Disk pages/blocks** are logical storage units on persistent storage.
- **Buffer frames** are in-memory slots that hold copies of database pages in the DBMS buffer pool. A device/controller cache is a separate layer.

Two operations between disk and main memory

- **Input(A)** transfers the physical block A to main memory.
- **Output(B)** transfers the buffer block B to the disk and replaces the data there.

### Some Concepts
- Persistent storage holds database pages; the DBMS buffer pool keeps page copies in main-memory frames.
- A frame can be evicted when it is unpinned; a dirty page may be written back as part of eviction, subject to the WAL rule. Pin/unpin prevents replacement while an operation needs the page.
- Latches protect short-lived in-memory structures; transaction locks protect logical data access for transaction isolation. Fix/unfix commonly refers to pinning/unpinning a buffer page.

More Concepts:

- **Force** requires modified pages to reach persistent storage at commit; **no-force** permits commit after the required log is durable while data pages remain buffered. No-force does not by itself make a commit nondurable when WAL is used.
- **Steal** permits flushing a page that contains uncommitted updates; recovery must be able to undo those updates. Together, steal/no-force commonly requires both undo and redo.

## Log-based Crash Recovery / 基于日志的崩溃恢复
### Logging
- A recovery log records enough information to redo or undo updates, along with transaction and page identifiers and ordering metadata. Log records may contain physical before/after values, logical operations, or other engine-specific data; not every engine stores both old and new bytes in every record. [ARIES](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging) is one specific recovery design; [Database System Concepts, 7e, ch. 19](https://www.db-book.com/slides-dir/PDF-dir/ch19.pdf) presents its recovery algorithm; [PostgreSQL WAL](https://www.postgresql.org/docs/18/wal-intro.html) documents a product-specific implementation.
- Logs are appended in log sequence order, commonly to buffered log pages. Record size and format depend on the recovery design.

### Write-Ahead Logging (WAL) / 预写日志
1. Before a dirty data page is written to persistent storage, its update log records must be durable through that page's pageLSN.
2. Before commit is acknowledged, the commit record and the transaction's preceding log records required by the recovery protocol must be durable. WAL record formats vary by engine.

#### Write-Ahead Logging (WAL) – e.g.,
- LSN (log sequence number) – LSNs increase monotonically within the illustrated log sequence.
- pageLSN - The LSN of the most recent log record for an update to that page.
- flushedLSN - max LSN flushed so far (flush to disk)
- In this ARIES-style illustration, WAL requires **pageLSN <= flushedLSN** before the data page can be written.

**Cannot** write the page to disk
![](./WALegCannot.png)
**Can** write the page to disk
![](./WALegCan.png)

### Transaction Table
- The transaction table tracks transactions that have not yet written an end record; it stores transaction ID, status, and lastLSN.
- Contains transactionID, status (running/committed/aborted), and lastLSN.  
  During analysis, remove a transaction when its END record is encountered. A transaction with a durable COMMIT but no END at crash is a winner that may remain in the table; it is not undone.
  e.g.

| transactionID | status     | lastLSN |
| ------------- | ---------- | ------- |
| T1            | running    | 40      |
| T2            | committed  | 80      |

### Dirty Page Table
- One entry per dirty page in the buffer pool. A page becomes dirty after an update changes it.
- In ARIES, **recLSN** is the LSN of the first update that made the page dirty after it was last clean; it is the earliest update that may need redo for that page. Loading a page does not itself make it dirty ([Database System Concepts, 7e, ch. 19](https://www.db-book.com/slides-dir/PDF-dir/ch19.pdf)).  
  e.g.

| Pageid | recLSN |
| ------ | ------ |
| P1     | 10     |
| P2     | 50     |
| P3     | 80     |

![](./dirtyPageTable.png)

### Checkpoint
Periodically, the DBMS creates a checkpoint, in order to **minimize the time taken to recover in the event of a system crash**.  
Write to log:

- Begin checkpoint record: Indicates when checkpoint began.
- End checkpoint record: Contains current Transaction table and dirty page table.

**Fuzzy Checkpoint** – the creation of checkpoint **takes a little time**

- Transactions continue while a fuzzy checkpoint is collected; it is not a quiescent database image. Recovery uses the checkpoint metadata and scans the subsequent log. A fuzzy checkpoint does not itself force dirty pages to disk ([ARIES](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging)).

### Transaction – Abort
- Get lastLSN of transaction from transaction table.
- Follow the transaction's log chain backward through prevLSN. For each update undone, write a Compensation Log Record (CLR) describing the undo and its undoNextLSN; CLRs are redoable and are not themselves undone.
  - Continue logging while undo proceeds.
- At end of UNDO, write an “end” log record.

#### e.g.
T1

1. Update A: 100 -> 200
2. Update A: 200 -> 300
3. Update A: 300 -> 400

---

              Abort 400

We will go backward, from UNDO 3, 400 -> 300, to UNDO 2..., finally get 100

#### Transaction – Abort e.g.,
| LSN | Log                  |
| --- | -------------------- |
| 400 | begin checkpoint     |
| 405 | end checkpoint       |
| 410 | update: T1 writes P5 |
| 420 | update: T2 writes P3 |
| 430 | update: T1 writes P4 |
| 440 | T1 abort             |
| 445 | CLR: Undo T1 LSN 430 |
| 450 | CLR: Undo T1 LSN 410 |
| 455 | T1 End               |
| 460 | update: T3 writes P5 |

### Transaction - Commit
- Write commit record to log.
- Mark the transaction committed in the transaction table, then flush the log through the COMMIT record's LSN before acknowledging commit. Earlier transaction records are flushed with it because the log is ordered.
- Append an END record after commit processing and remove the transaction from the in-memory transaction table. Group commit can amortize flushes; acknowledgment semantics still depend on the engine and its durability configuration.

### Crash recovery
Three phases

- Phase 1 – **Analysis**: reconstruct the transaction table and dirty page table from the checkpoint and subsequent log.
- Phase 2 – **Redo** repeats history from the earliest recLSN, including updates from transactions that were incomplete at the crash.
- Phase 3 – **Undo** the remaining effects of loser (incomplete) transactions.

### Crash recovery – Steps
1. **Analysis phase**

- Transaction table
- Dirty page table

2. **Redo phase (top - bottom)**

- Start scanning at the smallest recLSN in the Dirty Page Table. For each redoable update or CLR, consider it only when its page is in the table and its LSN is at least that page's recLSN; redo it only if the on-disk pageLSN is less than the record LSN. Update pageLSN after redo. This is the ARIES-style per-page test, not just a comparison to one global x.

3. **Undo phase (bottom - top)**

- Undo only loser transactions that were active or aborting at the crash; committed transactions are winners and are not undone.
- Initialize ToUndo with the lastLSN of every loser. Repeatedly remove the largest LSN.
- For a CLR, follow undoNextLSN without undoing the CLR. For an undoable update, undo it, append a CLR whose undoNextLSN is that update's prevLSN, then follow prevLSN. For other records, follow prevLSN ([CMU recovery notes, pp. 2 and 5–6](https://15445.courses.cs.cmu.edu/fall2024/notes/21-recovery.pdf)).
- Add each non-null next LSN to ToUndo. When a loser's chain reaches null, write END for that transaction; recovery Undo finishes only when ToUndo is empty.

#### Example1
| Time | Transaction Info                        |
| ---- | --------------------------------------- |
| 0    | BEGIN CHECKPOINT                        |
| 5    | END CHECKPOINT EMPTY XACT TABLE AND DPT |
| 10   | T1: UPDATE P1 OLD: YYY NEW: ZZZ         |
| 15   | T1: UPDATE P2 OLD: WWW NEW: XXX         |
| 20   | T1: COMMIT                              |

Answer:

1. Analysis phase  
   Transaction table:  
   T1, commit, 20  
   Dirty page table:  
   P1 10  
   P2 15
1. Redo phase  
   Dirty page smallest LSN: 10  
   Update logs: LSN 10 and LSN 15  
   LSN 10 => if pageLSN(P1) < 10, redo LSN 10, set pageLSN(P1) = 10  
   LSN 15 => if pageLSN(P2) < 15, redo LSN 15, set pageLSN(P2) = 15
1. Undo phase  
   nothing

#### Example2
| Time | Transaction Info                          |
| ---- | ----------------------------------------- |
| 0    | BEGIN CHECKPOINT                          |
| 5    | END CHECKPOINT (EMPTY XACT TABLE AND DPT) |
| 10   | T1: UPDATE P1 (OLD: YYY NEW: ZZZ)         |
| 15   | T1: UPDATE P2 (OLD: WWW NEW: XXX)         |
| 20   | T2: UPDATE P3 (OLD: UUU NEW: VVV)         |
| 25   | T1: COMMIT                                |
| 30   | T2: UPDATE P1 (OLD: ZZZ NEW: TTT)         |

Answer

1. Analysis phase  
   Transaction table:  
   T1, commit, 25  
   T2, running, 30
   Dirty page table:  
   P1 10  
   P2 15  
   P3 20
2. Redo phase  
   Dirty page smallest LSN: 10  
   Update-log candidates: LSN 10, 15, 20, and 30; apply the DPT/recLSN/pageLSN test to each.  
   LSN 10 => if pageLSN(P1) < 10, redo LSN 10, set pageLSN(P1) = 10  
   LSN 15 => if pageLSN(P2) < 15, redo LSN 15, set pageLSN(P2) = 15  
   LSN 20 => if pageLSN(P3) < 20, redo LSN 20, set pageLSN(P3) = 20  
   LSN 30 => if pageLSN(P1) < 30, redo LSN 30 and set pageLSN(P1) = 30; otherwise, skip it.
3. Undo phase  
   Initialize ToUndo with T2's lastLSN, 30. Undo LSN 30 and write a CLR whose undoNextLSN points to T2's previous log record, LSN 20.  
   Follow T2's prevLSN chain; undo each remaining undoable update and write a CLR pointing to that update's prevLSN. Continue through any non-update records until the chain reaches null, then write END for T2. The example table omits any BEGIN record.

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

- One-safe: acknowledge commit when its commit record is durable at the primary, without waiting for the backup. A primary-site loss before log transfer can lose an acknowledged commit.  
  (A primary-site failure can occur before the latest log records arrive at the backup.)
- Two-very-safe: acknowledge commit after the commit record is durable at both primary and backup. This reduces the risk of losing an acknowledged commit but reduces availability if either site is unavailable.
  (Acknowledgments wait for both sites, so a failure of either site can reduce commit availability.)
- Two-safe: use the two-site acknowledgment rule while both sites are active; if only the primary remains, acknowledge after the primary commit record is durable. This improves availability but has a failover scenario in which the backup may not contain a primary-only acknowledged commit.  
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

## CAP Theorem / CAP定理
During a network partition, a distributed service cannot guarantee both availability for every request and linearizable consistency for all operations. Partition tolerance describes the failure model, not a property that a system can simply opt out of. A system may reject or delay some requests, or return responses that do not preserve linearizability. This statement does not imply that a product permanently chooses only two labels in ordinary operation. [Gilbert and Lynch's formal CAP result](https://www.comp.nus.edu.sg/~gilbert/pubs/BrewersConjecture-SigAct.pdf) states the impossibility under its model.

- **Consistency** in the CAP result means linearizability: operations appear to take effect atomically in an order consistent with real time.
- **Availability** means every request to a non-failing node eventually receives a response.
- **Partition tolerance** means the system continues operating despite communication partitions, under the theorem's model.

## Different Types of Consistency
Consistency guarantees form a spectrum and should be named precisely:

- Linearizable (strong) reads reflect the latest completed write in a real-time order.
- Eventual consistency means replicas converge if updates stop; a read before convergence may be stale.
- Causal consistency preserves the order of causally related operations.
- Session guarantees include read-your-writes and monotonic reads/writes. Their usefulness depends on the application.

### Tradeoff between C and A
e.g., Airline reservation system

- As an application example, a reservation service might tolerate stale reads when many seats remain but require stricter coordination near capacity. This is a business policy example, not a statement of the CAP theorem.

### Segment C and A
- Segment the system into different components. Each provides different types of guarantees.
- Service components may provide different consistency and availability guarantees; summarize each component's contract rather than assigning one binary label to the whole application.
- Can be partitioned along different dimensions (time)
- E.g., partition according to different data
  - Product information - availability, if there is some out dated data, it's OK
  - Shopping cart – availability, eventually add to cart is fine
  - Checkout, pay the bill, shipping records - consistency, avoid sold out or outdated delivery...

### If no network partition
- No network partition, but still some failure of the node
- Tradeoff between Consistency and Latency (unavailable -> extreme high latency)
- Achieving different levels of consistency/availability takes different amount of time
- Maintaining consistency should balance between the strictness of consistency versus availability

## BASE Properties
BASE is an informal design mnemonic sometimes used for systems that favor availability and asynchronous convergence; it is not a consequence that every partition-tolerant system must follow. The terms are commonly expanded as Basically Available, Soft state, and Eventual consistency. NoSQL products vary and do not all share one consistency model.

### CAP -> PACELC
PACELC asks: if there is a partition (P), does the design favor availability (A) or consistency (C); else (E), does it favor lower latency (L) or consistency (C)? The labels describe a chosen design tradeoff, not a universal property of a product. [Abadi's PACELC paper](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf) introduces this extension.

- PA/EL: favor availability during partitions and lower latency otherwise.
- PC/EC: favor consistency in both cases, accepting reduced availability during partitions and higher latency otherwise.
- PA/EC: favor availability during partitions and consistency otherwise.
- PC/EL: favor consistency during partitions and lower latency otherwise.

## NoSQL
### Type of NoSQL Databases
1. Document Stores
   - Documents are stored as self-contained values, commonly JSON, BSON, or XML; supported encodings and query features depend on the product.
   - Documents can be indexed
2. Graph Databases
   - Data are represented as vertices and edges
   - Graph databases are powerful for graph-like queries (e.g., find the shortest path between two elements)
3. Key-Value Stores
   - Keys are mapped to (possibly) more complex value (e.g., lists)
   - Keys can be stored in a hash table and can be distributed easily
   - Many key-value stores expose get/put/update/delete operations by key and do not provide relational joins; query and transaction features vary by product.
4. Columnar Databases
   - Columnar storage lays out values by column rather than by row and can be used by relational or analytical systems; it is a storage organization, not a NoSQL model by itself.

## Data Warehousing
![](dataWarehousnig.png)

- A classical data warehouse consolidates historical data from multiple sources under an integrated schema for analysis. Modern warehouses may be physically distributed.
- When and how to gather data
  - Source driven architecture: data sources transmit new information to warehouse, either continuously or periodically (e.g. at night) I.e. data source give out
  - Destination driven architecture: warehouse periodically requests new information from data sources. I.e. Data warehouse requesting

### Data Warehousing – Design Issues
- Synchronous coordination such as two-phase commit across an OLTP source and analytical warehouse can add latency and reduce availability. Many designs accept ingestion lag and load updates periodically, but freshness requirements vary by workload.
- What schema to use
  - Depends on purpose
  - Schema integration
- Data cleansing
  - e.g., Correct mistakes in addresses (misspellings, zip code errors)
  - e.g., Merge address lists from different sources and purge duplicates
- How to propagate updates - The data stored in a data warehouse is documented with an element of time, either explicitly or implicitly
- What data to summarize
  - Raw data may be too large to store
  - Aggregate values (totals/subtotals) often suffice
  - Where the engine supports materialized-view rewrite and the query is eligible, a query on raw data may be answered from a stored aggregate.

## Distributed Database / 分布式数据库
### DBMS in Real life
- Many production DBMS deployments serve networked clients; embedded databases are also common.
- Large companies have multiple servers working together
- Many systems has a complex distributed architecture
- e.g., bank transactions in different branches

### Two-Phase Commit Protocol (2PC), distinct from Two-Phase Locking (2PL)
2PC coordinates the atomic outcome across participants; it does not itself provide transaction isolation. [PostgreSQL's two-phase transaction documentation](https://www.postgresql.org/docs/18/two-phase.html) describes durable prepared transactions; [Gray and Lamport's transaction-commit paper](https://lamport.azurewebsites.net/video/consensus-on-transaction-commit.pdf) explains why the coordinator waits for all resource managers before committing.


- Goal: either all of the servers commit the transaction, or all of them abort the transaction
- One of the servers becomes the coordinator who must ensures the same outcome at all of the servers

Phase 1 (voting phase)

- coordinator asks all participants if they can commit
- each participant votes
- A YES vote means the participant is prepared: it must durably record the prepared state and wait for the coordinator's decision. It cannot unilaterally decide the global outcome after voting YES.
- A NO vote lets the coordinator decide abort.

Phase 2 (completion phase)

- coordinator tells all participants to commit or abort
- the participants carry out the joint decision

![](./twophaseCommitProtocol.png)

1. `Coordinator -> Participant`: `canCommit (trans)`  
   The coordinator asks whether the participant can commit a transaction.

2. `Participant -> Coordinator`: `Yes / No`  
   The participant replies with its vote on whether it can commit the transaction.

3. The coordinator makes one global decision: COMMIT requires every required YES vote, while a NO vote or a pre-decision timeout can lead to ABORT:

   - `Coordinator -> Participant`: `doCommit (trans)`  
      Only when every required participant has voted YES does the coordinator durably record the global COMMIT decision and then notify all participants to commit.
   - `Coordinator -> Participant`: `doAbort (trans)`  
      If any participant votes NO, or a required vote is still missing when the coordinator times out before making a commit decision, the coordinator durably records global ABORT and notifies all participants to abort, including participants that already voted YES.

4. `Participant -> Coordinator`: `haveCommitted (trans, participant)`  
   The participant confirms that it has committed the transaction, notifying the coordinator.

5. If a participant recovers in the prepared state without a recorded decision, it asks the coordinator for the durable outcome. If the coordinator is unreachable, the prepared participant may have to wait.

- Before the global decision, a participant may vote NO and the coordinator may choose abort if any vote is NO or a participant fails to respond. After a participant has voted YES, it remains durably prepared and can block if the coordinator is unreachable; timeout alone does not safely tell it to abort. The coordinator records and communicates the decision, and participants follow it.
- If the decision is abort, the coordinator asks participants to roll back.
- The coordinator records its decision durably before notifying participants; participants record and follow the decision as required by their recovery protocol.

### Concurrency Control in Networked System
![](concurrencyProblemNetworked.png)

- Each server is responsible for applying concurrency control to its own objects
- The members of a collection of servers of distributed transactions are jointly responsible for ensuring that they are performed in a serially equivalent manner
- Servers independently acting would not work
- If transaction T is before transaction U in their conflicting access to objects at one of the servers
- Then: They must be in that order at all of the servers whose objects are accessed in a conflicting manner by both T and U
- The Coordinator should assure this

### Concurrency Control Review
Timestamp ordering concurrency control

- The coordinator accessed by a transaction issues a **globally unique timestamp**
- The timestamp is passed **with each object access**
- The servers are jointly responsible for ensuring serial equivalence, that is if T access an object before U, then T is before U at all objects

Optimistic concurrency control  
For distributed transactions to work:

- When optimistic concurrency control is combined with 2PC, each participant validates before voting YES; 2PC itself does not provide concurrency validation.
- A distributed optimistic protocol must define a consistent transaction order, often using globally comparable timestamps.

### Transactions with replicated data
One-copy Serializability  
The effect of transactions on replicated objects should be the **same as if they had been performed one at a time on a single set of objects**

If all servers are available then no issue – but what if some servers are not available?

### Available copies replication
- The available copies replication scheme is designed to allow some servers to be temporarily unavailable
- Before a transaction commits, it checks for failures and recoveries of the RMs it has contacted, the set should not change during execution

e.g., X fails before T’s deposit. T would check if X is still available. If X is unavailable, then T will abort.
