# Prompt Design

## Contents

- Minimal sufficient context
- Prompt components
- Instruction placement
- Constraints and examples
- Review procedure
- Anti-patterns

## Minimal sufficient context

Assume the target model understands common language, programming concepts, and routine reasoning only when its observed behavior supports that assumption. Supply context that changes the answer:

- the outcome and audience;
- non-obvious domain facts;
- hard constraints and approval boundaries;
- available tools and trusted data sources;
- required evidence or output structure;
- known failure cases.

Do not add explanations merely because they are true. A paragraph earns its place when removing it causes a measurable regression, violates a product requirement, or leaves a material ambiguity. For model-specific scaffold selection, read [model-adaptation.md](model-adaptation.md).

Prefer outcome-focused instructions over prescribing a complete internal strategy. Prescribe steps only when order is a real dependency, the workflow is fragile, or the path itself must be audited.

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

State each rule once. Repeat only when an evaluation demonstrates that deliberate reinforcement fixes a recurring failure without creating regressions.

## Constraints and examples

Write constraints around real failure modes:

- Replace “be careful” with the action, trigger, and observable boundary.
- Explain the consequence when it helps generalization.
- Give a recovery path when a constraint can fail.
- Avoid large collections of `NEVER` rules. Move detectable prohibitions into code.

Use examples when they define a format, resolve an ambiguity, or repair a measured gap. Keep examples consistent and minimal for the selected model profile. For a model that misses implicit boundaries, add one positive and one near-miss example before adding a large example bank. More examples do not necessarily help smaller models more.

Do not assume XML, Markdown, JSON, or another delimiter is universally optimal. Choose a clear, consistent structure and compare alternatives when format materially affects performance.

Do not request exposed chain-of-thought. Ask for concise rationale, cited evidence, intermediate artifacts, checks performed, or a structured decision record when observability is needed.

## Review procedure

1. Restate the expected outcome in observable terms.
2. Mark every instruction as objective, context, boundary, procedure, style, or output.
3. Find duplicates, conflicts, vague qualifiers, hidden defaults, and platform assumptions.
4. Identify instructions that belong in a tool, schema, validator, permission layer, or reference.
5. Delete information the target model already knows unless it repairs a measured failure.
6. Select a lean or scaffolded profile from model-specific evidence.
7. Produce the smallest coherent revision for that profile.
8. Replay the same evaluation cases and inspect both final outcomes and traces.

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
