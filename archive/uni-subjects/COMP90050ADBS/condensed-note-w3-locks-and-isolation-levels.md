# What do shared, exclusive, and granular locks guarantee? / 共享锁、排他锁与粒度锁能保证什么？

Compatibility rules govern which readers and writers may hold locks together. Well-formed two-phase locking gives a serializability guarantee for legal histories; coarse and fine-grained locks trade lock-manager overhead against concurrency. Historical Degree 0–3 labels are not SQL isolation-level names. / 锁兼容规则决定读写者能否同时持锁。对合法历史而言，结构良好的两阶段锁保证可串行化；粗细粒度锁权衡锁管理开销与并发度。历史 Degree 0–3 标签不是 SQL 隔离级别名称。

## Locks / 锁
### Slock & Xlock
- SLOCK (shared lock) that allows other transactions to **read**, but not write/modify the shared resource.
- A lock on an object should not be granted to a transaction while that object is locked by another transaction in an incompatible mode.
- An XLOCK lets its holder read and modify the object; while it is held, other transactions cannot hold an incompatible SLOCK or XLOCK on that object ([CMU two-phase locking notes](https://15445.courses.cs.cmu.edu/fall2024/notes/17-twophaselocking.pdf)).

#### Lock Compability
|                 | Free | Shared (Slock) | Exclusive (Xlock) |
| --------------- | ---- | -------------- | ----------------- |
| Request - Slock | √    | √              | ×                 |
| Request - Xlock | √    | ×              | ×                 |

#### Slock & Xlock – When to use which one?
- Actions in Transactions are: READ, WRITE, XLOCK, SLOCK, UNLOCK, BEGIN, COMMIT, ROLLBACK
- BEGIN, END , SLOCK, XLOCK can be ignored as they can be automatically inserted in terms of the corresponding operations
- If a transaction ends with a COMMIT, it is replaced with: {UNLOCK A if SLOCK A or XLOCK A appears in T for any object A}.
- ROLLBACK can be replaced by {**WRITE(UNDO)** A if WRITE A appears in T for any object A} { UNLOCK A if SLOCK A or XLOCK A appears in T for any object A}.

#### Example
![transactionLockExample](./transactionLockExample.png)
Note T2 need to WRITE (UNDO) B because it want to ROLLBACK

### Isolation Concept
- **Well-formed transactions**: A transaction is well formed if all READ, WRITE and UNLOCK operations are covered by appropriate LOCK operations
- **Two phase transactions**: A transaction is two phased if all LOCK operations precede all its UNLOCK operations. I.e. All locks are before unlocks

### Isolation Theorem
- **Locking theorem**: If all transactions are well formed and two-phased, then any legal (does not grant conflicting grants) history will be isolated.
- **Locking theorem (Converse)**: If a transaction is not well formed or not two-phase, there exists a counterexample with another transaction that violates the theorem's guarantee. This does not mean every schedule involving it is nonserializable.
- **Rollback theorem**: An update transaction that does an UNLOCK and then does a ROLLBACK is **not** two phase. The idea is ROLLBACK is a Write action, therefore it is a unlock before lock.

### Degree of Isolation
The degrees below are a historical lock-based classification, not names or exact equivalents for SQL isolation levels.


#### Degree 3:
![](./degree3.png)\
A Three degree isolated Transaction has no lost updates, and has repeatable reads.\
Lock protocol is **two phase and well formed**.\
It is sensitive to the following conflicts: write->write; write ->read; read->write

#### Degree 2
![](./degree2.png)\
Degree 2: A Two degree isolated transaction has no lost updates and no dirty reads.\
Lock protocol is two phase with **respect to exclusive locks** and well formed with respect to **Reads and writes**. (May have Non repeatable reads.)\
It is sensitive to the following conflicts: write- >write; write ->read;

#### Degree 1
![](./degree1.png)\
Degree 1: A One degree isolation has no lost updates.\
Lock protocol is two phase with **respect to exclusive locks** and well formed with respect to **writes**.\
It is sensitive the following conflicts: write- >write;

#### Degree 0
![](./degree0.png)\
Degree 0 : A Zero degree transaction does not overwrite another transactions dirty data if the other transaction is at least One degree.\
Lock protocol is well-formed with respect to writes. It ignores all conflicts.

## Granular Lock
- **Definition** - we need to build some **hierarchy**, then locks can be taken at any level, which will automatically grant the locks on its descendants.
- **Intention** - allow concurrent runs as much as possible for a better performance, while avoiding conflicts as much as possible
- **Steps**
  - Pick a set of column values (predicates).
  - They form a graph/tree structure.
  - Lock the nodes in this graph/tree
- Example\
  ![](./granularitylockExample.png)

### Granularity of locks (coarse & fine)
Coarse locks reduce the number of lock-manager entries and their overhead, but limit concurrency and can increase contention. Fine-grained record locks require more lock entries but can allow more independent work to proceed concurrently ([CMU two-phase locking notes](https://15445.courses.cs.cmu.edu/fall2024/notes/17-twophaselocking.pdf)).

### Express intention
Intention mode locks on coarse granules.

### Types of granular locks
| Type | Name                                                                                     |
| ---- | ---------------------------------------------------------------------------------------- |
| X    | exclusive lock                                                                           |
| S    | shared lock                                                                              |
| U    | update lock – intention to update in the future                                          |
| IS   | intent to set shared locks at finer granularity                                          |
| IX   | Intent to set shared or exclusive locks at finer granularity                             |
| SIX  | a coarse granularity shared lock with an Intent to set finer granularity exclusive locks |

### Compatibility Mode of Granular Locks (symmetric)
![](./compabilityGranularLocks.png)

### Isolation Concept
- Acquire locks from root to leaf.
- Release locks from leaf to root.
- To acquire an S mode or IS mode lock on a non-root node, **one** parent must be held in IS mode or higher (one of {IS,IX,S,SIX,U,X}).
- To acquire an X, U, SIX, or IX mode lock on a non-root node, **all** parents must be held in IX mode or higher (one of {IX,SIX,U,X}).

#### e.g., - deadlock
![](./deadlockExample.png)
T1:

```
SLock A
Read A
If (A== 3) {
    % Upgrading Slock to Xlock
    Xlock A
    Write A
}
Unlock A
```

T2:

```
SLock A
Read A
If (A==3) {
    % Upgrading Slock to Xlock
    Xlock A
    Write A
}
Unlock A
```

T3:

```
SLock A
Read A
Unlock A
```

Both T1 and T2 already hold SLOCK A. Each then requests an XLOCK upgrade; each request waits because the other transaction still holds SLOCK A, so neither can proceed to release its shared lock.

#### solution
For this illustrated conditional update, releasing SLOCK A and then requesting XLOCK A avoids the upgrade cycle only if the transaction rereads and rechecks the condition after the XLOCK is granted. This is a specialized read/recheck pattern, not a general strict-2PL recipe.
![](./deadlockexamplesolution.png)
T1:

```
SLock A
Read A
If (A == 3){
    % Release lock and try in Xlock mode
    Unlock(A)
    Xlock A
    Read A
    if(A == 3){
        Write A
    }
}
Unlock A
```

T2:

```
SLock A
Read A
If (A == 3){
    % Release lock and try in Xlock mode
    Unlock(A)
    Xlock A
    Read A
    if(A == 3){
        Write A
    }
}
Unlock A
```

T3

```
SLock A
Read A
Unlock A
```
