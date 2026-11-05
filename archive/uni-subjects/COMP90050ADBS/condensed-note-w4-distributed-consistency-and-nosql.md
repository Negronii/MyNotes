# What do CAP, consistency models, and PACELC say about distributed services? / CAP、一致性模型与 PACELC 如何描述分布式服务？

CAP states a conditional limit during a network partition between linearizable consistency and a response to every request at a non-failing node. Consistency contracts vary, and PACELC adds the latency/consistency choice outside partitions. BASE and NoSQL are design terms and families, not universal product guarantees. / CAP 描述网络分区期间线性一致性与每个非故障节点响应请求之间的条件限制。一致性契约有不同强度，PACELC 还描述无分区时的延迟/一致性取舍。BASE 与 NoSQL 是设计术语和类别，不是统一产品保证。

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
