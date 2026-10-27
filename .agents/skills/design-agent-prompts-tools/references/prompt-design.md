# Prompt Design

## Contents

- Minimal sufficient context
- Prompt components
- Instruction placement
- Constraints and examples
- Review procedure
- Anti-patterns

## Minimal sufficient context

Supply non-obvious context that changes the answer or execution:

- the outcome and audience;
- non-obvious domain facts;
- hard constraints and approval boundaries;
- available tools and trusted data sources;
- required evidence or output structure;
- known failure cases.

Retain a paragraph when it serves a requirement, changes a decision or action, resolves a material ambiguity, or addresses a relevant reported failure. Omit explanations of common knowledge unless the task needs them. For model-specific scaffold selection, read [model-adaptation.md](model-adaptation.md).

Prefer outcome-focused instructions. Prescribe steps only for a real ordering dependency or required workflow; otherwise let the task owner choose the method.

## Prompt components

Use only the components the task needs:

1. **Objective:** the observable result.
2. **Context:** facts the model cannot safely infer.
3. **Capabilities:** tools, data, and execution environment.
4. **Boundaries:** prohibited side effects, approval points, and scope.
5. **Success criteria:** evidence or state that proves completion.
6. **Output contract:** structure required by the consumer.
7. **Dynamic context:** current user, environment, state, and request.

Keep stable instructions before volatile runtime context when the provider's caching model benefits from a stable prefix. Treat cache behavior as provider-specific and verify current documentation.

## Instruction placement

Place a rule at the narrowest layer that owns it:

| Rule | Preferred owner |
| --- | --- |
| Product-wide behavior | System/developer prompt |
| One tool's selection or parameters | Tool description/schema |
| Deterministic input validity | Schema or runtime validator |
| Authorization or destructive-action policy | Runtime permission layer |
| One request's preference | User prompt/runtime context |
| Long domain detail | Retrieved reference |

State each rule once at its owning layer. If repetition is proposed to fix recurring behavior, validate that reinforcement rather than treating it as a default.

## Constraints and examples

Write constraints around real failure modes:

- Replace “be careful” with the action, trigger, and observable boundary.
- Explain the consequence when it helps generalization.
- Give a recovery path when a constraint can fail.
- Avoid large collections of `NEVER` rules. Move detectable prohibitions into code.

Use examples when they define a format, resolve an ambiguity, or address a relevant failure. Keep them consistent and minimal. For a model that misses implicit boundaries, try a positive and a near-miss example before adding a large example bank. More examples do not necessarily help smaller models more.

State the desired action or result directly. Explain a limitation, distinction, or counterexample when it affects the current decision; avoid rebutting an interpretation the user has not raised and that the task does not imply.

Do not assume XML, Markdown, JSON, or another delimiter is universally optimal. Choose a clear, consistent structure and compare alternatives when format materially affects performance.

Do not request exposed chain-of-thought. Ask for concise rationale, cited evidence, intermediate artifacts, checks performed, or a structured decision record when observability is needed.

## Review procedure

Scale the review to the artifact and uncertainty:

- Identify the observable outcome, necessary boundaries, and relevant failure evidence.
- Remove duplicates, conflicts, vague defaults, irrelevant context, and requirements owned by another layer.
- Keep only the guidance needed for the task. Model-profile selection is relevant when adapting models or resolving model-specific behavior.
- Make the smallest coherent revision. For clear, small edits, inspect consistency and decisive scenarios. If a conclusion depends on unresolved material behavior, run the smallest actual case that resolves it. For quantified gains, model migrations, or reliability comparisons, follow [evaluation.md](evaluation.md).
- Report static review, actual runs, and measured comparisons accurately.

## Anti-patterns

- Universal numeric claims without a named evaluation.
- “Best practice” statements without provider/model/task scope.
- Long role-play personas that do not change observable behavior.
- Repeating the same autonomy rule in several sections.
- Encoding API limits, prices, or model behavior as timeless facts.
- Forcing a plan or clarification for every task regardless of risk.
- Grading exact tool-call order when several valid paths exist.
- Assuming frontier-model minimalism or legacy-model verbosity transfers to every model family.
- Adding examples until the prompt resembles a training set.
- Using prompt prose to compensate indefinitely for a model that needs task decomposition, deterministic checks, retrieval, fine-tuning, or escalation.
