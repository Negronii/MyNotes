# Database Performance and Reliability / 数据库性能与可靠性

核心概念：数据库性能由存储层级、数据访问、查询计划与资源配置共同决定；可靠性分析要区分固定时段故障概率、恒定故障率/MTTF和可修复系统的可用度。RAID 的容量、冗余和读写表现取决于布局、工作负载及修复假设。

The performance of a database system is evaluated based on:

1. **Efficiency (Speed)**
2. **Effectiveness**
3. **Security & Reliability**

## Efficiency
Efficiency of a database system is influenced by both hardware and software aspects:

- **Hardware**
  - Disks and I/O bandwidth
  - Main memory
  - Number of processors
  - Communication network
  - Type of architecture
- **Software/DB Tuning**
  - Types of DB
  - Indexing
  - Query optimisation

## Effectiveness
Effectiveness of a database system is determined by:

- Concurrent users: Users reading and writing over the same data
- Transactions: Required tasks are all done together

## Reliability
Reliability of a database system is ensured by:

- Crash recovery
  - Hardware:
    - Arrangement of multiple disks
    - Voting among multiple disks/modules
    - Disk block write
- Fault tolerance
- Data duplication

## Hard Disk & Memory Hierarchy
### Hard Disk Drive
![Physical Architecture](./physicalArchitecture.png)

A **hard disk drive (HDD)** is a crucial component of computing systems that provides data storage. Its structure comprises of several key elements:

- **Platter**: The entire circular disk.
- **Sector**: A device exposes sectors as addressable units; logical and physical sector sizes can differ.
- **Track**: A circular path on a platter. The red highlighted area in the image is one track.
- **Cylinder**: Tracks at the same radial position across platters. A file-system cluster is an allocation unit made of sectors, not a mechanical disk component.
- **Actuator Arm**: The component that moves the head to the required position.
- **Head**: This component is responsible for reading and writing data on the disk.

Note that the disk rotates at high speed, allowing the head to read and write data at different locations.

#### Disk Access Time in HDD
In this simplified model, estimate the transfer delay as:

$$
\text{Disk Access Time} = \text{Seek Time} + \text{Rotational Delay} + \frac{\text{Transfer Length}}{\text{Bandwidth}}
$$

Where:

- **Seek Time**: This is the time taken by the head to move from its current position to the desired track. Also known as seek latency.
- **Rotational Delay**: The time the disk takes to rotate and bring the desired sector under the head. This is also referred to as rotational latency.
- **Transfer Length**: This refers to the amount of data to be transferred. The units for this measure can vary, such as KB, MB, GB, etc.
- **Bandwidth**: This measures the amount of data that can be transferred within a given timeframe. Its unit is Storage/Time (e.g., 4MB/S).

#### Exercise
What is the disk access time for a 4 KB transfer when average seek time is 12 ms, rotational delay is 4 ms, and transfer rate is 4 MB/s?

Using decimal units (1 MB = 1000 KB), transfer time is 4 KB / 4000 KB/s = 0.001 s = 1 ms, so the estimate is 12 + 4 + 1 = 17 ms. This model omits controller and queueing delays and assumes the request is not already cached.

### Solid-State Drives (SSD)
Solid-state drives (SSDs) store data in flash memory and have no moving head or rotating platter. They avoid HDD seek and rotational delay, but still have controller, flash, queueing, and write-management latency. Read and write performance depends on the device, workload, and queue depth; overwrites are not universally slower. Flash pages are erased in larger blocks and the flash translation layer manages remapping and wear leveling ([Database System Concepts, 7e, ch. 12](https://www.db-book.com/Previous-editions/db7/slides-dir/PDF-dir/ch12.pdf)).

#### Disk Access Time in SSDs
A bandwidth-only estimate for a transfer is:

$$
\text{Disk Access Time} = \frac{\text{Transfer Length}}{\text{Bandwidth}}
$$

### Memory Hierarchy
![Memory Hierarchy](./Mem-hierarchy.png)

- Reg: Register
- CPU caches (L1/L2 and other levels) reduce the average cost of CPU memory access; they do not directly cache hard-disk blocks. Operating-system file caches, storage-device caches, and a DBMS buffer pool are separate layers with different units and behavior.
- Main Memory: If the system is shut down, data stored in the main memory (but not in the hard disk) will be lost. The unit of measurement for Main Memory is typically in GB.
- Hard Disk: The unit of measurement is usually in TB.
- Speed: Cache > Main Memory > Hard Disk
- Storage Capacity: Cache (in MB) < Main Memory (in GB) < Hard Disk (in TB)
- Simplified CPU path: check the CPU cache hierarchy, then access DRAM on a miss. A page fault or database storage request may involve an OS file cache, DBMS buffer pool, controller cache, and persistent storage; these are not one universal linear path.

#### Effective Memory Access Time
For a single cache level, if $M$ is the full cost of the miss path, including lookup, then:

$$
EA = H \times C + (1 - H) \times M
$$

where:

- $H$ is the hit ratio (the percentage probability of finding data in the cache)
- $C$ is the cache access time
- $M$ is the full miss-path cost. If $M$ means only lower-memory access time, use $EA = H C + (1-H)(C+M)$ instead.

The CPU-cache example concerns L1/L2 memory hierarchy. It is distinct from both a storage-device/controller cache and the DBMS buffer pool, which caches database pages in main memory. The latter is the buffer model used in query-cost calculations.

Why don't we have larger caches?

1. They are expensive.
2. If the processor and the cache are not on the same chip, the access time increases.

#### Effective Disk Buffer Access Time
A device or controller cache is different from the DBMS buffer pool in main memory. In this one-level model, BC is the hit-path cost and D is the full miss-path cost; the estimate excludes other caching levels and queueing:

$$
EA = HB \times BC + (1 - HB) \times D
$$

where:

- $HB$ is the hit ratio of the disk buffer
- $BC$ is the buffer access time
- $D$ is the disk access time

#### Example
e.g., Assume disk access time is S, buffer access time is C, hit ratio is H, and S = 1000C. What is the effective access time, EA, expressed as a multiple of C when H = 30%?

$EA = 30\% \times C + (1 - 30\%) \times S = 0.3C + 0.7 \times 1000C = 700.3C$

## Type of DB systems and DB Architectures
### Database Types
#### Simple File
- **Definition**: A data storage system where data is stored as a plain text file. Each line represents one record, with fields separated by delimiters (e.g., commas or tabs).
- **Tradeoffs**: A flat-file design can be sufficient for a small, single-process workload. Schema enforcement, indexes, transactions, and concurrent updates then need to be supplied by the application or another layer; speed and reliability depend on the implementation.

#### Relational Database Management Systems (RDBMS)
- **Definition**: A relational database represents data as relations (commonly shown as tables) and provides operations for querying and updating them. Primary and foreign keys are constraints that a schema may declare; tables need not all be joined by such constraints.
- **Tradeoffs**: A DBMS can provide query planning, indexes, transactions, and constraint enforcement, but performance and reliability depend on the engine, schema, workload, and configuration.

#### Object Oriented Database Systems (OODB)
- **Definition**: A data storage system where data is stored in the form of 'objects' directly, similar to Object Oriented Programming (OOP).
- **Strengths**: Reliable, well suited for applications requiring complex data.
- **Weaknesses**: Can be slow on some applications, limited application independent optimisation.
- **Use Cases**: Suitable for applications requiring complex data structures and methods.

#### NoSQL Databases - Key-value Storage
- **Definition**: Stores values addressed by keys. Key uniqueness, atomicity, transactions, and query features depend on the product.
- **Related idea**: MapReduce is a distributed data-processing model, and Hadoop is an ecosystem that includes MapReduce; neither is itself a definition of a key-value database.

#### Deductive Database Systems (DDBS)
- **Definition**: A database system that can make deductions based on rules and facts stored in the database.
- **Tradeoffs**: Rule languages can express derived relations and queries. Whether that model is useful depends on the application and implementation.
- **Use Cases**: Applications that require rule-based deductions.

### Database Architectures
These are broad course categories, not guarantees about performance, availability, consistency, or security. Those properties depend on the particular design and workload.

#### Centralized (Client-Server) Database Architecture
- **Description**:
  - The central server is with database in one location.
  - The client and server can be in different locations.
- **Advantages**:
  - Suitable for simple applications,
  - easy to manage,
  - simple system administration,
  - effective optimization process.
- **Disadvantages**: May not scale well, limited to one location.
- **Use Cases**: Suitable for applications that can be managed centrally, such as PC/Cluster Computing/data centres.

#### Distributed Database Architecture
- **Description**:
  - Data is distributed across several nodes in different locations.
  - Communicate with each other using network.
- **Advantages**:
  - Scalable, can handle large data sets, databases can be in different locations
  - provides concurrency, recovery, and transaction processing.
- **Tradeoffs**: Distribution can improve locality or capacity and can add network, coordination, replication, and recovery costs. Replication can create stale or conflicting views unless the chosen protocol prevents or resolves them.

#### World Wide Web (WWW) Database Architecture
- **Description**: In the WWW database architecture, data is stored in many locations with **several owners** of data.
- **Advantages**: Very convenient to access and share data, wide data availability.
- **Tradeoffs**: Independent ownership and network boundaries make authority, availability, consistency, and query planning depend on the participating services and protocols; there is no single universal WWW database architecture or guarantee.

#### Grid Database Architecture
- **Description**: In a grid database architecture, data and processing are shared among a group of computer systems which may be geographically separated.
- **Advantages**:
  - High processing capability,
  - access at different locations,
  - shared data and processing.
- **Tradeoffs**: Grid computing shares distributed compute and data resources under multiple administrative domains. Reliability and security depend on the participating systems; this model is not a claim that all grid deployments use a database architecture.

#### Peer-to-Peer (P2P) Database Architecture
- **Description**: Data and processing are shared among a group of computer systems which may be **geographically separated**. **Nodes can join and leave the network at will**. Administration is done by owner.
- **Advantages**: Suitable when the nodes of the network cannot be planned in advance, or some may leave and join frequently, shared data and processing, flexible network membership.
- **Tradeoffs**: Membership changes make coordination and replica management harder. A peer-to-peer design can serve workloads beyond file sharing; its guarantees depend on the protocol and trust model.

#### Cloud-Based Database Architecture
- **Description**: Cloud-based database architecture offers online computing, storage, and a range of new services for data and devices that are accessible through the Internet.
- **Advantages**:
  - Pay as you go, On-demand resources, cost-effective,
  - maintenance done externally by the cloud provider,
  - user pays for the services just like phone services, electricity, etc., huge potential for developing applications with minimal infrastructure costs.
- **Tradeoffs**: A provider may manage infrastructure and offer on-demand resources, while the customer still needs to evaluate access control, data location, availability, cost, and provider dependency. Cloud services differ in their contracts and behavior.

## Fault Tolerance Introduction
### Basic Probability and Mean Time to Event
Let $p_A$ and $p_B$ be independent probabilities that events occur during the same fixed observation interval. Then:

- $P(A \cap B) = p_A p_B$
- $P(A \cup B) = p_A + p_B - p_A p_B$

For small probabilities, $P(A \cup B) \approx p_A+p_B$. A probability over a fixed interval is not itself a time or a failure rate. If a component has a constant failure rate $\lambda$ per unit time (an exponential lifetime model), its MTTF is $1/\lambda$. For rare failures over an interval of length $\Delta t$, $p \approx \lambda \Delta t$.

For $n$ independent modules with the same per-interval failure probability $p$, the exact chance of at least one failure in that interval is $1-(1-p)^n$, approximately $np$ when $p$ is small. Under the constant-rate model, the rate of the first failure is $n\lambda$, so the time to the first failure has mean $1/(n\lambda)$.

### Module Availability
Module availability is the ratio of service accomplishment to elapsed time.
![Module Availability](./module-availability.png)
For a repairable module that alternates between up and down periods, long-run availability is:
$$\text{Availability} = \frac{MTTF}{MTTF + MTTR}$$
Here MTTF is the mean up-time and MTTR is the mean time spent repairing. This is a long-run average under the stated up/down model, not a probability of avoiding failure forever.

## Redundant Array of Independent Disks (RAID) / 独立磁盘冗余阵列
RAID is a method of combining multiple disks as a unit for fault tolerance or performance improvement, or both, of a database system ([Patterson, Gibson, and Katz's 1988 paper](https://www.cs.cmu.edu/~garth/RAIDpaper/Patterson88.pdf); [Database System Concepts, 7e, ch. 12](https://www.db-book.com/Previous-editions/db7/slides-dir/PDF-dir/ch12.pdf)).

For graphs below, we use the following conventions:

- We use b for Bit; B for byte; 8 continuous bits = 1 byte
- A for block, 4000/8000 continuous bytes = 1 block
- p for parity, Parity (or check bits) are used for error detection
  - P0 is parity for bytes B0 and B1, $P_i = B_{2i} \oplus B_{2i+1}$, here $\oplus$ is the exclusive-or operator

Please note that the RAID levels are not exhaustive and there are other RAID levels such as RAID 10, RAID 50, etc. that combine the features of the basic RAID levels for additional redundancy or performance.

Reliability model for the calculations below: let $p$ be the probability that one disk fails within one fixed observation interval, and assume independent disk failures. If a disk has constant failure rate $\lambda$ per hour, then $MTTF_{disk}=1/\lambda$; $1/p$ is not a time unless the interval and rate model are specified. For $N$ disks, the probability of at least $k$ failures during an interval with no repair is
$$P(\text{at least }k)=\sum_{j=k}^{N}\binom{N}{j}p^j(1-p)^{N-j}.$$
These mission-interval probabilities are not MTTF estimates for a repaired array.

### RAID 0 (Block Level Striping)
<image alt="RAID0" src="raid0.png" width=300/>

- Data is split into blocks and spread across multiple disks.
- Note the data is stored in a zig-zag way (A0, A2, A4, A6 in Disk 1, A1, A3, A5, A7 in Disk 2)
- Advantages: Independent block requests can run in parallel; a large sequential transfer may use both disks.
- Drawbacks: There is no redundancy, so either disk failing loses the array. With two independent disks and failure probability $p$ per fixed interval, $P(\text{loss})=1-(1-p)^2=2p-p^2\approx2p$. With constant per-disk failure rate $\lambda$ and no repair, array MTTF is $1/(2\lambda)=MTTF_{disk}/2$. Throughput gains depend on workload and bottlenecks.

### RAID 1 (Mirroring)
<image alt="RAID1" src="raid1.png" width=300/>

- Data is duplicated across two or more disks.
- Advantages: Two copies can serve reads, and data remains available after one independent disk failure if the surviving copy is sound.
- Drawbacks: Usable capacity is about half for a two-disk mirror. Both disks must receive writes, so write performance depends on workload and implementation.
- In a no-repair observation interval, both disks failing has probability $p^2$. In a repairable two-disk mirror with independent constant failure rate $\lambda$, rare failures, and mean repair/rebuild time $r$, the approximate mean time to data loss is $1/(2\lambda^2r)=MTTF_{disk}^2/(2r)$. This assumes independent failures and ignores common causes; it is not $MTTF_{disk}^2$ ([Database System Concepts, 7e, ch. 12](https://www.db-book.com/Previous-editions/db7/slides-dir/PDF-dir/ch12.pdf)).

### RAID 2 (Bit Level Striping)
<image alt="RAID2" src="raid2.png" width=300/>

- Data is striped at bit level and protected by a memory-style error-correcting code (ECC); the redundancy disks are not shown in the preserved data-only sketch.
- Protection and failure tolerance depend on the code and array layout. RAID 2 is largely of historical/teaching interest; it is not equivalent to nonredundant RAID 0.

### RAID 3 (Byte Level Striping)
<image alt="RAID3" src="raid3.png" width=300/>

- As drawn, consecutive data units are striped across two data drives with a dedicated parity drive; RAID 3 uses fine-grained (commonly byte-level or bit-interleaved) striping. One failed drive can be reconstructed; two simultaneous failures exceed this layout's single parity.
- In a no-repair observation interval, loss probability is $\binom{3}{2}p^2(1-p)+p^3=3p^2-2p^3\approx3p^2$. For a repairable array under the same independent constant-rate assumptions, the rare-event approximation is $MTTDL\approx1/(6\lambda^2r)=MTTF_{disk}^2/(6r)$, where $r$ is the time to restore redundancy. This is a model, not a field guarantee.

### RAID 4 (Block Level Striping)
<image alt="RAID4" src="raid4.png" width=300/>

- Data is split into blocks and spread across multiple disks, with a dedicated disk for parity blocks.
- Block striping with one dedicated parity disk can serve independent reads in parallel and reconstruct one failed disk.
- Small random writes update parity and can make the dedicated parity disk a bottleneck; large sequential writes behave differently. There is no generic throughput or MTTF value independent of the workload and repair model.

### RAID 5 (Block Level Striping with Parity Striping)
<image alt="RAID5" src="raid5.png" width=300/>

- Data and parity blocks are distributed across the drives, avoiding RAID 4's single dedicated parity drive. One failed drive can be reconstructed from the remaining data and parity.
- A single-parity array loses data after two unrecoverable drive failures before redundancy is restored. Small random writes still incur parity work; the relative performance of RAID 4 and RAID 5 depends on workload and implementation.
- Drawbacks: Complex to implement and manage.

### RAID 6 (Block Level Striping with Double Parity)
<image alt="RAID6" src="raid6.png" width=500/>

- This five-drive illustration has three data drives and two independent parity streams (P and Q). The second parity lets this layout reconstruct up to two failed drives; writes must maintain both parity values.
- With independent per-drive failure probability $p$ in one fixed interval and no repair, loss requires at least three failed drives:
$$P(\text{loss})=\binom{5}{3}p^3(1-p)^2+\binom{5}{4}p^4(1-p)+p^5=10p^3-15p^4+6p^5\approx10p^3.$$
This is an interval probability, not an MTTF. Repaired-array MTTDL also depends on repair/rebuild time, correlated failures, and latent errors.

### Choosing RAID Level
The tradeoff depends on layout and workload: striping can improve parallel reads or writes, while RAID 0 has no redundancy; mirroring and parity consume capacity and add write work to tolerate specified failures. Compare usable capacity, tolerated failures, rebuild exposure, workload, and system support.
When choosing the suitable RAID level, the following factors should be considered:

- **Reliability**: The ability of the system to handle and recover from hardware failure.
- **Performance**: The speed at which data can be read from or written to the disk.
- **Storage Utilization**: The amount of storage space that is effectively used.
- **Price/Number of Disks**: The cost and the number of disks required.

## Fault Tolerance by Voting / 多数表决容错
### Definition of majority here
if n nodes, then:

- if n is odd, majority means $\frac{(n + 1)}{2}$
- if n is even, majority means $\frac{n}{2} + 1$

### Failvote
In the fail-vote/fail-fast model described by [Saltzer and Kaashoek, ch. 8](https://live.ocw.mit.edu/courses/res-6-004-principles-of-computer-system-design-an-introduction-spring-2009/6b31587ec59b1b002cb7a710d9781453_faults_open_5_0.pdf), a failvote voter accepts an output only when a strict majority of all configured replicas agrees. For three replicas, two matching outputs suffice; for four, three are required. A replica being powered on does not prove that its output is correct.

### Failfast
A self-checking fail-fast replica model can continue with one surviving replica after failed replicas are detected. An ordinary untrusted survivor cannot validate its answer by comparison with another result, so this is a model prerequisite rather than a guarantee for every fail-fast design. Detection errors and common-mode failures remain outside this simple model.

### Supermodule
A supermodule combines modules with a voter or comparator. Its failure condition depends on the design: a design that remains usable with one self-checking module fails only when all modules are unavailable; failvote has a stricter output-agreement threshold. Do not use the all-modules-down formula below for a failvote system.

#### Fault Tolerance with Repair
Assume independent module failures with a constant rate, immediate detection, and repair time with mean MTTR. In a two-state up/down model, one module's long-run unavailability is
$$q = \frac{MTTR}{MTTF + MTTR} \approx \frac{MTTR}{MTTF}$$
when MTTR is much smaller than MTTF. Values such as MTTR of a few hours to one day and MTTF of 750,000 hours (about 85.6 years) are illustrative inputs for this model, not a general current disk specification.

#### Approximate Failure Rate of a One-Available-Module Supermodule
For a supermodule that can operate with any one self-checking module available, the approximate rate of total failure is
$$\lambda_{sys} \approx n\lambda q^{n-1}, \qquad \lambda=1/MTTF,$$
when failures are rare, independent, and repaired independently. This follows because any of the n modules can fail while the other n-1 are unavailable. The result has units of failures per time; its reciprocal is an approximate MTTDL. It excludes common-cause failures, repair queues, latent errors, and voter failures. Failvote/failfast systems with a different voting threshold need a different failure-state calculation.

## Communication Reliability / 通信可靠性
In a reliable message passing system, the communication between two nodes can be represented as a series of states. The key components of this system include:

- **Out**: Number of messages sent
- **In**: Number of messages received
- **Ack**: Number of acknowledgements

For example, the communication between Node A and Node B can be represented as follows:
<image alt="State 0: Node A (In:6, Ack:3, Out:3), Node B (Out:6, Ack:6, In:3)" src="com_01.png" width=600/>
<image alt="State 1: Node B sends message 7, Node A (In:6, Ack:3, Out:3), Node B (Out:7, Ack:6, In:3)" src="com_02.png" width=600/>
<image alt="State 2: Node A sends acknowledge 7, Node A (In:7, Ack:3, Out:3), Node B (Out:7, Ack:6, In:3)" src="com_03.png" width=600/>
<image alt="State 3: Node B receives acknowledge 7, Node A (In:7, Ack:3, Out:3), Node B (Out:7, Ack:7, In:3)" src="com_04.png" width=600/>
If B does not receive the acknowledgement, it may retry message 7. Retries can deliver the same message more than once; acknowledgements alone do not guarantee exactly-once effects. Applications that need deduplication use message identifiers or sequence numbers and durable receiver-side state.

If two nodes want to communicate with each other, how to make sure the data sent is correctly?

- Stable storage – data in stable storage is durable and not be lost easily
- Acknowledgement info

## Duplex Write & Logged Write / 双写与日志写入
### Atomicity
Atomicity means a transaction's changes are committed as a unit or rolled back as a unit. A redundant disk write is a storage technique, not by itself transaction atomicity. For a transfer of $100, the debit, credit, and recovery record must be coordinated so recovery cannot expose only one side.

### Atomic Disk Write – Duplex Write
- A duplex-write scheme keeps redundant copies, often with version or sequence metadata, and may consult a log during recovery.
- A checksum such as CRC can detect many accidental corruptions, but it does not correct data or prove that a copy is the latest valid one.
- Two sequential writes are not an atomic transaction and do not guarantee that one good copy always exists: a crash, torn write, shared failure, or undetected corruption can affect both copies. The recovery protocol and its failure assumptions determine what can be recovered.

### Example
State 0: Main Memory (empty), Hard Disk (100 700 (v#7) Block 123)
![](./update_disk_block_00.png)
State 1: Operation: read, Main Memory (100 700), Hard Disk (100 700 (v#7) Block 123)
![](update_disk_block_01.png)
![](update_disk_block_02.png)
State 2: Operation: Modify contents in memory to say 200, contents modified to 200 in memory, update changes to disk, Main Memory (200 700), Hard Disk (100 700 (v#7) Block 123)
![](update_disk_block_03.png)
![](update_disk_block_04.png)
State 3: Operation: Write to disk in a different block, Written to a different block, Next update will take place to Block 123 and the version number V#7 will be changed to v#9. (Two different physical disks can be used for duplex writes as well), Main Memory (200 700), Hard Disk (100 700 (v#7) Block 123; 200 700 (v#8) Block 475)
![](update_disk_block_05.png)

### Logged write
- similar to duplex write, except one of the writes goes to a log.
- Log – durable & can be read quickly
- If the log stores a compact change record, logging a small update may avoid rewriting a full block. Durability and replay still depend on the log protocol.

## CRC Calculation / 循环冗余校验
To compute an n-bit binary CRC, follow these steps:

1. **Padding**: Add n zero bits to the right of the input bits. For example, a 3-bit CRC with polynomial $x^3 + x + 1$ appends 000 before division.
2. **Compute Polynomial**: Compute the (n + 1)-bit pattern representing the CRC's divisor (called a "polynomial"). For example, a 3-bit CRC with a polynomial $x^3 + x + 1$ would have the coefficients 1, 0, 1, and 1. i.e. $1 \times x^3 + 0 \times x^2 + 1 \times x^1 + 1 \times x^0$

3. **Position Polynomial**: Position the (n + 1)-bit pattern representing the CRC's divisor underneath the left-hand end of the input bits.

4. **Perform XOR Operations**: Starting at the leftmost bit, XOR the divisor with the current message window when its leading bit is 1; otherwise shift to the next position. Continue polynomial long division over GF(2) across the padded message. The final n-bit remainder is the CRC. A CRC detects many transmission or storage errors but does not repair data or authenticate its source; detection strength depends on the chosen polynomial and error pattern.

Example:

![CRC calculation](CRC_calculation.png)
