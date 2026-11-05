# How do you write a prompt that makes a task clear and testable? / 如何编写清楚且可检验的任务提示词？

A useful prompt makes the task, necessary context, constraints, and expected output clear. Add examples or structure when they address a measured failure. Prompt text can guide model behavior, but it cannot enforce access control, guarantee factual accuracy, or replace application validation. / 有效提示词要清楚说明任务、必要背景、约束和输出要求。只有在示例或结构能解决实测问题时，才加入它们。提示词能引导模型，但不能执行访问控制、保证事实正确，也不能替代应用校验。

**Key terms / 关键术语：** instruction / 指令；context / 上下文；few-shot example / 少样本示例；output contract / 输出约定；structured output / 结构化输出；validation / 校验。

## The “capable intern” heuristic / “能干的实习生”启发式

Treat the model as capable of using the information and tools actually supplied, but unaware of unstated product rules, source freshness, user permissions, or the format expected by a downstream system. State those requirements explicitly when they matter.

| Vague request | More useful instruction |
|---|---|
| “Handle the refund.” | “Look up the sample order, check the current refund policy, and explain the next step. The application must authorize any refund action before execution.” |
| “Classify the ticket.” | “Choose billing, technical, or general. If the message does not contain enough evidence, return needs_review.” |
| “Summarize the document.” | “Return three bullets about the decisions and open questions. Do not add claims absent from the supplied document.” |

These examples illustrate clarity; they do not imply that a prompt can verify an order, authorize a refund, or make a summary factually correct. The runtime must perform those checks.

## A practical prompt checklist / 提示词检查清单

Include only what helps this task:

1. **Goal / 目标：** State the requested result and audience.
2. **Relevant context / 相关背景：** Supply rules, terminology, source material, or assumptions the model cannot infer.
3. **Inputs / 输入：** Identify the content to transform and delimit untrusted source text.
4. **Constraints / 约束：** Explain required coverage, exclusions, uncertainty handling, and what should trigger a question or handoff.
5. **Examples / 示例：** Add aligned positive, negative, or edge examples when they reduce ambiguity.
6. **Output contract / 输出约定：** Specify fields, format, length, language, and validation expectations.
7. **Tools and side effects / 工具与副作用：** Explain intended tool use, while the application independently enforces permissions and business conditions.

This list is an organizing aid, not a universal seven-layer prompt architecture. Some APIs distinguish system, developer, and user messages; use the roles and precedence defined by the exact API. Put dynamic data in the request context rather than hard-coding user records in reusable instructions.

## Make constraints and examples useful / 让约束和示例真正有用

“Be concise” may be sufficient for a simple chat. A downstream parser may need a precise schema, while a support response may need an uncertainty path. More text is not automatically better: conflicting examples, repeated rules, or irrelevant context can hurt.

Use an example that demonstrates the intended boundary, not only the easiest typical input. If examples and instructions disagree, the model may follow the wrong pattern. Keep examples synthetic and avoid real customer records or secrets.

## Structured output / 结构化输出

For machine-consumed output, prefer an API-supported schema-constrained mode when it fits the task. In the OpenAI API documentation checked on 2026-10-15, Structured Outputs supports schema adherence for supported schemas and models; JSON mode guarantees valid JSON syntax but not adherence to an application schema. Refusals, incomplete responses, unsupported schema features, and semantic errors still need handling. Schema conformance does not prove that a field is true, authorized, or safe to execute. If the chosen API cannot enforce the schema, parse, validate, and use a bounded retry or explicit failure path.

For human-readable output, headings, bullets, XML tags, or code fences can make sections easier to interpret. Delimiters help organize content; they are not a security boundary and do not guarantee valid machine output.

**Small output contract / 简单输出约定:**

~~~json
{
  "summary": "A short account of the supplied text",
  "category": "billing",
  "needs_review": false
}
~~~

Application code should check allowed categories and required fields, and verify any consequential claim against its source. For the broader distinction between task success, factual correctness, source support, and instruction adherence, see [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md).

## Optional organization pattern / 可选组织方式

Some teams group a long instruction by general-to-specific concerns. The following is a checklist, not a standard that every prompt needs:

| Section | What it contains |
|---|---|
| **Role and task context / 角色与任务背景** | Work setting and goal. |
| **Behavior / 行为** | Tone and response style. |
| **Tool guidance / 工具说明** | Intended use and limits of available tools. |
| **Procedure / 流程** | Steps that are useful to explain to the model. |
| **Output / 输出** | Format and length. |
| **Safety reminders / 安全提醒** | Human-readable reminders; code still enforces authorization and stop conditions. |
| **Request-specific context / 本轮背景** | Current task data and state, supplied only when needed. |

Do not put real names, ticket numbers, secrets, or private histories in a reusable prompt. Use a synthetic record when illustrating the format.

## Related notes / 相关笔记

- [Advanced Prompting Techniques / 高级提示技巧](./advanced-prompting-techniques.md) covers optional methods for failures that a clear baseline prompt does not resolve.
- [Context Engineering Principles / 上下文工程原则](../context/context-engineering-principles.md) explains how to select and update the full information available to each inference.
- [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md) explains why prompts cannot replace runtime authorization and stop controls.

## Sources / 来源

- OpenAI, [Model optimization: write effective prompts](https://developers.openai.com/api/docs/guides/model-optimization#write-effective-prompts), checked 2026-10-15.
- OpenAI, [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs), checked 2026-10-15. API behavior and supported schema features can change.
