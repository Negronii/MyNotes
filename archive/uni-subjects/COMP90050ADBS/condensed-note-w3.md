# Transactions and Concurrency Control / 事务与并发控制

核心概念：并发控制协调事务交错，锁兼容与两阶段规则限制冲突；隔离级别说明可观察的并发异常，不等同于某一种锁或 MVCC 机制。快照隔离读取固定快照且通常检测同一行写冲突，仍可能因不同写集产生写偏斜；应用不变量和产品保证需另外核对。

## Transactions / 事务
### Transaction - A unit of work in a database
- A transaction can have any number and type of operations in it
- Either happens as a whole or not
- Transactions ideally have four properties, commonly known as ACID properties

### ACID (Atomicity, Consistency, Isolation, Durability) properties:
- Atomicity - All changes to data are performed as if they are a single operation. That is, all the changes are performed, or none of them are.
  Example – A transaction that (i) subtracts $100 if balance >100 (ii) deposits $100 to another account
  (both actions with either happen together or none will happen)
- Consistency - Data is in a ‘consistent’ state when a transaction starts and when it ends – in other words, any data written to the database must be valid according to all defined rules (e.g., no duplicate student ID, no negative fund transfer, etc.)
  - What is ‘consistent’ - depends on the application and context constraints
  - It is not easily computable in general
  - Serializable execution orders participating transactions as if they ran one at a time. It does not enforce an application invariant unless the relevant constraints are declared or every transaction checks them correctly.
- Isolation controls how concurrent transactions observe one another. Together with atomic commit, it prevents another transaction from observing only one side of a completed transfer; isolation alone does not make the debit and credit atomic.
- Durability- the system should tolerate system failures and any committed updates should not be lost.

### Types of Actions
- Unprotected actions - no ACID property
- Protected actions - these actions are not externalised before they are completely done. These actions are controlled and can be rolled back if required. These have ACID property.
- Real actions - these are real physical actions once performed cannot be undone. In many situations, atomicity is not possible with real actions (e.g., firing two rockets as a single atomic action)

### Embedded SQL example in C
This partial example targets PostgreSQL ECPG: assume the connection is established and the surrounding C program includes the required headers. ECPG preprocesses embedded EXEC SQL statements before the C compiler; this is not ODBC ([ECPG documentation](https://www.postgresql.org/docs/18/ecpg-concept.html)).

```c
EXEC SQL INCLUDE sqlca;

int main(void) {
    EXEC SQL BEGIN DECLARE SECTION;
    /* Host variables used to exchange values with SQL */
    int order_id;
    int cust_id;
    char salesperson[10];
    char status[6];
    EXEC SQL END DECLARE SECTION;

    EXEC SQL WHENEVER SQLERROR GOTO query_error;
    EXEC SQL WHENEVER NOT FOUND GOTO bad_number;
    printf("Enter order number: ");
    scanf("%d", &order_id);
    EXEC SQL SELECT CustID, SalesPerson, Status
        INTO :cust_id, :salesperson, :status
        FROM Orders
        WHERE OrderID = :order_id;
    printf("Customer number: %d\n", cust_id);
    printf("Salesperson: %s\n", salesperson);
    printf("Status: %s\n", status);
    return 0;

query_error:
    fprintf(stderr, "SQL error: %ld\n", sqlca.sqlcode);
    return 1;
bad_number:
    fprintf(stderr, "Invalid order number.\n");
    return 1;
    EXEC SQL WHENEVER SQLERROR CONTINUE;
    EXEC SQL WHENEVER NOT FOUND CONTINUE;
}
```

- **Host Variables** - Declared in a section enclosed by the **BEGIN** DECLARE SECTION and **END** DECLARE SECTION. While accessing these variables, they are prefixed by a colon “:”. The colon is essential to distinguish between host variables and database objects (for example tables and columns).
- **Data Types** - The data types supported by a DBMS and a host language can be quite different. e.g. if we have int type id in DB, we can't use string id in C
- **Error Handling** - The DBMS reports run-time errors to the applications program through an SQL Communications Area (SQLCA) by INCLUDE SQLCA. The WHENEVER...GOTO statement tells the pre-processor to generate error- handling code to process errors returned by the DBMS.
- **Singleton SELECT** - The statement used to return the data is a singleton SELECT statement; that is, it returns only a single row of data. Therefore, the code
  example does not declare or use cursors.

### Flat Transaction
Everything inside the BEGIN WORK and COMMIT WORK is at the same level. The transaction will either survive together with everything else (commit) Or it will be rolled back with everything else (abort) – if some errors happen

```c
/* PostgreSQL ECPG fragment; assumes an open connection and the preceding sample's global sqlca. */
long BuySomething(long acc_id, long amount) {
    EXEC SQL BEGIN DECLARE SECTION;
    long sql_acc_id;
    long sql_amount;
    long balance_after;
    EXEC SQL END DECLARE SECTION;
    sql_acc_id = acc_id;
    sql_amount = amount;

    EXEC SQL WHENEVER SQLERROR CONTINUE;
    EXEC SQL INSERT INTO history(AccId, Amount, time)
        VALUES (:sql_acc_id, :sql_amount, CURRENT_TIMESTAMP);
    if (sqlca.sqlcode < 0) return -1;
    EXEC SQL UPDATE accounts
        SET AccBalance = AccBalance - :sql_amount
        WHERE AccId = :sql_acc_id;
    if (sqlca.sqlcode < 0) return -1;
    EXEC SQL SELECT AccBalance INTO :balance_after
        FROM accounts
        WHERE AccId = :sql_acc_id;
    if (sqlca.sqlcode != 0) return -1;
    return balance_after; /* the post-update balance */
}

int process_purchase(long acc_id, long amount) {
    long acc_balance;
    EXEC SQL BEGIN WORK;
    if (sqlca.sqlcode < 0) return -1;
    acc_balance = BuySomething(acc_id, amount);
    if (sqlca.sqlcode < 0 || acc_balance < 0) {
        EXEC SQL ROLLBACK WORK;
        return -1;
    }
    EXEC SQL COMMIT WORK;
    return sqlca.sqlcode < 0 ? -1 : 0;
}
```

#### Flat Transaction - Limitation
Flat transactions do not model many real applications.

```
BEGIN WORK
S1 : book flight from Melbourne to Singapore S2: book flight from Singapore to London
S3: book flight from London to Dublin
END WORK
```

From Dublin if we cannot reach our final destination instead we wish to fly to Paris from Singapore and then reach our final destination.

If we roll back we need to redo the booking from Melbourne to Singapore which is a waste.

#### Flat Transaction – Solution: Save Points
![save-points](./save-points.png)

- The only reason why an application program needs an identifier for a savepoint is that it may later want to re-establish (return to) that savepoint.
- To do that, the application invokes the ROLLBACK WORK function, but rather than requesting the entire transaction to be aborted, it passes the number of the savepoint it wants to be restored.

### Nested Transaction
![nested transaction](nestedTransaction.png)
It is a tree of executions, T1 can have more T11 and T12.... The left hand side is called parent transaction.

#### Rules to follow in Nested Transaction
##### Commit rule
- In the course's closed-nesting model, a child may provisionally commit before its parent finishes; that result becomes visible to the parent but is not durable or externally visible until the root transaction commits.
- If an ancestor aborts, the provisional effects of its descendants are rolled back.

##### Roll back rules
- If a subtransaction rolls back all its children are forced to roll back

##### Visibility rules
- Changes made by a subtransaction are visible to the parent only when the subtransaction commits.
- All objects of parent are visible to its children.

Implication of this is that the parent should not modify objects while children are accessing them. This is not a problem as parent is not run in parallel with its children.

This course model does not run a parent and its child in parallel; sibling children may run in parallel.

### Transaction Processing Monitor (TP Monitor)
The main function of a TP monitor is to integrate other system components and manage resources.

- TP monitors manage the transfer of data between clients and servers
- breaks down applications or code into transactions and ensures that all databases are updated properly
- It also takes appropriate actions if any error occurs

### TP Monitor Services
- **Heterogeneity**: A transaction spanning different resource managers needs a coordinated outcome. Two-phase commit can coordinate atomic commit; isolation and application consistency require separate mechanisms.
- **Control communication**: If the application communicates with other **remote processes**, the local TP monitor should maintain the communication status among the processes to be able to recover from a crash.
- **Terminal management**: Since many terminals run client software, the TP monitor should provide appropriate ACID property between the client and the server processes.
- **Presentation service**: this is similar to terminal management in the sense it has to deal with different presentation ( user interface) software -- e.g. X-windows
- **Context management**: E.g. maintaining the sessions etc.
  Start/Restart: There is no difference between start and restart in TP based system.

## Concurrency Control / 并发控制
For correct execution, we need to impose exclusive access to the shared variable counter by Tasks.

- To resolve conflicts
- To preserve database consistency

### Different ways for concurrency control
- **Dekker's algorithm (using code)** - needs almost no hardware support, but the code is very complicated to implement for more than two transactions/processes
- **OS supported primitives** (through interruption call) - expensive, independent of number of processes, machine independent
- **Spin locks** (using atomic lock/unlock instructions) – most commonly used

### Dekker's algorithm
int c1, c2, turn = 1; /_ global variable_/

T1
{ some code T1}

```c
/* T1 wants exclusive access to the resource and we assume initially c1 = = 0*/
c1 = 1; turn = 2;
repeat until { c2 == 0 or turn == 1}
/* Start of exclusive access to the shared resource (successfully changed variables) */
use the resource
counter = counter+1;
/* release the resource */
c1 = 0;
{some other code of T1}
```

T2
{ some code T2}

```c
/* T2 wants exclusive access to the resource and we assume initially c2 = = 0 */
c2 = 1; turn = 1;
repeat until { c1 == 0 or turn == 2}
/* Start of exclusive access to the shared resource */
use the resource
counter = counter+1;
/* release the resource */
c2 = 0 ;
{some other code of T2}
```

- needs almost no hardware support although it needs atomic reads and writes to main memory
- the code is very complicated to implement if more than two transactions/ process are involved
- harder to understand the algorithm for more than two process
  takes lot of storage space
- uses busy waiting
- efficient if the lock contention (that is frequency of access to the locks) is low

### OS supported primitives
- A blocking mutex or semaphore may ask the OS scheduler to park a waiting thread and wake it later; this avoids spinning while blocked but has scheduling and context-switch overhead. The implementation may still use hardware atomic operations internally. It is not necessarily an interrupt on every lock request.

### Spin Lock
- Spin locks use an atomic read-modify-write primitive such as test-and-set or compare-and-swap, and busy-wait while the lock is held. They can be useful for very short critical sections with low contention, but waste CPU under contention; database systems also use blocking locks and latches. Implementation and processor support vary.

#### Spin lock – Test and Set
```text
Atomic pseudocode (not C or a processor-specific implementation):
testAndSet(lock):
    old = atomic_exchange(lock, LOCKED)
    return old == UNLOCKED
```

Using test and set in spin lock for exclusive access

```text
lock = UNLOCKED
```

T1

```text
while (!testAndSet(&lock)) { /* spin until acquired */ }
/* exclusive access for T1 */
counter = counter + 1
atomic_store(lock, UNLOCKED)
```

T2

```text
while (!testAndSet(&lock)) { /* spin until acquired */ }
/* exclusive access for T2 */
counter = counter + 1
atomic_store(lock, UNLOCKED)
```

#### Spin lock – Compare and Swap
```c
boolean cs(int *cell, int *old, int *new)
{/* the following is executed atomically*/
if (*cell == *old) { *cell = *new; return TRUE;}
else { *old = *cell; return FALSE;} //put it into old and will be used later
}
```

#### Short summary
Test-and-set and compare-and-swap are both atomic read-modify-write operations used to implement synchronization. Neither is accurately described as locking only reads or only writes. The pseudocode above is a teaching sketch; real primitives also have memory-ordering requirements.

## Semaphore
Derived from train and track

- Try to Get track, wait if track not clear
- If Get track was successful, use it (no other train will be able to use it at the same time)
- Once the train passes, the semaphore is set until the train exits that section of track
  Computer semaphores have a **get()** routine that acquires the semaphore (perhaps waiting until it is free) and a **give()** routine that returns the semaphore to the free state, perhaps **signalling** (waking up) a waiting process.

### Exclusive mode Semaphore
![](Semaphore.png)

- A semaphore or mutex implementation may track waiters in a queue; whether the queue is FIFO and how ownership is represented are implementation choices. A waiting thread can be awakened when the resource becomes available.

### Convoy avoiding semaphore
Waking every waiter can cause a thundering herd as they all compete to acquire the resource. Queueing and handoff policies trade fairness, throughput, and scheduling overhead; waking all waiters is not a general convoy-avoidance guarantee.

## Deadlock / 死锁
- Deadlocks are rare, however, they do occur and the database has to deal with them when they occur
- In a deadlock, each process in the deadlock is waiting for another member to release the resources it wants.

### Deadlock - Solutions
- Have enough resources so that no waiting occurs – not practical since we cannot have infinite resources
- Do not allow a process to wait, simply rollback after a certain time. This can create live locks which are worse than deadlocks.
- Linearly order the resources and request of resources should follow this order,
- i.e., a transaction after requesting ith resource can request jth resource if j > i. This type of allocation guarantees no cyclic dependencies among the transactions.

### Linear Order
![no cyclic](nocyclic.png)

- Pa: Holds resources at level i and request resource at level j which are held by Pb. j > i
- Pb: Holds resources at level j and request resource at level k which are held by Pc. k > j
- Pc: Holds resources at level k and request resource at level l which are held by Pd l > k
- Pd: Holds resources at level l and and is currently running.
- Pq: Holds resources at level g and request resource at level l which are held by Pd. l > g
- l > k > j > i and l > g.
  We cannot have loops. The dependency graph can be a tree or a linear chain and hence cannot have cycles.

### Deadlock – Avoidance / Mitigation
- Pre-declare all necessary resources and allocate in a single request, not practical as not possible to know about all requests.
- Periodically check the resource dependency graph for cycles. If a **cycle** exists - rollback (i.e., terminate) one or more transaction to eliminate cycles (deadlocks). The chosen transactions should be cheap (e.g., they have not consumed too many resources).
- Allow waiting for a maximum time **on a lock** then **force Rollback**. Many successful systems (IBM, Tandem) have chosen this approach.
- (Many distributed database systems maintain only local dependency graphs and use time outs for global deadlocks.)

## Isolation & Dependency / 隔离与依赖
### Isolation Concept
- Isolation defines which effects concurrent transactions may observe. Serializable isolation makes the committed result equivalent to some serial execution; weaker isolation levels may permit anomalies. Isolation preserves application invariants only when constraints are enforced or every transaction follows the required logic.
- We can achieve isolation by sequentially processing each transaction - generally not efficient and provides poor response times.
- We need to run transactions concurrently with the following goals
  - Concurrent execution should not cause application programs (transactions) to malfunction (fail).
  - Concurrent execution should not have lower throughput or bad response times than serial execution.

### Possible dependencies
![possible-dependencies](possibleDependency.png)

- Lost Update, Write-Write, T1 Write is covered by T2
- Dirty Read, Write-Read, T1 read in middle of write
- Unrepeatable Read, Read-Write, T1 reading while others writing
- OK, no dependency

### Dependency model
- $I_i$ : set of inputs (objects that are read) of a transaction $T_i$
- $O_i$ : set of outputs (objects that are modified) of a transaction $T_i$ Note $O_j$ and $I_j$ are not necessarily disjoint that is $O_j \cap I_j ≠ ∅$
- Given a set of transactions , Transaction $T_j$ has no dependency on any transaction $T_i$ in if -
  $$
  O_i\cap(I_j\cup O_j) = empty\ for\ all\ i ≠ j
  $$
- This approach cannot be planed ahead as in many situation inputs and outputs may be state dependant/not known in prior.

### Dependency Formal Definition
- Let **H** is a **history sequence** of tuples of the form (T, action, object). Here, T is transaction, action can be read/write, object is what the action operates on. e.g. (T1, Read, O1)
- For conflict-serializability, add an edge $T_i \to T_j$ when an operation of $T_i$ precedes and conflicts with an operation of $T_j$ on the same object: the transactions differ and at least one operation is a write. Read-read pairs do not conflict. The object may label the edge.
- A precedence graph is acyclic exactly when the history is conflict-equivalent to a serial history. This graph criterion is about conflict serializability, not every possible notion of serial equivalence ([Database System Concepts, 7e, ch. 18](https://www.db-book.com/Previous-editions/db7/slides-dir/PDF-dir/ch18.pdf)).

### Dependency Relations Example
H1 = <(T1,R,O1), (T2,W,O5), (T1,W,O3), (T3,W,O1), (T5,R,O3), (T3,W,O2), (T5,R,O4), (T4,R,O2), (T6,W,O4)>  
H2 = <(T1,R,O1), (T3,W,O1), (T3,W,O2), (T4,R,O2), (T1,W,O3), (T2,W,O5), (T5,R,O3), (T5,R,O4), (T6,W,O4)>

Give

- DEP(H1)
- DEP(H2)
- Dependency graph

For questions like this, first we focus on the object order: O1, O2.... We can notice that O1 is in T1 and T3, so we can write <T1, O1, T3> in the DEP(H1). Then we can see T3 and T4 both operate on O2, so we can write <T3, O2, T4>...

DEP(H1) = {<T1, O1,T3>, <T3,O2,T4>, <T1,O3,T5>, <T5,O4,T6> }  
DEP(H2) = {<T1, O1,T3>, <T3,O2,T4>, <T1,O3,T5>, <T5,O4,T6> }  
Dependency graph
![dependency graph](./dependencygraph.png)

### Isolated History
- A serial history is history that is resulted as a consequence of running transactions sequentially one by one.
- N transactions can result in a maximum of N! serial histories.
- A history is conflict-serializable if it is conflict-equivalent to a **serial history** (the conflicting operations have the same order).
- A history is legal if it respects the applicable lock-grant rules.
- In this course's dependency-graph terminology, the wormhole theorem characterizes the illustrated isolation condition. For the standard conflict-serializability test, use the acyclic-precedence-graph criterion above.

#### Isolated History – e.g.,
![dependency graph](./dependencygraph.png)
If T1 precedes T2, it is written as T1 << T2.

```
Before(T) = {T’ | T’ << T}
After(T) = {T’| T << T’}
```

E.g.

```
After(T1) = {T5,T6, T3, T4}
After(T3) = {T4}
After (T5) = {T6}
```

### Wormhole Transaction
A transaction T’ is called a **wormhole transaction** if

$$
T' \in Before(T) \cap After(T)
$$

That is T << T’ << T. This implies there is a **cycle** in the dependency graph of the history. Presence of a wormhole transaction implies it is not isolated (=> not a serial schedule).

Idea to solve wormhole problem:

1. Known history
2. Write DEP based on history
3. Draw Dependency graph based on DEP
4. See if there is a wormhole or not

#### 2022S1 Example
Given the following transaction history h we are told that k, l, m, n, o, and p are transactions, and operations are Read and Write operations which are labeled as R and W, and operations are done on the objects labeled as a, b, c, d, e:  
h = < (k,R,a),(m,W,a),(m,W,b),(n,R,b),(k,W,c),(l,W,e),(o,R,c),(o,R,d), (p,W,d) >  
Please find the DEP(h) and draw as a simple graph version as well. Then using the concept of wormholes explain whether this history is equal to a serial history or not, i.e., if this history is not equal to a serial history then give a wormhole example, and if it is then give a serial execution of these transactions that this history is equal to. Briefly explain your steps with sentences while answering this question.

Remind that the tuple is (Transaction, Action, Object), the DEP is <T1, O, T2>. The use of all characters is indeed confusing us.

Answer
![](./2022S1Q3.png)

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
![](./degree3.png)  
A Three degree isolated Transaction has no lost updates, and has repeatable reads.  
Lock protocol is **two phase and well formed**.  
It is sensitive to the following conflicts: write->write; write ->read; read->write

#### Degree 2
![](./degree2.png)  
Degree 2: A Two degree isolated transaction has no lost updates and no dirty reads.  
Lock protocol is two phase with **respect to exclusive locks** and well formed with respect to **Reads and writes**. (May have Non repeatable reads.)  
It is sensitive to the following conflicts: write- >write; write ->read;

#### Degree 1
![](./degree1.png)  
Degree 1: A One degree isolation has no lost updates.  
Lock protocol is two phase with **respect to exclusive locks** and well formed with respect to **writes**.  
It is sensitive the following conflicts: write- >write;

#### Degree 0
![](./degree0.png)  
Degree 0 : A Zero degree transaction does not overwrite another transactions dirty data if the other transaction is at least One degree.  
Lock protocol is well-formed with respect to writes. It ignores all conflicts.

## Granular Lock
- **Definition** - we need to build some **hierarchy**, then locks can be taken at any level, which will automatically grant the locks on its descendants.
- **Intention** - allow concurrent runs as much as possible for a better performance, while avoiding conflicts as much as possible
- **Steps**
  - Pick a set of column values (predicates).
  - They form a graph/tree structure.
  - Lock the nodes in this graph/tree
- Example  
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

### Optimistic Locking
- When conflicts are rare, transactions can execute operations without managing locks and without waiting for locks - higher throughput
- Use data without locks
- Before committing, each transaction rechecks its read-set and validates the values or versions used by the computation. A value comparison can miss an intervening update that changes a value and later restores it (ABA); version or write-sequence checks are needed when that history matters.
- If any conflict found, the transaction repeats the attempt
- If no conflict, make changes and commit

#### Example
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

On success, this path holds locks for the recheck and write, but lock duration and throughput depend on contention and work inside the critical section. Value equality does not prove that no intervening update occurred.  
Advantage: avoids holding locks during the initial computation when conflicts are rare  
Disadvantage: Repeat in Loop for long time

### Snapshot Isolation / 快照隔离
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

### Two phase locking Transaction - Snapshot Locking potential problem
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

### Time Stamping / 时间戳排序
This is one optimistic timestamp-validation model: at validation, a transaction may abort if a conflicting update is newer than the version it read. Basic timestamp-ordering protocols instead assign transaction timestamps and maintain read/write timestamps per item, checking operations against those timestamps. Do not treat this sentence as the general timestamp-ordering algorithm. Validation, commit durability, and version retention are separate concerns.

**Time Domain Versioning**  
In this time-domain versioning example, an update creates a new version with a validity interval rather than overwriting the earlier version. This temporal-data model is distinct from the basic timestamp-ordering protocol above.  
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
