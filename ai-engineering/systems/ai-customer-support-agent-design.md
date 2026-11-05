# How do you design a customer-support assistant that can safely issue refunds? / 如何设计能够安全处理退款的客服助手？

**Core explanation / 核心解释：** Keep identity, eligibility, confirmation, and refund execution in an application-controlled workflow. Let the model help interpret or explain the request, but require trusted code to read authoritative order and policy state, verify the amount, obtain any needed confirmation, execute an idempotent action, and confirm its result. Hand off ambiguous or failed cases. / 将身份、资格检查、确认和退款执行放在应用控制的工作流中。模型可以帮助理解或解释请求，但可信代码必须读取权威订单与政策状态、核实金额、获取必要确认、执行幂等动作并确认结果。遇到歧义或失败时转交人工。

## Design: customer support assistant with tools / 带工具的客服助手

**Clarify first:** Which intents can be automated? Which actions change customer accounts or money? What policy and order systems are authoritative? Which requests require explicit consent or human review? What is the handoff path?

**Worked choice / 方案选择：** Suppose the supported flow is checking an order and requesting a refund, and policy disputes or tool failures need a person. I would use a fixed sequence: authenticate the customer; read the order and current policy; have application code check eligibility; show the proposed refund and ask for confirmation; call an idempotent refund operation; verify its result; then report the outcome or hand off. The sequence is predictable and changes financial state, so a fixed workflow makes authorization and stop points explicit. An agent loop would need evidence that dynamic tool choice materially helps before adding that control surface.

**Illustrative architecture / 架构示意:**

~~~text
Customer → intent and risk handling → assistant workflow
                                      ↙          ↘
                          read-only order/FAQ    bounded action tools
                                      ↘          ↙
                              validation → response or human handoff
~~~

**Tool and policy design:**

- Separate read-only lookup from actions that change state.
- Give the runtime—not the model—responsibility for identity, authorization, business limits, confirmation requirements, and final tool execution.
- Make retryable writes idempotent where the underlying system supports it; log the request outcome without exposing unnecessary personal data.
- Use a fixed workflow for a predictable sequence. Consider an agent loop only where dynamic tool selection adds value and can be bounded, observed, and stopped.
- Provide explicit handling for ambiguous intent, unavailable tools, policy conflicts, and user requests for a person.

**Evaluation and operations:** use reviewed examples for common intents, boundary cases, policy changes, tool failures, and escalation. Track task completion, human handoff, tool errors, unauthorized-action attempts, user feedback, and cost per resolved interaction. Treat the automation target as a product decision supported by evaluation, not a fixed percentage.

A tool-call schema can constrain the shape of a proposed call; the application must still check whether the user and action are permitted. OpenAI's [Function calling](https://developers.openai.com/api/docs/guides/function-calling) and [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) documentation, checked 2026-10-15, illustrates provider-specific behavior; it does not replace application-side validation and authorization. See [Agent Fundamentals / 智能体基础](../agents/agent-fundamentals.md), [Tool Design and Function Calling / 工具设计与函数调用](../agents/tool-design-and-function-calling.md), and [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md).

**Related design method / 相关设计方法：** [How do you turn an AI system design prompt into a defensible architecture? / 如何把 AI 系统设计题转化为有依据的架构？](./ai-system-design-interview-questions.md) covers the reusable scoping and trade-off sequence.
