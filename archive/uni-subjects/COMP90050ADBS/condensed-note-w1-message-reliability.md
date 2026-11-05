# Why can acknowledgements still lead to duplicate message effects? / 为什么消息确认仍可能导致重复处理？

If a sender does not receive an acknowledgement, it cannot know whether the message or only its acknowledgement was lost. Retrying may therefore deliver the same logical message again; durable deduplication or an idempotent receiver protocol is needed for once-only effects. / 发送方没有收到确认时，无法判断丢失的是消息还是确认，因此重试可能再次投递同一逻辑消息。要得到一次性效果，需要持久去重或幂等的接收方协议。

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
