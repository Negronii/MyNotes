# When do optimistic validation and snapshot isolation allow concurrent updates? / 乐观验证与快照隔离何时允许并发更新？

Optimistic schemes defer conflict checks until validation. Snapshot isolation reads a fixed snapshot and commonly detects writes to the same row, yet disjoint write sets can still violate a cross-row invariant through write skew. Timestamp protocols also need their own explicit rules. / 乐观方案把冲突检查推迟到验证阶段。快照隔离从固定快照读取，并通常检测对同一行的并发写入；但不同写集仍可能因写偏斜共同违反跨行不变量。时间戳协议也需明确自己的规则。

## Optimistic Locking
- When conflicts are rare, transactions can execute operations without managing locks and without waiting for locks - higher throughput
- Use data without locks
- Before committing, each transaction rechecks its read-set and validates the values or versions used by the computation. A value comparison can miss an intervening update that changes a value and later restores it (ABA); version or write-sequence checks are needed when that history matters.
- If any conflict found, the transaction repeats the attempt
- If no conflict, make changes and commit

### Example
```sql
% Read without lock
Read A into A1
Read B into B1
Read C into C1
Loop: Compute new values based on A1 and B1
    % Start taking locks
    % Read again
    Slock A; Read A into A2
    Slock B; Read B into B2
    Xlock C; Read C into C2
    if (A1 == A2 & B1 == B2 & C1 == C2)
        Write new value into C
        commit
        Unlock A, B and C
    else % read data is changed
        A1 = A2
        B1 = B2
        C1 = C2
        unlock A ,B and C
        goto Loop
end
```

On success, this path holds locks for the recheck and write, but lock duration and throughput depend on contention and work inside the critical section. Value equality does not prove that no intervening update occurred.\
Advantage: avoids holding locks during the initial computation when conflicts are rare\
Disadvantage: Repeat in Loop for long time

## Snapshot Isolation / 快照隔离
Assume every read in one transaction attempt uses a fixed snapshot S. The write-conflict test below represents first-committer-wins validation against versions committed after S; a conflict aborts the attempt, and a retry starts a new transaction with a new snapshot.

```text
begin attempt using snapshot S
Read C, D, A, and B from S
Compute new values C3 and D3 from A and B
if either C or D has a version committed after S:
    abort this attempt
    retry in a new transaction using a new snapshot
else:
    write C3 to C and D3 to D
    commit
```

Snapshot isolation gives a transaction a consistent snapshot and commonly uses first-committer-wins for concurrent writes to the same row. It can still permit write skew, so it is not generally serializable. Product behavior and isolation-level names differ: [PostgreSQL 18 documents MVCC and Serializable Snapshot Isolation](https://www.postgresql.org/docs/18/mvcc-intro.html) and [application-level consistency anomalies](https://www.postgresql.org/docs/18/applevel-consistency.html); [SQL Server 17 distinguishes RCSI from SNAPSHOT](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver17); [Oracle 26 documents its own multiversion read-consistency model](https://docs.oracle.com/en/database/oracle/oracle-database/26/cncpt/data-concurrency-and-consistency.html). These implementations should not be collapsed into one generic product claim.

## Two phase locking Transaction - Snapshot Locking potential problem
Integrity constraint A+B >= 0; A = 100; B = 100;
T1:

```
Lock(X,A)
Lock(S,B)
Read A to A1;
Read B to B1;
A1 = A1 -200;
if (A1+ B1 >= 0)
    Write A1 to A
    Commit
else abort
end
Unlock (all locks)
```

T2:

```
Lock(S,A)
Lock(X,B)
Read A to A1;
Read B to B1;
B1 = B1 -200;
If (A1+ B1 >= 0)
    Write B1 to B
    Commit
else abort
end
Unlock (all locks)
```

Only one transaction can commit.

Snapshot Isolation Transaction - Snapshot Locking potential problem
Integrity constraint A+B >= 0; A = 100; B = 100;
T1:

```sql
Loop:
    Read A to A1;
    Read B to B1;
    A3 = A1 -200;
    Lock(X, A)
    Read A to A2
    if (A1 != A2)
        Unlock(A)
        goto Loop
    % potential problem: B1 is read without lock, the value of B possiblily has been changed
    elseif (A3+ B1 >= 0)
        Write A3 to A
        Commit
    else abort
Unlock (all locks)
```

T2:

```sql
Loop:
    Read A to A1;
    Read B to B1;
    B3 = B1 -200;
    Lock(X, B)
    Read B to B2
    if (B1 != B2)
        Unlock(B)
        goto Loop
    % A1 is read without lock
    elseif (A1+ B3 >= 0)
        Write B3 to B
        Commit
    else abort
Unlock (all locks)
```

Under snapshot-style validation, both transactions can commit because they write different rows, yet the invariant A+B >= 0 is violated. This is write skew: no serial order permits both updates.

## Time Stamping / 时间戳排序
This is one optimistic timestamp-validation model: at validation, a transaction may abort if a conflicting update is newer than the version it read. Basic timestamp-ordering protocols instead assign transaction timestamps and maintain read/write timestamps per item, checking operations against those timestamps. Do not treat this sentence as the general timestamp-ordering algorithm. Validation, commit durability, and version retention are separate concerns.

**Time Domain Versioning**\
In this time-domain versioning example, an update creates a new version with a validity interval rather than overwriting the earlier version. This temporal-data model is distinct from the basic timestamp-ordering protocol above.\
<o,<V1, [t1, t2)>, <V2, [t2,t3)>, <V3,[t3,\*)>

e.g.
T1
select average (salary)
from employee

T2
update employee
set salary = salary\*1.1
where salary < $40000

If T1 reads from a snapshot taken before T2 commits, it can compute the average from the older salary versions and the read-only T1 may commit after T2. This schedule alone does not require T1 to abort; a timestamp-validation protocol that rejects stale reads would need to be specified separately. Under MVCC, T2 need not wait for this read-only T1 to finish, subject to product-specific rules.
