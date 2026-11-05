# What can duplex writes, logs, and CRC actually guarantee? / 双写、日志与 CRC 实际能保证什么？

Redundant copies and logs support recovery only when write order, version selection, and failure assumptions are defined. CRC detects many accidental error patterns but neither repairs data nor authenticates its source. A storage technique alone does not make a multi-step transaction atomic. / 只有在写入顺序、版本选择和故障前提明确时，冗余副本与日志才支持恢复。CRC 能检测许多意外错误模式，但既不能修复数据，也不能认证来源。存储技术本身不会让多步事务具备原子性。

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
