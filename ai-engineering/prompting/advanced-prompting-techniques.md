# Advanced Prompting Techniques / 高级提示技巧

**Core explanation / 核心解释：** Few-shot examples, reasoning prompts, self-consistency, tool loops, prompt chains, and prompt generation are optional methods for particular failure modes. They add tokens, calls, or control-flow complexity, so compare them with a simpler prompt and application-side checks on representative cases. Published results establish benefits only for the evaluated tasks and setups, not a general performance guarantee. / 少样本示例、推理提示、自一致性、工具循环、提示词链和提示词生成都是针对特定失败模式的可选方法。它们会增加 token、调用或控制流复杂度，因此应在有代表性的样本上与简单提示和应用校验做比较。论文结果只说明其评估任务和设置下的效果，不构成普遍性能保证。

**Key terms / 关键术语：** zero-shot / 零样本；few-shot / 少样本；chain-of-thought (CoT) / 思维链；self-consistency / 自一致性；ReAct / 推理与行动；prompt chaining / 提示词链；meta-prompting / 元提示。

## When should you use few-shot vs. zero-shot prompting? / 何时使用少样本或零样本提示？

Start with a clear zero-shot instruction for a simple, well-defined task. Add a few examples when they resolve ambiguity, demonstrate a non-obvious label boundary, or show a required output format. Keep examples representative and include meaningful edge cases. More examples can consume context and can also bias the model toward an accidental pattern.

**Zero-shot / 零样本:**

~~~text
Classify the sentiment as positive, negative, or neutral.
Review: "The product arrived late, but the quality exceeded expectations."
Return one label.
~~~

**Few-shot / 少样本:**

~~~text
Classify each review as positive, negative, or neutral.
"Terrible experience, never buying again." → negative
"Exactly what I needed. Fast shipping." → positive
"It's okay. Nothing special." → neutral
"The product arrived late, but the quality exceeded expectations." →
~~~

For extraction, examples can demonstrate how a date or amount should be normalized. Keep them synthetic; validate required fields, allowed values, and source evidence in application code. Measure the example/no-example variants on the same held-out cases rather than assuming few-shot is more reliable.

## What is chain-of-thought, and when is it useful? / 什么是思维链，何时有用？

Chain-of-thought (CoT) prompting asks for intermediate reasoning text before a final answer, often through examples or an instruction. Research found gains on some multi-step arithmetic and reasoning benchmarks under particular model and prompt conditions. The result is task- and model-dependent: asking for step-by-step text does not guarantee correct reasoning, and a written rationale is not proof that it faithfully describes the model's internal computation.

A small arithmetic illustration is 4 × $2 + 2 × $3 = $8 + $6 = $14. A model may give a concise answer, a worked explanation, or an incorrect derivation. Verify consequential arithmetic with code or another trusted method.

OpenAI's reasoning-model guidance, checked 2026-10-15, recommends trying a straightforward prompt first; asking for step-by-step reasoning can be unnecessary or counterproductive for those models. API behavior differs by provider and model, so evaluate the actual target rather than carrying a prompt recipe across systems.

## What is self-consistency? / 什么是自一致性？

Self-consistency samples multiple candidate reasoning answers and aggregates their final answers, often by a majority vote. The research paper reported improvements on several tested reasoning benchmarks. It can help when the candidates make partly independent errors, but repeated samples can agree on the same wrong answer. Use a task-specific verifier for important results.

**Illustration, not model output / 示意，不是模型实测输出：** For 17 × 23, two valid decompositions are 17 × (20 + 3) = 340 + 51 = 391 and (10 + 7) × 23 = 230 + 161 = 391. If sampling several candidates, normalize equivalent answers before aggregation; voting does not replace checking.

Multiple samples increase token use and usually require more inference work. Exact cost and wall-clock impact depend on batching, provider behavior, and the selected model. Compare accuracy, latency, and cost with a single answer on the target task.

## What is ReAct, and when should an application use a tool loop? / 什么是 ReAct，应用何时应使用工具循环？

ReAct is a research prompting pattern that interleaves a model's reasoning text, an action, and an observation from an environment. Its paper evaluated it on specific knowledge and interactive tasks. It is one design option for tasks that need successive observations and actions, not a universal default for tool use. A one-shot function call or a developer-controlled workflow may be simpler when the path is known.

**Synthetic flight-search illustration / 虚构的航班搜索示例:**

~~~text
User: Find the lowest listed fare from NYC to LA for next Tuesday.
Action: search_flights(origin="NYC", destination="LA", date=<resolved date>)
Observation: The search service returned three fares: $189, $210, and $175.
Answer: The lowest fare returned by that search was $175.
~~~

This example assumes a real search service would resolve airport codes, date, currency, freshness, and availability. The model must not invent those observations. The application should validate tool arguments, authorize side effects, limit tool access and turns, record outcomes, and stop safely on errors. Treat retrieved pages and tool output as untrusted input; see [Agent Fundamentals / 智能体基础](../agents/agent-fundamentals.md), [Tool Design and Function Calling / 工具设计与函数调用](../agents/tool-design-and-function-calling.md), and [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md).

## When should you chain prompts? / 何时串联提示词？

Use a fixed prompt chain when the task has separable steps and code can validate, branch, retry, or stop between them. If the sequence is known, developer-controlled stages can be easier to inspect than an open-ended agent loop. Each model call can still be wrong; validate intermediate outputs and test the whole chain.

**Outline → validate → write / 大纲 → 校验 → 写作:**

1. Ask for an outline in a declared schema.
2. Parse it and check required sections and constraints in application code.
3. If valid, ask for a draft based on the outline; otherwise return an explicit failure or a bounded correction request.

~~~python
outline = call_model(make_outline_prompt(topic))
parsed = parse_schema(outline)
if not parsed.ok:
    return validation_error(parsed.issues)
if not deterministic_checks(parsed.value):
    return validation_error("outline violates required section rules")
return call_model(make_draft_prompt(parsed.value))
~~~

If five stages each succeed with probability 0.95 and failures are independent, the probability that all five succeed is 0.95⁵ ≈ 0.774. Real failures may be correlated, and retries or gates change the result; measure the actual workflow instead of treating this illustration as a reliability estimate.

## What is meta-prompting? / 什么是元提示？

Meta-prompting uses a model to generate candidate instructions or revise an existing prompt in response to concrete failures. Treat either output as a candidate. Evaluate variants on development examples, inspect failures, and keep a final held-out set untouched until selection; repeated tuning against the same set can overfit it.

Automatic Prompt Engineer (APE) is one research approach to generating and selecting instruction candidates for evaluated tasks. The templates here are a lightweight human-directed workflow, not a reproduction of that method or its reported results.

**Candidate generation / 生成候选提示词:**

~~~text
Task: Classify a support message as billing, technical, or general.
Success: Choose the supported category; return needs_review when evidence is insufficient.
Inputs: Only the supplied message and category definitions.
Output: Return the category and needs_review as JSON.
Generate three materially different candidate instructions. For each, state which ambiguity it addresses. Do not claim the candidates have been tested.
~~~

**Failure-driven revision / 根据失败样例修订:**

~~~text
Current prompt:
[insert the current synthetic prompt]

Observed failure:
[insert a synthetic input and the incorrect output]

Expected behavior:
[state the correct output and why]

Revise only the instruction needed to address this failure. Preserve the task, output contract, and other constraints. Return the revised prompt and a short change note. This candidate still requires evaluation on examples not used to write it.
~~~

A practical loop is to define success criteria, generate or revise candidates, compare them on the same development set, review regressions and edge cases, then confirm the selected version on an untouched held-out set before deployment. Keep the evaluation data appropriate for the sensitivity and policy of the task.

## Related notes / 相关笔记

- [Prompt Engineering Fundamentals / 提示工程基础](./prompt-engineering-fundamentals.md) covers clear instructions, examples, and output contracts.
- [Context Engineering Principles / 上下文工程原则](../context/context-engineering-principles.md) covers the information available to each inference.
- [Agent Fundamentals / 智能体基础](../agents/agent-fundamentals.md), [Orchestration Patterns / 编排模式](../agents/orchestration-patterns.md), and [Tool Design and Function Calling / 工具设计与函数调用](../agents/tool-design-and-function-calling.md) cover runtime tool loops and control flow.

## Sources / 来源

- Wei et al., [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903).
- Kojima et al., [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916).
- Wang et al., [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171).
- Yao et al., [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629).
- Zhou et al., [Large Language Models Are Human-Level Prompt Engineers](https://arxiv.org/abs/2211.01910), for the APE instruction-generation and selection approach.
- OpenAI, [Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices), checked 2026-10-15. These instructions describe OpenAI reasoning models and should not be generalized to other APIs.
- OpenAI, [Prompt generation](https://developers.openai.com/api/docs/guides/prompt-generation), checked 2026-10-15. This is an OpenAI-specific example of generating or revising prompt text, not evidence that a generated prompt performs better without task evaluation.
