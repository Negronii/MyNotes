# Backend Concepts / 后端概念

核心要点：判断死锁要找真实资源等待环，普通异步 I/O 等待本身不是死锁；HashMap 的公开契约与 OpenJDK 17 的负载因子、树化阈值等实现细节必须分开看，不能推广为所有 map 的保证。

## Deadlocks / 死锁

A deadlock is a state in which a set of processes or threads cannot proceed because each waits for a resource held by another member of the set. In the classic resource-allocation model, the four conditions are **mutual exclusion**, **hold and wait**, **no preemption**, and **circular wait**. For that model, breaking any one condition prevents deadlock; the conditions are not a checklist that makes every slow or waiting operation a deadlock.

Example: thread A locks resource `R1` and then waits for `R2`; thread B holds `R2` and waits for `R1`. Neither can release its first lock while blocked on the second. A consistent global lock order, shorter lock scopes, or avoiding nested locks can remove this cycle, depending on the design.

An asynchronous request waiting for I/O is not by itself a deadlock. JavaScript's event loop does not hold exclusive DOM access while a `fetch` is pending, and a Promise is a representation of eventual completion rather than a lock. An application can still stall because of a dependency cycle, an unresolved Promise, or exhausted resources; identify the actual dependency/resource graph before calling it a deadlock. For the corresponding operating-system view of process and thread waits, see [Processes, threads, and concurrency](../../engineering-foundations/operating-systems/processes-threads-and-concurrency.md).

## Java `HashMap` / Java `HashMap`

The following implementation details are scoped to **OpenJDK 17's `java.util.HashMap`**, not the `Map` interface or every hash-table implementation. The Java SE 17 API documents the default initial capacity of 16 and load factor of 0.75. When size exceeds `capacity × loadFactor`, this implementation grows and rebuilds its table; the API describes roughly doubling the bucket count. A lower load factor trades more space for fewer collisions, while a higher one trades space for more lookup work.

OpenJDK 17 spreads a key's hash bits before selecting a bucket. Colliding entries share a bucket, usually as a linked chain; heavily populated bins can be represented as red-black trees to improve lookup under suitable conditions. In this source version, `TREEIFY_THRESHOLD` is 8 and `MIN_TREEIFY_CAPACITY` is 64: when a bin reaches the treeification path, a table smaller than 64 is resized instead. These are implementation thresholds, not API guarantees; do not infer a fixed transition from bucket size alone.

`HashMap` relies on keys' `hashCode()` and `equals()` implementations being consistent, permits one `null` key and `null` values, and does not guarantee iteration order. It is unsynchronized; concurrent structural modification requires external synchronization or a suitable concurrent collection. Its basic `get`/`put` operations have expected constant-time performance only when hashes disperse keys adequately.

## Sources / 参考资料

- Coffman, Elphick, and Shoshani (1971), [System Deadlocks](https://doi.org/10.1145/356586.356588), for the classic resource-allocation conditions.
- [Java SE 17 `HashMap` API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/HashMap.html) for the public contract and documented defaults; [OpenJDK 17 `HashMap` source](https://github.com/openjdk/jdk17u/blob/master/src/java.base/share/classes/java/util/HashMap.java) for implementation thresholds and mechanics.
