# What database types and architectures does this course compare? / 本课程比较哪些数据库类型与体系结构？

These labels describe broad ways to organize data and computation. They identify different design concerns, but none alone guarantees speed, scale, availability, or security; those properties depend on the system, workload, and protocol. / 这些名称描述数据与计算的宽泛组织方式，可帮助识别设计关注点，但任何分类本身都不保证速度、扩展性、可用性或安全性；这些属性取决于具体系统、负载和协议。

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
