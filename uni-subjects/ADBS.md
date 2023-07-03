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

1. **Efficiency/Speed**
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

## Dominant Factor in DBMS

Access to stored data in an efficient manner has become the dominant factor in database management systems.

## Basic Hardware of a Classical Disk

A classical disk operates by rapidly rotating with a magnetic head, which reads and writes data to the platter surfaces. The disk structure includes:

- Tracks: circular path on disk surface
- Tracks are subdivided into disk sectors


## Disk Access

The time it takes to read data from or write data to a disk is known as disk access time. This time is calculated as the sum of the seek time, rotational delay, and the time it takes to transfer the data. 

The formula for calculating disk access time is:

$$
\text{Disk Access Time} = \text{Seek Time} + \text{Rotational Delay} + \frac{\text{Transfer Length}}{\text{Bandwidth}}
$$

For example, if the average seek time is 12 ms, the rotational delay is 4 ms, and the transfer rate is 4MB/sec, the disk access time for a transfer size of 4KB would be calculated using the above formula.

## Solid-State Drive (SSD)

Unlike Hard Disk Drives (HDD), Solid-State Drives (SSD) have no moving parts and use silicon rather than magnetic materials. This results in several advantages over HDDs:

- No seek/rotational latency
- No start-up times
- Silent operation
- Faster random access times (typically under 100 micro-seconds compared to 2000 - 3000 micro-seconds for HDD)

However, SSDs are relatively expensive and have certain read/write limitations, which is why they have not yet completely replaced HDDs.

An example of an SSD is the Samsung 860 PRO SATA III 2.5-inch, which has a capacity of 4TB and offers sustained sequential read and write speeds of up to 560 MB/s and 530 MB/s, respectively.

## Memory Hierarchy

The memory hierarchy is a model that describes the relationship between different types of memory in a computer system. It includes the processor, registers, L1 and L2 cache, main memory, and hard disk. The access speed drops significantly from on-chip to off-chip memory.

The effective memory access time (EA) can be calculated using the formula:

$$
EA = H*C + (1-H)*M
$$

where:
- H is the hit ratio (the ratio of references satisfied by cache to total references)
- C is the cache access time
- M is the memory access time

The same concept applies to the disk buffer or disk cache, which is embedded in the disk and is different from the cache in the memory hierarchy. The effective disk buffer access time can be calculated using a similar formula:

$$
EA = HB*BC + (1-HB)*D
$$

where:
- HB is the hit ratio of the disk buffer
- BC is the buffer access time
- D is the disk access time

For example, if the disk access time is S, the buffer access time is C, the hit ratio is H, and S = 1000C, the effective access time, EA, as a multiple of C when H = 30% can be calculated using the above formula.

## Moore's Law and Joy's Law

Moore's Law states that the capacity of memory chips doubles approximately every 18 months since 1970. On the other hand, Joy's Law for processors states that processor performance doubles approximately every two years since 1984.

These laws have significant implications for the development of hardware and the performance of computer systems. For instance, the IBM Summit (2019) performs 200 Petaflops (200,000 trillion calculations/second), more than doubling the top speeds of the TaihuLight Supercomputer (2018) which was a year older. 

## Data Storage Units

It's important to be familiar with the different units of data storage:
- Byte (B): 1
- Kilobyte (KB): \(1,024^1\) or \(2^{10}\) = 1,024 Bytes
- Megabyte (MB): \(1,024^2\) or \(2^{20}\) = 1,048,576 Bytes
- Gigabyte (GB): \(1,024^3\) or \(2^{30}\) = 1,073,741,824 Bytes
- Terabyte (TB): \(1,024^4\) or \(2^{40}\) = 1,099,511,627,776 Bytes
- Petabyte (PB): \(1,024^5\) or \(2^{50}\) = 1,125,899,906,842,624 Bytes
- Exabyte (EB): \(1,024^6\) or \(2^{60}\) = 1,152,921,504,606,846,976 Bytes
- Zettabyte (ZB): \(1,024^7\) or \(2^{70}\) = 1,180,591,620,717,411,303,424 Bytes
- Yottabyte (YB): \(1,024^8\) or \(2^{80}\) = 1,208,925,819,614,629,174,706,176 Bytes

These units are essential for understanding the capacity of different storage devices and the amount of data that can be stored in them.

## Database Types

### Simple File
- **Definition**: Data is stored as a plain text file. Each line holds one record, with fields separated by delimiters (e.g., commas or tabs).
- **Strengths**: Fast for simple applications.
- **Weaknesses**: Can be slow for complex applications, less reliable, hard to maintain (concurrency problems), requires additional code development for features that exist in relational databases.
- **Suitable for**: Simple applications where speed is a priority.

### Relational Database Systems (RDBS)
- **Definition**: Data is stored as a collection of tables (relations) consisting of rows and columns. A primary key is used to uniquely identify each row.
- **Strengths**: Very reliable, application independent optimisation, well suited to many applications, very fast due to large main memory machines and SSDs.
- **Weaknesses**: Can be slow for some simple applications.
- **Suitable for**: Applications requiring high reliability and speed, and those that can benefit from application independent optimisation.

### Object Oriented Database Systems (OODB)
- **Definition**: Data is stored in the form of 'objects' directly, similar to Object Oriented Programming (OOP).
- **Strengths**: Reliable, well suited for applications requiring complex data.
- **Weaknesses**: Can be slow on some applications, limited application independent optimisation.
- **Suitable for**: Applications requiring complex data structures and methods.

### NoSQL (Key-value pair)
- **Definition**: Non-relational database modelled other than the tabular relations. Covers a wide range of database types.
- **Strengths**: Flexible/no fixed schema, simple design, should linearly scale.
- **Weaknesses**: Compromise consistency, allows replications, may result in stale reads.
- **Suitable for**: Applications that require flexibility and scalability, and can tolerate eventual consistency.

### Deductive Database Systems (DDBS)
- **Definition**: A database system that can make deductions based on rules and facts stored in the database.
- **Strengths**: Most of the application can be developed entirely using DDBS.
- **Weaknesses**: Many applications do not require the expressive power of these systems.
- **Suitable for**: Applications that require rule-based deductions.

## Database Architectures

### Centralized (Client-Server)
- **Definition**: A central server with a central DB in one location (but client and server can be in different locations).
- **Advantages**: Simple system administration, effective optimisation process.
- **Challenges**: Limited to one location.
- **Suitable for**: Applications that can be managed centrally, such as PC/Cluster Computing/data centres.

### Distributed
- **Definition**: Data is distributed across several nodes in different locations.
- **Advantages**: Can handle large data sets, provides concurrency, recovery and transaction processing.
- **Challenges**: Hard system administration, complicated crash recovery, potential inconsistency due to data replication.
- **Suitable for**: Large-scale applications that require data distribution and concurrency.

### World Wide Web (WWW)
- **Definition**: Data is stored in many locations with several owners of data.
- **Advantages**: Wide data availability.
- **Challenges**: No certainty of data availability or consistency, ineffective optimisation process, potential security issues.
- **Suitable for**: Applications that require wide data availability and can tolerate inconsistency.

### Grid
- **Definition**: Data and processing are shared among a group of computer systems which may be geographically separated.
- **Advantages**: Shared data and processing.
- **Challenges**: Administration done locally by each owner of the

system, reliability and security not well developed or studied.
- **Suitable for**: Specific applications, such as scientific applications.

### Peer-to-Peer (P2P)
- **Definition**: Data and processing is shared among a group of computer systems which may be geographically separated. Nodes can join and leave the network at will.
- **Advantages**: Shared data and processing, flexible network membership.
- **Challenges**: Hard to design transaction models due to flexible network membership.
- **Suitable for**: Specific applications, such as scientific applications, where nodes need the flexibility to join and leave the network.

### Cloud Computing
- **Definition**: Offers online computing, storage and a range of new services for data and devices that are accessible through the Internet.
- **Advantages**: User pays for the services just like phone services, electricity, etc. Huge potential for developing applications with minimal infrastructure costs.
- **Challenges**: Dependence on internet connectivity, potential security issues.
- **Suitable for**: Applications that require on-demand resources and services, and can benefit from the pay-as-you-go model.

## Fault Tolerance

Fault tolerance is the property that enables a system to continue operating properly in the event of the failure of some of its components.

## Basic Probability and Mean Time to Event

- Probability of an event A happening in a certain period: $P(A)$
- Probability of both events A and B happening in that period (assuming A and B are independent events): $P(A \text{ and } B) = P(A) \times P(B)$
- Probability of either event A or B happening in that period: $P(A \text{ or } B) = P(A) + P(B) - P(A \text{ and } B) = P(A) + P(B) - P(A) \times P(B)$ (assuming $P(A)$ and $P(B)$ are very small)
- Mean time to event A: $MT(A) = \frac{1}{P(A)}$
- If events A and B have mean times $(MT(A)) and (MT(B))$, then the mean time to the first event $MT(A \text{ or } B) = \frac{1}{P(A \text{ or } B)}$

If there are $n$ events, each with the same probability $p$, then:
- Probability that one of the events occur: $n \times p$ (assuming $p$ is small)
- Mean time to one of the events (i.e., mean time to the first event): $\frac{1}{n \times p} = \frac{1}{p} \times \frac{1}{n} = m \times \frac{1}{n} = \frac{m}{n}$ (where $m = \frac{1}{p}$ is the mean time to an event)


## Module Availability

Module availability measures the ratio of service accomplishment to elapsed time. It can be calculated as:
$$\text{Module Availability} = \frac{MTTF}{MTTF + MTTR}$$
where:
- $MTTF$ is the Mean Time To Failure
- $MTTR$ is the Mean Time To Repair

## Redundant Array of Independent Disks (RAID)

RAID is a method of combining multiple disks as a unit for fault tolerance or performance improvement, or both, of a database system.

### RAID 0 (Block level Striping)

- Data is split into blocks and spread across multiple disks.
- Advantages: Provides balanced I/O of disk drives, throughput approximately doubles.
- Drawbacks: Any disk failure will be catastrophic, and MTTF reduces by a factor of 2.

### RAID 1 (Mirroring)

- Data is duplicated across two or more disks.
- Advantages: Provides higher read throughput, continues to operate as long as one disk is functional, MTTF increases substantially.
- Drawbacks: Lower write throughput, half storage utilization.

### RAID 2 (Bit level Striping)

- Data is split into bits and spread across multiple disks.
- Advantages: Provides higher transfer rate.
- Drawbacks: MTTF reduced by half as in RAID 0, rarely used.

### RAID 3 (Byte level Striping)

- Data is split into bytes and spread across multiple disks, with a parity byte for error detection.
- Advantages: Provides higher transfer rate, MTTF increases substantially as one disk failure can be recovered from the data of the other disks.
- Drawbacks: Rarely used.

### RAID 4 (Block level Striping)

- Data is

split into blocks and spread across multiple disks, with a dedicated disk for parity blocks.
- Advantages: Provides higher throughput, MTTF increases substantially.
- Drawbacks: Very slow writes, the dedicated parity disk has more writes as parity needs to be updated for every data write.

### RAID 5 (Block level Striping with Parity Striping)

- Data and parity blocks are both split and spread across multiple disks.
- Advantages: Provides higher throughput, slower writes but better than RAID 4 as parity bits are distributed among all disks and the number of write operations on average equal among all disks, MTTF increases substantially.
- Drawbacks: Complex to implement and manage.

### RAID 6 (Block level Striping with Double Parity)

- Similar to RAID 5 except two parity blocks are used.
- Advantages: Any two disk failures can be safe to recover the data, reliability is of the order of MTTF^3/10.
- Drawbacks: More complex parity calculation, slower writes due to double parity.

## Note

- We use b for Bit; B for byte; A for block
- 8 continuous bits = 1 byte
- 4000/8000 continuous bytes = 1 block 

Please note that the RAID levels are not exhaustive and there are other RAID levels such as RAID 10, RAID 50, etc. that combine the features of the basic RAID levels for additional redundancy or performance.

## Fault Tolerance by Voting

Fault tolerance in database systems can be achieved through voting mechanisms. There are two main types of voting mechanisms: Failvote and Failfast.

### Failvote

In a Failvote system, a majority agreement is needed to accept an action, such as a read or write operation. For instance, if we start with 10 devices, the system works as long as 6 of them are working. An action is accepted when 6 or more devices agree on the decision. The system stops functioning when the 5th device fails, as there cannot be 6 devices agreeing on the decision.

### Failfast

In contrast, a Failfast system is only concerned with the majority among the working devices. It assumes that we can identify which devices are working. Hence, we can continue to operate until only 2 working devices remain. If both agree, we can proceed with the action. However, if they differ, the system stops. For example, if 0 devices are faulty, we have 10 working and we need at least 6 to agree. If 1 device is faulty, we have 9 working and we need at least 5 to agree. The system continues to operate in this manner until 8 devices are faulty, leaving 2 working devices that both need to agree. If 9 devices are faulty, we have 1 working and we have to stop as there is nothing to compare!

## Supermodule

A Supermodule is a system with multiple hard disk drives that is expected to function with only one working disk. It uses voting when multiple disks are working/available, but can still function even when only one disk is available.

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

## Communication Reliability

In a reliable message passing system, we have three key components:

- **Out**: Number of messages sent
- **In**: Number of messages received
- **Ack**: Number of acknowledgements

The communication between two nodes can be represented as a series of states. For example:

- **State 0**: Node A (In:6, Ack:3, Out:3), Node B (Out:6, Ack:6, In:3)
- **State 1**: Node A (In:6, Ack:3, Out:3), Node B sends message 7 (Out:7, Ack:6, In:3)
- **State 2**: Node A sends acknowledge 7 (In:7, Ack:3, Out:3), Node B (Out:7, Ack:6, In:3)
- **State 3**: Node A (In:7, Ack:3, Out:3), Node B (Out:7, Ack:7, In:3)

## Checkpoint Before Sending a Message

Before sending a message, a checkpoint is created to ensure data consistency. This can be represented as a series of states:

- **State 0**: Node A (In:6, Out:3, Ack:3), Node B (In:3, Out:6, Ack:6)
- **State 1**: Node A (In:6, Out:3, Ack:3), Node B sends message 7 (In:3, Out:7, Ack:6)
- **State 2**: Node A (In:6, Out:3, Ack:3), Node B (In:3, Out:7, Ack:6)
- **State 3**: Node A receives message 7 (In:7, Out:3, Ack:3), Node B (In:3, Out:7, Ack:6)

## Disk Writes for Consistency

To ensure consistency, either the entire block is written correctly on the disk, or the contents of the block remain unchanged. There are two methods to achieve this:

1. **Duplex Write**: Each block of data is written in two places sequentially. If one of the writes fails, the system can issue another write. Each block is associated with a version number, and the block with the latest version number contains the most recent data. While reading, we can determine the error of a disk block by its CRC (Cyclic Redundancy Check). This method always guarantees that at least one block has consistent data.

2. **Logged Write**: Similar to duplex write, except one of the writes goes to a log. This method is very efficient if the changes to a block are small.

## Cyclic Redundancy Check (CRC)

CRC is a method used to detect errors in data transmission or storage. A CRC polynomial is used to generate a check value. The most common CRC polynomial is $x^{32} + x^{23} + x^{7} + 1$. This CRC generator can detect all burst errors with a length less than or equal to 32 bits. For burst errors with length 33, 5 out of 10 billion will be undetected, and for burst errors of length 34 or more, 3 out of 10 billion will be undetected.

The process of CRC generation involves several steps:

1. Add n zero bits as 'padding' to the right of the input bits.
2. Compute the (n + 1)-bit pattern representing the CRC's divisor (called a "polynomial").
3. Position the (n + 1)-bit pattern representing the CRC's divisor underneath the left-hand

end of the input bits.
4. The algorithm acts on the bits directly above the divisor in each step. The result for each iteration is the bitwise XOR of the polynomial divisor with the bits above it. The bits not above the divisor are simply copied directly below for that step. The divisor is then shifted one bit to the right, and the process is repeated until the bits of the input message becomes zero.

The validity of a received message can be verified by performing the above calculation again, this time with the check value added instead of zeroes. The remainder should equal zero if there are no detectable errors.

## Atomicity

Atomicity is a property of database transactions which ensures that all changes to data are performed as if they are a single operation. That is, all the changes are performed, or none of them are. For example, if we are transferring $100 from account A to account B, the operation is atomic because either the entire operation (deducting from A and adding to B) happens, or none of it does.

## Updating Disk Block

The process of updating a disk block involves several steps:

1. **Read**: The contents of the disk block are read into the main memory.
2. **Modify**: The contents in the memory are modified.
3. **Write**: The modified contents are written back to the disk in a different block. The version number of the block is updated.

For example:

- **State 0**: Main Memory (empty), Hard Disk (100 700 (v#7) Block 123)
- **State 1**: 
  - Operation: **read**
  - Main Memory (100 700), Hard Disk (100 700 (v#7) Block 123)
- **State 2**:
  - Operation: **Modify** contents in memory to say 200, contents modified to 200 in memory, update changes to disk
  -  Main Memory (200 700), Hard Disk (100 700 (v#7) Block 123)
- **State 3**: 
  - Operation: **Write** to disk in a different block, Written to a different block, Next update will take place to Block 123 and the version number V#7 will be changed to v#9. (Two different physical disks can be used for duplex writes as well)
  - Main Memory (200 700), Hard Disk (100 700 (v#7) Block 123; 200 700 (v#8) Block 475)

