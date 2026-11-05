# What does OpenJDK 17 HashMap guarantee, and what is implementation detail? / OpenJDK 17 HashMap 的契约与实现细节分别是什么？

The Java SE 17 API defines the public `HashMap` contract and documents defaults; treeification thresholds and bucket mechanics below are specific to OpenJDK 17 source. Do not generalize them to the `Map` interface or every hash table. / Java SE 17 API 定义 `HashMap` 的公开契约并记录默认值；以下树化阈值和桶机制属于 OpenJDK 17 源码细节，不应推广到 `Map` 接口或所有哈希表。

## Java `HashMap` / Java `HashMap`

The following implementation details are scoped to **OpenJDK 17's `java.util.HashMap`**, not the `Map` interface or every hash-table implementation. The Java SE 17 API documents the default initial capacity of 16 and load factor of 0.75. When size exceeds `capacity × loadFactor`, this implementation grows and rebuilds its table; the API describes roughly doubling the bucket count. A lower load factor trades more space for fewer collisions, while a higher one trades space for more lookup work.

OpenJDK 17 spreads a key's hash bits before selecting a bucket. Colliding entries share a bucket, usually as a linked chain; heavily populated bins can be represented as red-black trees to improve lookup under suitable conditions. In this source version, `TREEIFY_THRESHOLD` is 8 and `MIN_TREEIFY_CAPACITY` is 64: when a bin reaches the treeification path, a table smaller than 64 is resized instead. These are implementation thresholds, not API guarantees; do not infer a fixed transition from bucket size alone.

`HashMap` relies on keys' `hashCode()` and `equals()` implementations being consistent, permits one `null` key and `null` values, and does not guarantee iteration order. It is unsynchronized; concurrent structural modification requires external synchronization or a suitable concurrent collection. Its basic `get`/`put` operations have expected constant-time performance only when hashes disperse keys adequately.

## Sources / 参考资料

- [Java SE 17 `HashMap` API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/HashMap.html) for the public contract and documented defaults; [OpenJDK 17 `HashMap` source](https://github.com/openjdk/jdk17u/blob/master/src/java.base/share/classes/java/util/HashMap.java) for implementation thresholds and mechanics.
