# Advanced Database Systems
## Database Management System (DBMS)

A Database Management System (DBMS) is a software system designed to store, manage, and facilitate access to databases. The complexity of managing a database system has increased due to:

- More data
- More aspects of businesses
- Data stored in various sites and accessed by many users
- More complex data types such as images, social networks, videos, etc.

## Database System Objectives

A database system should provide:

- Ability to retrieve and process the data effectively and efficiently
- Secure and reliable storage of data

## Database Performance Metrics

The performance of a database system is evaluated based on:

1. **Efficiency (Speed)**
2. **Effectiveness**
3. **Security & Reliability**

### Efficiency

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

### Effectiveness

Effectiveness of a database system is determined by:

- Concurrent users: Users reading and writing over the same data
- Transactions: Required tasks are all done together

### Reliability

Reliability of a database system is ensured by:

- Crash recovery
  - Hardware:
    - Arrangement of multiple disks
    - Voting among multiple disks/modules
    - Disk block write
- Fault tolerance
- Data duplication

## Basic Hardware of a Classical Disk

A classical disk operates by rapidly rotating with a magnetic head, which reads and writes data to the platter surfaces. The disk structure includes:

- Tracks: circular path on disk surface
- Tracks are subdivided into disk sectors

## Disk Access Time

Disk access time is a crucial factor in database management systems, as it determines the duration required to read data from or write data to a disk. It is computed as the sum of the seek time, rotational delay, and the time taken to transfer the data. The formula for calculating disk access time is:

$$
\text{Disk Access Time} = \text{Seek Time} + \text{Rotational Delay} + \frac{\text{Transfer Length}}{\text{Bandwidth}}
$$

The seek time delay, or seek latency, is the time taken for the head of the actuator arm to move from its current position to the required track. This delay is a physical property of a **Hard Disk Drive (HDD)** only.

The rotational delay, or rotational latency, is the waiting time for the disk's rotation to bring the required sector of a track to the head of the actuator arm. This delay is also a physical property of an **HDD** only.

## Solid-State Drives (SSD)

Solid-State Drives (SSDs) are a type of storage device that do not have any moving parts, hence the term "solid-state". They store data in grids of cells, where each grid is referred to as a block and each row in a grid is called a page. 

The lack of moving parts in SSDs leads to several advantages over HDDs:

- **No seek/rotational latency**
- No start-up times
- Silent operation
- Faster random access times

However, SSDs also have their drawbacks. They are relatively more expensive and have certain read/write limitations. For instance, SSDs tend to be slower when overwriting

data.

## Disk Access Time in SSDs

Since SSDs do not have any moving parts, they do not experience seek or rotational delays. Therefore, the disk access time in SSDs is simplified to:

$$
\text{Disk Access Time} = \frac{\text{Transfer Length}}{\text{Bandwidth}}
$$

This results in SSDs being faster than HDDs for the same amount of data transfer, given that the base sequential data transfer rates are the same for the two drives. 

## Data Drives in Computers

Data drives, whether HDDs or SSDs, fit into computers as the primary storage devices. After data is read from these drives, it is passed to the processors. However, the access times for HDDs and SSDs can be high, especially when reading large amounts of data. For example, for a simple task with 1 Million bit reading from the memory, the processing time will be almost 117 minutes for HDD and almost 1 minute for SSD.

## Improving Performance

To improve the performance of data drives, we can consider several strategies. One is to improve the access time for the memory, which would require new technological design. However, SSDs are already at the limits of fast memory, and faster memories would be very expensive.

Another strategy is to change the structure of the memory. Not all the data in memory is always required, so we can design a new fast and small memory called Cache. We can then read from Cache instead of the main memory, which can significantly reduce access time. The access time for a hierarchical structure with one cache is calculated as:

$$
\text{access time} = \text{access cache} * \text{hit ratio} + \text{access mem} * (1 - \text{hit ratio})
$$

This approach balances the need for speed and cost, providing a more efficient way to access data.

### Example 

In a hard disk drive (HDD), the average seek time is 12 ms, rotation delay is 4 ms, and transfer rate is 4MB/sec. For simplicity we assume 1MB equals to 1000KB.

1. What physical property of an HDD causes the seek time delay?
   - The seek time delay/seek latency is the period that the head of the actuator arm moves from a position to a required track.
2. What physical property of an HDD causes the rotation delay?
   -  The rotation delay/rotation latency is the waiting period that the rotation of the disk brings the required sector of a track to head of the actuator arm.
3. What will be the disk access time for a transfer size of 8MB? What will be the disk access time for a transfer size of 8KB?
    - Disk access time for 8MB = $12 + 4 + \frac{8}{4}\times1000ms = 2016ms$
    - Disk access time for 8KB = $12 + 4 + \frac{8}{4 \times 1000}\times1000ms = 18ms$
    - A comparison of the two cases highlights that sequentially reading large data pays off as seek time is buried under a lot of transfer time. For example, in the first case, seek time is only 0.6% of the total time while nearly all the time is spent on transferring data. In the second case, seek time is 66.7% of the total time while only a small fraction of the time is spent on data transfer.
4. In a solid state drive, what will be the disk access time for a transfer size of 8MB when transfer rate 4MB/sec? Is an SSD faster than an HDD for the same amount of

data transfer (Assuming the base sequential data transfer rates are the same for the given two drives.)? Why?
   - Unlike an HDD, an SSD do not have any rotating part. Hence there is no rotation delay or seek delay in an SSD. Therefore, for the same transfer rate and same amount of data transfer, an SSD is always faster than an HDD. Moreover, the data transfer rate of SSDs is usually higher than that of HDDs in general as well.
   - Disk access time of SSD = $\frac{Transfer Length}{Bandwidth} = \frac{8}{4} = 2sec$

## Memory Hierarchy and Effective Memory Access Time

The memory hierarchy in a computer system describes the relationship between different types of memory, including the processor, registers, L1 and L2 cache, main memory, and hard disk. As we move from on-chip to off-chip memory, the access speed drops significantly.

The effective memory access time (EA) is a crucial metric in this context and can be calculated using the following formula:

$$
EA = H \times C + (1 - H) \times M
$$

where:
- \(H\) is the hit ratio (the ratio of references satisfied by cache to total references)
- \(C\) is the cache access time
- \(M\) is the memory access time

This concept also applies to the disk buffer or disk cache, which is embedded in the disk and differs from the cache in the memory hierarchy. The effective disk buffer access time can be calculated using a similar formula:

$$
EA = HB \times BC + (1 - HB) \times D
$$

where:
- \(HB\) is the hit ratio of the disk buffer
- \(BC\) is the buffer access time
- \(D\) is the disk access time

### Example

Consider two machines: Machine A has a smaller cache with a 50% cache hit ratio, and Machine B has a larger cache with a 90% cache hit ratio. However, the memory access time of Machine A is 100C, and that of Machine B is 400C, where \(C\) is the cache access time. Despite Machine A having faster memory access, Machine B has a faster overall effective memory access time due to its larger cache and higher cache hit ratio.

- Effective memory access time of A: \(0.5 \times C + (1 - 0.5) \times 100C = 50.5C\)
- Effective memory access time of B: \(0.9 \times C + (1 - 0.9) \times 400C = 40.9C\)

## Database Types

### Simple File

Data is stored as a plain text file, with each line holding one record and fields separated by delimiters. This format is fast for simple applications but can be slow for complex ones. It's less reliable, hard to maintain, and requires additional code development for features that exist in relational databases. It's suitable for simple applications where speed is a priority.

### Relational Database Systems (RDBS)

Data is stored as a collection of tables (relations) consisting of rows and columns. Tables in a database are related using primary/foreign key relationships. RDBS is very reliable, application-independent, and well-suited to many applications. It can be slow for some simple applications but is ideal for applications requiring high reliability and speed.

### Object Oriented Database Systems (OODB)

Data is stored in the form of 'objects' directly, similar to Object Oriented Programming (OOP). OODB is reliable and well-suited for applications requiring complex data. It can be slow on some applications and has limited application-independent optimization.

### NoSQL Databases

#### Key-value Storage

A key-value database stores data as a collection of key-value pairs where a key serves as a unique identifier. All access to the database is done via the key. Both keys and values can be complex. This type of database is flexible, has a simple design, and should linearly scale. It's suitable for datasets that do not need complex relational table structures but can be expressed with simple key-value pairs.

#### Document Storage

This type of database is flexible for storing different kinds of documents, where they may not all have the same sections. XML, JSON,

etc. are subclasses of document-oriented databases. It's well-suited for cases where different kinds of documents do not always have the same structure/sections.

#### Graph Storage

Graphs capture connectivity between entities. A graph is a structure amounting to a set of objects (vertices) where some pairs of the objects are connected/related in some sense. A connection is called an edge. The links can be material or immaterial. It's well-suited for connection data such as social network connections and spatial data.

### Deductive Database Systems (DDBS)

A DDBS can make deductions based on rules and facts stored in the database. Most of the application can be developed entirely using DDBS. However, many applications do not require the expressive power of these systems.

## Database Architectures

### Centralized (Client-Server) Database Architecture

A centralized database architecture involves a central server with a central database in one location. The client and server can be in different locations. This architecture is suitable for simple applications, easy to manage, and has simple system administration. However, it may not scale well and is limited to one location.

### Distributed Database Architecture

In a distributed database architecture, data is distributed across several nodes in different locations. This architecture is scalable, suitable for large applications, can handle large data sets, and provides concurrency, recovery, and transaction processing. However, system administration and crash recovery are difficult, and potential inconsistency may occur due to data replication.

### World Wide Web (WWW) Database Architecture

In the WWW database architecture, data is stored in many locations with several owners of data. This architecture is very convenient to access and share data, and it offers wide data availability. However, it has security issues, no guarantee on availability or consistency, ineffective optimization process, and extreme levels of administration issues.

### Grid Database Architecture

In a grid database architecture, data and processing are shared among a group of computer systems which may be geographically separated. This architecture offers high processing capability, access at different locations, and shared data and processing. However, it has similar issues to distributed databases, is less used nowadays, and reliability and security are not well developed or studied.

### Peer-to-Peer (P2P) Database Architecture

In a P2P database architecture, data and processing are shared among a group of computer systems which may be geographically separated. Nodes can join and leave the network at will. This architecture is suitable when the nodes of the network cannot be planned in advance, or some may leave and join frequently. However, it's difficult to design transaction models due to flexible network membership, and applications are usually limited to simple file sharing.

### Cloud-Based Database Architecture

Cloud-based database architecture offers online computing, storage, and a range of new services for data and devices that are accessible through the Internet. This architecture offers on-demand resources, is cost-effective, and maintenance is done externally by the cloud provider. However, it has some privacy and confidentiality issues, and there is a dependence on internet connectivity. It's suitable for applications that require on-demand resources and services, and can benefit from the pay-as-you-go model.

**Note**: I have not made any corrections to your notes as the information provided was accurate. I have only reorganized and reformatted the content as per your requirements.

## Fault Tolerance

Fault tolerance refers to the ability of a system to continue operating correctly even when some of its components fail.

## Basic Probability and Mean Time to Event

The probability of an event and the mean time to an event are fundamental concepts in understanding system reliability. Here are some key formulas:

- Probability of an event A happening in a certain period: $P(A)$
- Probability of both events A and B happening in that period (assuming A and B are independent events): $P(A \text{ and } B) = P(A) \times P(B)$
- Probability of either event A or B happening in that period: $P(A \text{ or } B) = P(A) + P(B) - P(A \times B)$ (assuming $P(A)$ and $P(B)$ are very small)
- Mean time to event A: $MT(A) = \frac{1}{P(A)}$
- If events A and B have mean times $MT(A)$ and $MT(B)$, then the mean time to the first event $MT(A \text{ or } B) = \frac{1}{P(A \text{ or } B)}$

If there are $n$ events, each with the same probability $p$, then:

- Probability that one of the events occur: $n \times p$ (assuming $p$ is small)
- Mean time to one of the events (i.e., mean time to the first event): $\frac{1}{n \times p} = \frac{1}{p} \times \frac{1}{n} = m \times \frac{1}{n} = \frac{m}{n}$(where $m = \frac{1}{p}$ is the mean time to an event)

## Module Availability

Module availability is the ratio of service accomplishment to elapsed time. It can be calculated as:

$$\text{Module Availability} = \frac{MTTF}{MTTF + MTTR}$$

where:

- $MTTF$ is the Mean Time To Failure
- $MTTR$ is the Mean Time To Repair

## Redundant Array of Independent Disks (RAID)

RAID is a method of combining multiple disks as a unit for fault tolerance or performance improvement, or both, of a database system. There are several RAID levels, each with its own advantages and disadvantages.

- We use b for Bit; B for byte; A for block
- 8 continuous bits = 1 byte
- 4000/8000 continuous bytes = 1 block 

Please note that the RAID levels are not exhaustive and there are other RAID levels such as RAID 10, RAID 50, etc. that combine the features of the basic RAID levels for additional redundancy or performance.

### RAID 0 (Block Level Striping)

- Data is split into blocks and spread across multiple disks.
- Advantages: Balanced I/O of disk drives, throughput approximately doubles.
- Drawbacks: Any disk failure is catastrophic, and MTTF reduces by a factor of 2.

### RAID 1 (Mirroring)

- Data is duplicated across two or more disks.
- Advantages: Higher read throughput, continues to operate as long as one disk is functional, MTTF increases substantially.
- Drawbacks: Lower write throughput, half storage utilization.

### RAID 2 (Bit Level Striping)

- Data is split into bits and spread across multiple disks.
- Advantages: Higher transfer rate.
- Drawbacks: MTTF reduced by half as in RAID 0, rarely used.

### RAID 3 (Byte Level Striping)

- Data is split into bytes and spread across multiple disks, with a parity byte for error detection.
- Advantages: Higher transfer rate, MTTF increases substantially as one disk failure can be recovered from the data of the other disks.
- Drawbacks: Rarely used.

### RAID 4 (Block Level

Striping)

- Data is split into blocks and spread across multiple disks, with a dedicated disk for parity blocks.
- Advantages: Higher throughput, MTTF increases substantially.
- Drawbacks: Very slow writes, the dedicated parity disk has more writes as parity needs to be updated for every data write.

### RAID 5 (Block Level Striping with Parity Striping)

- Data and parity blocks are both split and spread across multiple disks.
- Advantages: Higher throughput, slower writes but better than RAID 4 as parity bits are distributed among all disks and the number of write operations on average equal among all disks, MTTF increases substantially.
- Drawbacks: Complex to implement and manage.

### RAID 6 (Block Level Striping with Double Parity)

- Similar to RAID 5 except two parity blocks are used.
- Advantages: Any two disk failures can be safe to recover the data, reliability is of the order of $\frac{MTTF^3}{10}$.
- Drawbacks: More complex parity calculation, slower writes due to double parity.

## Choosing RAID Level

When choosing the suitable RAID level, the following factors should be considered:

- **Reliability**: The ability of the system to handle and recover from hardware failure.
- **Performance**: The speed at which data can be read from or written to the disk.
- **Storage Utilization**: The amount of storage space that is effectively used.
- **Price/Number of Disks**: The cost and the number of disks required.

## Storage Area Networks (SAN)

A **Storage Area Network (SAN)** is a dedicated network of storage devices. It has been the fundamental storage for data center type systems with mainframes for decades. Over time, different versions have evolved to allow for more data, but the fundamentals remain the same even today.

Key characteristics of SAN include:

- **Storage Organization**: Storage can be organized as RAID (Redundant Array of Inexpensive Disks) systems. This storage is partitioned and allocated to each system and can also be shared.
- **Usage**: SANs are used for shared-disk file systems.
- **Backup Functionality**: SANs have automated backup functionality.
- **Design Choices**: The failure probability of one disk is different than hundreds of disks, which requires design choices.

## Fault Tolerance by Voting

Fault tolerance in database systems can be achieved through voting mechanisms. There are two main types of voting mechanisms: Failvote and Failfast.

### Failvote

In a Failvote system, a majority agreement is needed to accept an action, such as a read or write operation. For instance, if we start with 10 devices, the system works as long as 6 of them are working. An action is accepted when 6 or more devices agree on the decision. The system stops functioning when the 5th device fails, as there cannot be 6 devices agreeing on the decision.

### Failfast

In contrast, a Failfast system is only concerned with the majority among the working devices. It assumes that we can identify which devices are working. Hence, we can continue to operate until only 2 working devices remain. If both agree, we can proceed with the action. However, if they differ, the system stops. For example, if 0 devices are faulty, we have 10 working and we need at least 6 to agree. If 1 device is faulty, we have 9 working and we need at least 5 to agree. The system continues to operate in this manner until 8 devices are faulty, leaving 2 working devices that both need to agree. If 9 devices are faulty, we have 1 working and we have to stop as there is nothing to compare!

## Supermodule

A Supermodule is a system with

multiple hard disk drives that is expected to function with only one working disk. It uses voting when multiple disks are working/available, but can still function even when only one disk is available.

## Fault Tolerance with Repair

In systems with repair of modules, the faulty equipment is repaired with an average time of MTTR (mean time to repair) as soon as a fault is detected. Sometimes, MTTR is just the time needed to replace the faulty module. Typical values for recent disks are:

- MTTR = Few hours (assuming we stock spare disks) to 1 Day 
- MTTF = 750000 hours (~ 86 years) [hard fault]

The probability of a particular module not being available is given by $\frac{MTTR}{MTTF+MTTR}$, which approximates to $\frac{MTTR}{MTTF}$ if MTTF >> MTTR.

### Fault Tolerance of a Supermodule with Repair

The probability that $n-1$ modules are unavailable, denoted as $P_{n-1}$, is given by $\left(\frac{MTTR}{MTTF}\right)^{n-1}$.

The probability that a particular $i^{th}$ module fails, denoted as $P_f$, is $\frac{1}{MTTF}$.

The probability that the system fails with a particular $i^{th}$ module failing last equals $P_f \times P_{n-1} = \frac{1}{MTTF} \times \left(\frac{MTTR}{MTTF}\right)^{n-1}$.

The probability that a supermodule fails due to any one of the $n$ modules failing last, when other $(n-1)$ modules are unavailable, is $\frac{n}{MTTF} \times \left(\frac{MTTR}{MTTF}\right)^{n-1}$.

The values for this probability differ for failvote and failfast systems.

## Communication Reliability in Message Passing Systems

In a reliable message passing system, the communication between two nodes can be represented as a series of states. The key components of this system include:

- **Out**: Number of messages sent
- **In**: Number of messages received
- **Ack**: Number of acknowledgements

For example, the communication between Node A and Node B can be represented as follows:

- **State 0**: Node A (In:6, Ack:3, Out:3), Node B (Out:6, Ack:6, In:3)
- **State 1**: Node B sends message 7, Node A (In:6, Ack:3, Out:3), Node B (Out:7, Ack:6, In:3)
- **State 2**: Node A sends acknowledge 7, Node A (In:7, Ack:3, Out:3), Node B (Out:7, Ack:6, In:3)
- **State 3**: Node B receives acknowledge 7, Node A (In:7, Ack:3, Out:3), Node B (Out:7, Ack:7, In:3)

## Checkpointing and Message Passing

Before sending a message, a checkpoint is created to ensure data consistency. This can be represented as a series of states:

- **State 0**: Node A (In:6, Out:3, Ack:3), Node B (In:3, Out:6, Ack:6)
- **State 1**: Node B sends message 7, Node A (In:6, Out:3, Ack:3), Node B (In:3, Out:7, Ack:6)
- **State 2**: Node A receives message 7, Node A (In:7, Out:3, Ack:3), Node B (In:3, Out:7, Ack:6)

## Disk Writes and Data Consistency

In the context of database systems, disk writes play a crucial role in ensuring data consistency. The principle is that either the entire block is written correctly on the disk, or the contents of the block remain unchanged. There are two primary methods to achieve this:

1. **Duplex Write**: Each block of data is written in two places sequentially. If one of the writes fails, the system can issue another write. Each block is associated with a version number, and the block with the latest version number contains the most recent data. While reading, we can determine the error of a disk block by its CRC (Cyclic Redundancy Check). This method always guarantees that at least one block has consistent data.

2. **Logged Write**: This method is similar to duplex write, except one of the writes goes to a log. This method is very efficient if the changes to a block are small.

## Cyclic Redundancy Check (CRC)

CRC is an error detection algorithm used to detect errors in data transmission or storage. It involves the use of a polynomial to generate a check value. The most common CRC polynomial is $x^{32} + x^{23} + x^{7} + 1$. This CRC generator can detect all burst errors with a length less than or equal to 32 bits. For burst errors with length 33, 5 out of 10 billion will be undetected, and for burst errors of length 34 or more, 3 out of 10 billion will be undetected.

The process of CRC generation involves several steps:

1. Add n zero bits as 'padding

to the right of the input bits.
2. Compute the (n + 1)-bit pattern representing the CRC's divisor (called a "polynomial").
3. Position the (n + 1)-bit pattern representing the CRC's divisor underneath the left-hand end of the input bits.
4. The algorithm acts on the bits directly above the divisor in each step. The result for each iteration is the bitwise XOR of the polynomial divisor with the bits above it. The bits not above the divisor are simply copied directly below for that step. The divisor is then shifted one bit to the right, and the process is repeated until the bits of the input message becomes zero.

The validity of a received message can be verified by performing the above calculation again, this time with the check value added instead of zeroes. The remainder should equal zero if there are no detectable errors.

## Atomicity in Database Transactions

Atomicity is a property of database transactions which ensures that all changes to data are performed as if they are a single operation. That is, all the changes are performed, or none of them are. For example, if we are transferring $100 from account A to account B, the operation is atomic because either the entire operation (deducting from A and adding to B) happens, or none of it does.

## Disk Block Update Process

The process of updating a disk block involves several steps:

1. **Read**: The contents of the disk block are read into the main memory.
2. **Modify**: The contents in the memory are modified.
3. **Write**: The modified contents are written back to the disk in a different block. The version number of the block is updated.

For example:

- **State 0**: Main Memory (empty), Hard Disk (100 700 (v#7) Block 123)
- **State 1**: Operation: **read**, Main Memory (100 700), Hard Disk (100 700 (v#7) Block 123)
- **State 2**: Operation: **Modify** contents in memory to say 200, contents modified to 200 in memory, update changes to disk, Main Memory (200 700), Hard Disk (100 700 (v#7) Block 123)
- **State 3**: Operation: **Write** to disk in a different block, Written to a different block, Next update will take place to Block 123 and the version number V#7 will be changed to v#9. (Two different physical disks can be used for duplex writes as well), Main Memory (200 700), Hard Disk (100 700 (v#7) Block 123; 200 700 (v#8) Block 475)

# Appendix

## Moore's Law and Joy's Law

Moore's Law states that the capacity of memory chips doubles approximately every 18 months since 1970. On the other hand, Joy's Law for processors states that processor performance doubles approximately every two years since 1984.

These laws have significant implications for the development of hardware and the performance of computer systems. For instance, the IBM Summit (2019) performs 200 Petaflops (200,000 trillion calculations/second), more than doubling the top speeds of the TaihuLight Supercomputer (2018) which was a year older.

## Data Storage Units

It's important to be familiar with the different units of data storage:

- Byte (B): 1
- Kilobyte (KB): $1,024^1$ or $2^{10}$ = 1,024 Bytes
- Megabyte (MB): $1,024^2$ or $2^{20}$ = 1,048,576 Bytes
- Gigabyte (

GB): $1,024^3$ or $2^{30}$ = 1,073,741,824 Bytes
- Terabyte (TB): $1,024^4$ or $2^{40}$ = 1,099,511,627,776 Bytes
- Petabyte (PB): $1,024^5$ or $2^{50}$ = 1,125,899,906,842,624 Bytes
- Exabyte (EB): $1,024^6$ or $2^{60}$ = 1,152,921,504,606,846,976 Bytes
- Zettabyte (ZB): $1,024^7$ or $2^{70}$ = 1,180,591,620,717,411,303,424 Bytes
- Yottabyte (YB): $1,024^8$ or $2^{80}$ = 1,208,925,819,614,629,174,706,176 Bytes

These units are essential for understanding the capacity of different storage devices and the amount of data that can be stored in them.
