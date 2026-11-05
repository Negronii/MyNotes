# How does WAL and ARIES recovery preserve committed work after a crash? / WAL 与 ARIES 恢复如何在崩溃后保留已提交工作？

Write-ahead logging makes required log records durable before dependent page writes or commit acknowledgement. ARIES-style recovery reconstructs transaction and dirty-page state, redoes history from relevant recLSNs, then undoes loser transactions while writing CLRs. / 预写日志要求相关日志记录先于依赖的数据页写入或提交确认而持久化。ARIES 风格恢复重建事务表和脏页表，从相关 recLSN 重做历史，再撤销失败事务并写入 CLR。

## Crash Recovery / 崩溃恢复
Recover from a failure either when a single-instance database crashes or all instances crash.\
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
- Contains transactionID, status (running/committed/aborted), and lastLSN.\
  During analysis, remove a transaction when its END record is encountered. A transaction with a durable COMMIT but no END at crash is a winner that may remain in the table; it is not undone.
  e.g.

| transactionID | status     | lastLSN |
| ------------- | ---------- | ------- |
| T1            | running    | 40      |
| T2            | committed  | 80      |

### Dirty Page Table
- One entry per dirty page in the buffer pool. A page becomes dirty after an update changes it.
- In ARIES, **recLSN** is the LSN of the first update that made the page dirty after it was last clean; it is the earliest update that may need redo for that page. Loading a page does not itself make it dirty ([Database System Concepts, 7e, ch. 19](https://www.db-book.com/slides-dir/PDF-dir/ch19.pdf)).\
  e.g.

| Pageid | recLSN |
| ------ | ------ |
| P1     | 10     |
| P2     | 50     |
| P3     | 80     |

![](./dirtyPageTable.png)

### Checkpoint
Periodically, the DBMS creates a checkpoint, in order to **minimize the time taken to recover in the event of a system crash**.\
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

1. Analysis phase\
   Transaction table:\
   T1, commit, 20\
   Dirty page table:\
   P1 10\
   P2 15
1. Redo phase\
   Dirty page smallest LSN: 10\
   Update logs: LSN 10 and LSN 15\
   LSN 10 => if pageLSN(P1) < 10, redo LSN 10, set pageLSN(P1) = 10\
   LSN 15 => if pageLSN(P2) < 15, redo LSN 15, set pageLSN(P2) = 15
1. Undo phase\
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

1. Analysis phase\
   Transaction table:\
   T1, commit, 25\
   T2, running, 30
   Dirty page table:\
   P1 10\
   P2 15\
   P3 20
2. Redo phase\
   Dirty page smallest LSN: 10\
   Update-log candidates: LSN 10, 15, 20, and 30; apply the DPT/recLSN/pageLSN test to each.\
   LSN 10 => if pageLSN(P1) < 10, redo LSN 10, set pageLSN(P1) = 10\
   LSN 15 => if pageLSN(P2) < 15, redo LSN 15, set pageLSN(P2) = 15\
   LSN 20 => if pageLSN(P3) < 20, redo LSN 20, set pageLSN(P3) = 20\
   LSN 30 => if pageLSN(P1) < 30, redo LSN 30 and set pageLSN(P1) = 30; otherwise, skip it.
3. Undo phase\
   Initialize ToUndo with T2's lastLSN, 30. Undo LSN 30 and write a CLR whose undoNextLSN points to T2's previous log record, LSN 20.\
   Follow T2's prevLSN chain; undo each remaining undoable update and write a CLR pointing to that update's prevLSN. Continue through any non-update records until the chain reaches null, then write END for T2. The example table omits any BEGIN record.
