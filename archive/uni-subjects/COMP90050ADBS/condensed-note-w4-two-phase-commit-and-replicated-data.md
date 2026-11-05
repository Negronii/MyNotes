# How does two-phase commit reach one outcome across participants? / 两阶段提交如何让多个参与者得到同一结果？

Participants vote and durably enter prepared state before the coordinator records one global decision. YES means prepared, not an independent commit decision, so a participant may block while the coordinator is unreachable. Isolation and one-copy serializability require separate concurrency-control rules. / 参与者投票并持久进入 prepared 状态后，协调者才记录一个全局决议。YES 表示已准备，不是独立的提交决议，因此协调者不可达时参与者可能阻塞。隔离和单副本可串行化需要另外的并发控制规则。

## Distributed Database / 分布式数据库
### DBMS in Real life
- Many production DBMS deployments serve networked clients; embedded databases are also common.
- Large companies have multiple servers working together
- Many systems has a complex distributed architecture
- e.g., bank transactions in different branches

### Two-Phase Commit Protocol (2PC), distinct from Two-Phase Locking (2PL)
2PC coordinates the atomic outcome across participants; it does not itself provide transaction isolation. [PostgreSQL's two-phase transaction documentation](https://www.postgresql.org/docs/18/two-phase.html) describes durable prepared transactions; [Gray and Lamport's transaction-commit paper](https://lamport.azurewebsites.net/video/consensus-on-transaction-commit.pdf) explains why the coordinator waits for all resource managers before committing.


- Goal: either all of the servers commit the transaction, or all of them abort the transaction
- One of the servers becomes the coordinator who must ensures the same outcome at all of the servers

Phase 1 (voting phase)

- coordinator asks all participants if they can commit
- each participant votes
- A YES vote means the participant is prepared: it must durably record the prepared state and wait for the coordinator's decision. It cannot unilaterally decide the global outcome after voting YES.
- A NO vote lets the coordinator decide abort.

Phase 2 (completion phase)

- coordinator tells all participants to commit or abort
- the participants carry out the joint decision

![](./twophaseCommitProtocol.png)

1. `Coordinator -> Participant`: `canCommit (trans)`\
   The coordinator asks whether the participant can commit a transaction.

2. `Participant -> Coordinator`: `Yes / No`\
   The participant replies with its vote on whether it can commit the transaction.

3. The coordinator makes one global decision: COMMIT requires every required YES vote, while a NO vote or a pre-decision timeout can lead to ABORT:

   - `Coordinator -> Participant`: `doCommit (trans)`\
      Only when every required participant has voted YES does the coordinator durably record the global COMMIT decision and then notify all participants to commit.
   - `Coordinator -> Participant`: `doAbort (trans)`\
      If any participant votes NO, or a required vote is still missing when the coordinator times out before making a commit decision, the coordinator durably records global ABORT and notifies all participants to abort, including participants that already voted YES.

4. `Participant -> Coordinator`: `haveCommitted (trans, participant)`\
   The participant confirms that it has committed the transaction, notifying the coordinator.

5. If a participant recovers in the prepared state without a recorded decision, it asks the coordinator for the durable outcome. If the coordinator is unreachable, the prepared participant may have to wait.

- Before the global decision, a participant may vote NO and the coordinator may choose abort if any vote is NO or a participant fails to respond. After a participant has voted YES, it remains durably prepared and can block if the coordinator is unreachable; timeout alone does not safely tell it to abort. The coordinator records and communicates the decision, and participants follow it.
- If the decision is abort, the coordinator asks participants to roll back.
- The coordinator records its decision durably before notifying participants; participants record and follow the decision as required by their recovery protocol.

### Concurrency Control in Networked System
![](concurrencyProblemNetworked.png)

- Each server is responsible for applying concurrency control to its own objects
- The members of a collection of servers of distributed transactions are jointly responsible for ensuring that they are performed in a serially equivalent manner
- Servers independently acting would not work
- If transaction T is before transaction U in their conflicting access to objects at one of the servers
- Then: They must be in that order at all of the servers whose objects are accessed in a conflicting manner by both T and U
- The Coordinator should assure this

### Concurrency Control Review
Timestamp ordering concurrency control

- The coordinator accessed by a transaction issues a **globally unique timestamp**
- The timestamp is passed **with each object access**
- The servers are jointly responsible for ensuring serial equivalence, that is if T access an object before U, then T is before U at all objects

Optimistic concurrency control\
For distributed transactions to work:

- When optimistic concurrency control is combined with 2PC, each participant validates before voting YES; 2PC itself does not provide concurrency validation.
- A distributed optimistic protocol must define a consistent transaction order, often using globally comparable timestamps.

### Transactions with replicated data
One-copy Serializability\
The effect of transactions on replicated objects should be the **same as if they had been performed one at a time on a single set of objects**

If all servers are available then no issue – but what if some servers are not available?

### Available copies replication
- The available copies replication scheme is designed to allow some servers to be temporarily unavailable
- Before a transaction commits, it checks for failures and recoveries of the RMs it has contacted, the set should not change during execution

e.g., X fails before T’s deposit. T would check if X is still available. If X is unavailable, then T will abort.
