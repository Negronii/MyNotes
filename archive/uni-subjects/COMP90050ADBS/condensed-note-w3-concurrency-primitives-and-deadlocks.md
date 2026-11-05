# How do synchronization primitives coordinate access and avoid deadlock? / 同步原语如何协调访问并避免死锁？

Mutual exclusion may use atomic busy-wait protocols or blocking primitives, which have different assumptions and costs. Deadlock requires a real wait cycle; a consistent resource order prevents cycles in the stated resource-order model. / 互斥可使用原子忙等协议或阻塞原语，两者的前提与成本不同。死锁要求真实等待环；在给定资源排序模型下，一致的资源顺序可以阻止循环等待。

## Concurrency Control / 并发控制
For correct execution, we need to impose exclusive access to the shared variable counter by Tasks.

- To resolve conflicts
- To preserve database consistency

### Different ways for concurrency control
- **Peterson's algorithm (two-process pseudocode)** demonstrates mutual exclusion under atomic, sequentially consistent shared-register assumptions; it busy-waits and is not a multi-process solution.
- **OS-supported blocking primitives**, such as mutexes and semaphores, can park waiters instead of busy-waiting; implementations may use a user-space atomic fast path and involve the kernel only when needed ([Linux futex manual](https://man7.org/linux/man-pages/man2/futex.2.html)).
- **Spin locks** use atomic operations to busy-wait; they can suit short waits in an appropriate environment but consume CPU while contended.

### Peterson's algorithm (two processes)
This is Peterson's two-process algorithm, not Dekker's: each process raises its flag, gives the other process priority, and waits while the other flag is raised and it is the other process's turn. The pseudocode assumes atomic, sequentially consistent shared-register reads and writes; ordinary shared C `int` variables do not by themselves provide those concurrent-memory guarantees ([Peterson's mutual-exclusion algorithm](https://www.cs.yale.edu/homes/aspnes/pinewiki/MutualExclusion.html)). Repeat each process's entry, critical-section, exit, and remainder sequence as needed.

```text
Shared state, initialized before either process runs:
    flag[1] = 0
    flag[2] = 0
    turn = 1

Process 1:
    flag[1] = 1
    turn = 2
    while flag[2] == 1 and turn == 2:
        wait
    # critical section
    counter = counter + 1
    flag[1] = 0
    # remainder section

Process 2:
    flag[2] = 1
    turn = 1
    while flag[1] == 1 and turn == 1:
        wait
    # critical section
    counter = counter + 1
    flag[2] = 0
    # remainder section
```

- The protocol uses busy waiting. Its performance depends on the workload and platform; this teaching pseudocode is not a substitute for language or operating-system synchronization primitives in application code.

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
