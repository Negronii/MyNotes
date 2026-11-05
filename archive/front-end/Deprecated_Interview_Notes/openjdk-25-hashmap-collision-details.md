# Which collision-tree thresholds does OpenJDK 25 HashMap use? / OpenJDK 25 的 HashMap 如何处理冲突树化阈值？

Hash-table performance depends on hash distribution, resizing, and the equality/hash contract. In OpenJDK 25 specifically, HashMap spreads a key hash with h ^ (h >>> 16) before indexing buckets; its source defines a treeification threshold of 8 and a minimum capacity of 64. These are implementation details for this JDK version, not Java Map interface guarantees. / 哈希表性能取决于哈希分布、扩容及相等/哈希契约。仅就 OpenJDK 25 而言，HashMap 在定位桶之前使用 h ^ (h >>> 16) 扩散哈希；源码定义树化阈值为 8、最小容量为 64。这些是该 JDK 版本的实现细节，不是 Java Map 接口保证。

In the ordinary putVal path, the bin-count check runs when a new node is appended. When the table is below the minimum capacity, the treeification helper resizes instead; a bin length of eight alone does not guarantee immediate treeification. The default load factor is 0.75, and the implementation resizes when its threshold is exceeded.

When implementing a hash map, preserve the invariant that equal keys have equal hash codes and expect collisions. For Java API behavior, use the Javadoc; inspect source only when an implementation detail matters.

**Versioned sources checked 2026-10-15:** [Java SE 25 HashMap Javadoc](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/HashMap.html) and [OpenJDK 25 HashMap source](https://github.com/openjdk/jdk/blob/jdk-25%2B36/src/java.base/share/classes/java/util/HashMap.java).
