# LangGraph 能恢复什么，又不替应用记住什么？

前几章用运行表、操作账本和队列实现了退款运行的恢复。很多团队会改用 LangGraph 这样的有状态图框架来编排同样的流程。本章以 LangGraph Python 为实例回答：它的检查点和中断能恢复哪些东西，哪些仍然必须由应用的运行记录和操作账本负责。案例仍是[一次 AI 运行断线或崩溃后，凭什么恢复](run-identity-and-authoritative-state.md)中的退款 `R-204`。文档核对基于 LangGraph Python `1.2.20`，下面的代码实际运行于 LangGraph `1.2.19`、Python `3.11.13`。

## 图状态、检查点和 `thread_id` 各管什么？

LangGraph 把运行过程表示成一张有状态的节点图。三个概念要先分清：

- **state（图状态）**：节点之间传递的数据。本例的图状态里有 `call-r1` 的订单观察、方案 `Q-204`、客户的确认结论，以及写入节点成功返回后归并进来的退款回执副本。
- **reducer（归并函数）**：决定节点返回的增量怎样并入已有状态。本例用 `operator.add` 把新条目追加到 `observations` 列表；只有节点成功返回的增量才会被归并，暂停和异常都没有增量。
- **checkpointer（检查点保存器）**：按 `thread_id`（图线程标识）保存一串图检查点，恢复时找回图状态和已完成的图步骤。

`thread_id` 不是应用的 `runId`。即使应用为每个运行建一个一对一的线程，也要分别保存两者。更重要的是，图检查点不证明退款是否已创建，代替不了操作账本：权威的确认记录、操作 `R-204`、幂等键 `K-R204`、参数摘要和提供方结果，仍由应用的运行记录和账本持有。示例里用确认结论驱动图内分支；生产应用还要在账本里持久化确认人身份、方案摘要和决定，并在继续写入前重新核验授权。

## `interrupt()` 恢复时为什么会重跑节点？

`interrupt()` 让图在某个节点里暂停，等外部输入（本例是客户确认）；之后用 `Command(resume=...)` 恢复。恢复时，LangGraph 从**该节点的开头**重新执行，而不是从 `interrupt()` 那一行接着往下。所以，写在 `interrupt()` 之前的副作用会在恢复时再执行一次。LangGraph 文档因此要求：中断之前调用的副作用必须是幂等的。

本例的做法是把远端写入放进确认节点之后的单独节点。这样确认节点重跑时不会再发退款请求。但这只避开了一个窗口，没有消除另一个：提供方已经创建退款、写入节点却在返回之前崩溃时，检查点里没有回执，恢复后写入节点会再执行一次。能否不产生第二笔退款，取决于接收方是否兑现“同键同参返回同一结果”的契约，这正是[退款请求超时后，怎样查清结果而不重复扣款](external-writes-and-reconciliation.md)中重放前提的第一条。框架没有提供 exactly-once（恰好一次）保证。

## 用一段可运行代码看边界

下面的示例故意让写入节点在提供方创建退款之后崩溃一次，看各层分别记住了什么。它有几条明确的假设：

- 退款参数和摘要在暂停之前固定，确认之后没有修改；
- 模拟提供方 `FakeProvider` 按幂等键去重：同键同参返回原退款 ID，同键异参拒绝，且去重记录至少保留到本例重试结束；
- `InMemorySaver`、`ledger`（模拟应用账本）和模拟提供方都在同一个进程里；第三步的 `graph.invoke(None, config)` 用同一个 `thread_id` 继续，重跑失败的写入节点。这是故障路径演示，不是跨进程重启。

| 同一进程中的阶段 | 节点与副作用变化 | 累计：确认节点 / 写入节点 / 提供方请求 / 新建退款 | `observations` 本次增量 |
|---|---|---|---|
| 初次 `graph.invoke(...)` 暂停 | `prepare` 写入 `call-r1` 观察与方案；`approve` 触发 `interrupt()` | `1 / 0 / 0 / 0` | 追加 `[订单观察, 方案]`；中断无增量 |
| `Command(resume=...)` 后模拟崩溃 | `approve` 从头重跑并返回确认；提供方创建 `re_demo_204` 后，写入节点在返回前抛异常 | `2 / 1 / 1 / 1` | 追加 `[确认]`；异常无回执增量 |
| 同一 `thread_id` 执行 `graph.invoke(None, config)` | 写入节点重跑，同键同参再发一次；模拟提供方返回原 ID，账本记为完成 | `2 / 2 / 2 / 1` | 追加 `[退款回执]`，没有重复追加 |

两次请求只产生一笔退款，靠的是模拟提供方的去重契约，而不是 LangGraph。若真实接收方不提供去重或查询契约，第二次请求可能创建第二笔退款，或者结果仍然未知。

> [!example]- 可运行代码：LangGraph Python（无密钥，实跑于 1.2.19）
>
> ```python
> from hashlib import sha256
> from importlib.metadata import version
> import json
> from operator import add
> from typing import Annotated, Any, TypedDict
> from langgraph.checkpoint.memory import InMemorySaver
> from langgraph.graph import END, START, StateGraph
> from langgraph.types import Command, interrupt
>
> run_id, thread_id = "run-o73-1", "lg-thread-run-o73-1"
> operation_id, key = "R-204", "K-R204"
> params = {"account": "acct-M9", "charge": "P-73", "amount": 2000,
>           "currency": "usd", "metadata": {"operation_id": operation_id}}
> digest = sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
>
> class State(TypedDict):
>     observations: Annotated[list[dict[str, Any]], add]
>
> class FakeProvider:
>     """模拟接收方：同键同参返回原退款，同键异参拒绝。"""
>     def __init__(self): self.requests, self.created = 0, {}
>     def create_refund(self, idem_key, body_digest):
>         self.requests += 1
>         if idem_key in self.created:
>             old_digest, refund_id = self.created[idem_key]
>             if old_digest != body_digest: raise ValueError("same key, different params")
>             return refund_id
>         self.created[idem_key] = (body_digest, "re_demo_204")
>         return "re_demo_204"
>
> provider, ledger = FakeProvider(), {}
> stats, crash_once = {"approval_node": 0, "side_effect_node": 0}, [True]
>
> def prepare(_):
>     return {"observations": [
>         {"kind": "evidence", "source_call_id": "call-r1", "order": "O-73",
>          "charge": "P-73", "refundable": 2000, "currency": "usd"},
>         {"kind": "plan", "plan_id": "Q-204", "params": params,
>          "operation_id": operation_id, "idempotency_key": key}]}
>
> def approve(state):
>     stats["approval_node"] += 1
>     plan = next(x for x in state["observations"] if x["kind"] == "plan")
>     answer = interrupt({"run_id": run_id, "plan_id": plan["plan_id"],
>                         "params": plan["params"]})
>     return {"observations": [{"kind": "confirmation", "decision": answer["decision"]}]}
>
> def route(state):
>     decision = next(x for x in reversed(state["observations"])
>                     if x["kind"] == "confirmation")["decision"]
>     return "create_refund" if decision == "confirm" else END
>
> def create_refund(_):
>     stats["side_effect_node"] += 1
>     ledger.setdefault(operation_id, {"digest": digest, "status": "effect_in_flight"})
>     if ledger[operation_id]["digest"] != digest: raise ValueError("operation params changed")
>     refund_id = provider.create_refund(key, digest)
>     if crash_once[0]:
>         crash_once[0] = False
>         raise RuntimeError("simulated crash after provider commit")
>     ledger[operation_id] = {"digest": digest, "status": "completed", "refund_id": refund_id}
>     return {"observations": [{"kind": "provider_receipt", "operation_id": operation_id,
>                               "refund_id": refund_id}]}
>
> builder = StateGraph(State)
> builder.add_node("prepare", prepare).add_node("approve", approve)
> builder.add_node("create_refund", create_refund)
> builder.add_edge(START, "prepare").add_edge("prepare", "approve")
> builder.add_conditional_edges("approve", route, {"create_refund": "create_refund", END: END})
> builder.add_edge("create_refund", END)
> graph = builder.compile(checkpointer=InMemorySaver())
> config = {"configurable": {"thread_id": thread_id}}
>
> paused = graph.invoke({"observations": []}, config)
> print(f"langgraph_version={version('langgraph')} run_id={run_id} thread_id={thread_id}")
> print(f"interrupt_pauses={len(paused.get('__interrupt__', []))} "
>       f"approval_node_runs_after_pause={stats['approval_node']}")
> try:
>     graph.invoke(Command(resume={"decision": "confirm"}), config)
> except RuntimeError as error:
>     print(f"simulated_failure={error}")
> final = graph.invoke(None, config)
> print(f"approval_node_runs_total={stats['approval_node']} "
>       f"side_effect_node_runs={stats['side_effect_node']}")
> print(f"provider_requests={provider.requests} provider_refunds={len(provider.created)}")
> print(f"operation_ledger_status={ledger[operation_id]['status']} "
>       f"refund_id={ledger[operation_id]['refund_id']}")
> print("observation_kinds=" + ",".join(x["kind"] for x in final["observations"]))
> ```
>
> 实际输出：
>
> ```text
> langgraph_version=1.2.19 run_id=run-o73-1 thread_id=lg-thread-run-o73-1
> interrupt_pauses=1 approval_node_runs_after_pause=1
> simulated_failure=simulated crash after provider commit
> approval_node_runs_total=2 side_effect_node_runs=2
> provider_requests=2 provider_refunds=1
> operation_ledger_status=completed refund_id=re_demo_204
> observation_kinds=evidence,plan,confirmation,provider_receipt
> ```

## 示例没有替你做什么？

示例只演示图恢复和接收方去重的配合，生产实现还缺几块，都要按主线的状态机补上：

- **发送闸门与取消竞争。** 首次发送和同键重放之前，都要用条件事务核验预期状态、当前 attempt 与 lease、确认仍覆盖原参数、grant 仍可写、未取消，并原子登记这次发送意图。取消先提交就禁止发送；意图先提交就按可能在途处理，之后只允许查询或人工对账。
- **持久化的检查点。** LangGraph 文档把 `InMemorySaver` 定位为内存实现，进程一退出就没了。部署时要换成持久化的 checkpointer，例如数据库支持的 `PostgresSaver`，并单独保留运行记录、确认记录和操作账本。即使图状态持久化了，远端 API 和本地数据库也不会因此共享一个事务。
- **修改方案的规则。** `R-204` 还没登记发送意图时，可以修改方案、重新确认，并使用新的操作版本；一旦登记了意图，就先保留原键和原参数对账。结果未知时不能换键新建；已确认退款后若还要调整，就是一个需要单独确认的新动作。

## middleware、`StateGraph` 和 Deep Agents 不在同一层

LangChain 生态里有三个容易混用的名字，它们属于不同的包和层次：

| 名字 | 所在包与入口 | 它是什么 | 什么时候选 |
|---|---|---|---|
| Agent middleware（智能体中间件） | `langchain.agents.create_agent(...)` 接收 `langchain.agents.middleware` 中的 middleware | 常规模型—工具循环内部的生命周期钩子，围绕模型调用或工具步骤做记录、转换、限流、guardrail（行为约束）或受控重试；底层 agent 图由 LangGraph 执行，它本身不是另一套持久化运行时 | 想在常见 agent loop 里加局部钩子 |
| `StateGraph` | `langgraph.graph.StateGraph` | 显式声明节点、条件分支、人工审批和恢复边界的图 | 需要由应用精确定义确认点、运行账本与副作用对账，例如本例 |
| Deep Agents | `from deepagents import create_deep_agent` | 更高层的 agent harness（智能体执行框架），把计划、虚拟文件系统上下文、子智能体和长期记忆等预制能力组合起来，建立在 LangChain 与 LangGraph 之上 | 任务正好符合这些预制能力 |

不要把 `create_deep_agent` 当作 `StateGraph` 的节点 API，也不要把 middleware 当作图检查点。

## 框架恢复的是图，账本仍归应用

LangGraph 的检查点能恢复图状态和已完成的步骤，`interrupt()` 能让运行等待客户确认后继续；但恢复时被中断的节点会从头重跑，写入节点在远端提交后崩溃也会被再执行一次。能否不重复退款，取决于接收方的去重契约和应用自己的操作账本、发送闸门，而不是框架。回到主线，退款的完整写入与对账规则见[退款请求超时后，怎样查清结果而不重复扣款](external-writes-and-reconciliation.md)；断线和取消怎样进入同一运行，见[用户断线、取消或要回答一个问题时，同一次运行怎样继续](disconnect-cancel-and-user-input.md)。

> [!info]- 来源
>
> - **图状态与 reducer**（“图状态、检查点和 `thread_id` 各管什么”）。LangGraph，[Define and update state](https://docs.langchain.com/oss/python/langgraph/graph-api-state)，“State”“Reducers”；对照 LangGraph Python [1.2.20](https://pypi.org/project/langgraph/1.2.20/) 文档核对。
> - **中断恢复时节点从头重跑、中断前的副作用须幂等**（“`interrupt()` 恢复时为什么会重跑节点”）。LangGraph，[Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)，“Rules of interrupts”“Side effects called before interrupt must be idempotent”。
> - **checkpointer 与 store、内存 saver 的限制**（“示例没有替你做什么”）。LangGraph，[Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)，“Checkpointer vs. store”及内存实现说明。
> - **可运行示例的环境**（“用一段可运行代码看边界”）。原稿示例在 LangGraph 1.2.20、Python 3.11.13 上运行；本章改写为退款案例后，在 LangGraph 1.2.19、Python 3.11.13 上实跑，输出如上。模拟提供方的去重契约与应用账本是本文明确声明的假设。
> - **middleware 与 Deep Agents 的层次与入口所属包**（“middleware、`StateGraph` 和 Deep Agents 不在同一层”）。LangChain，[Middleware overview](https://docs.langchain.com/oss/python/langchain/middleware/overview)，“Agent loop”“Use middleware inside a LangGraph workflow”；Deep Agents，[Overview](https://docs.langchain.com/oss/python/deepagents/overview) 与 [Quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart)，截至 2026-11-09 核对。
