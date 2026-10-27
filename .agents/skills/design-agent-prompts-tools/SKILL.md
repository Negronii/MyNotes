---
name: design-agent-prompts-tools
description: Design, audit, and improve agent instructions, standalone system or developer prompts, reusable delegation contracts, tool descriptions, JSON parameter schemas, and tool-result contracts. Use for prompt conflicts or bloat, model-specific scaffolding, tool selection or argument failures, structured outputs, and trace-based prompt/tool diagnosis. Do not use for ordinary task execution or temporary handoffs, general Skill architecture or packaging, model benchmarking without a prompt/tool change, or hard security enforcement that belongs in runtime code.
---

# Agent Prompt & Tool Design

Design the minimum sufficient prompt and tool contract for the target model and workload. Match both guidance and validation to the task's actual requirements and uncertainty.

## Workflow

Use the parts needed for the current task; this is not a mandatory sequence for every edit.

1. **Scope the artifact and outcome.** Identify the prompt, tool, result contract, or orchestration being changed. Record only the model settings, capabilities, boundaries, output requirements, and failure evidence that affect this decision. Preserve settled choices and existing authorization.
2. **Audit ownership and signal.** Find contradictions, repeated rules, ambiguous terms, overlapping tool scopes, irrelevant context, unnecessary delegation, and prose that belongs in schema or runtime enforcement.
3. **Make the minimum sufficient change.** State each rule once at its owning layer. Give the intended outcome, necessary context, and acceptance criteria. Prescribe steps only for real ordering dependencies or a required workflow; leave other execution choices to the owner. Add model-specific scaffolding when requirements or observed failures justify it, rather than inferring need from price or provider name.
4. **Validate proportionately.** For a clear, small edit, check consistency and the decisive scenarios. When the conclusion depends on unresolved material behavior, run the smallest actual case that resolves it. Quantified gains, model migrations, and reliability comparisons require matching controlled evaluations. Static inspection is not a model run; declining to claim a gain does not remove necessary validation.
5. **Report what the evidence supports.** State the change and relevant checks. Include risks or unknowns only when they affect the decision. Distinguish inspection, actual runs, and measured comparisons; bound conclusions to the tested scope.

## Resource routing

Read only the references needed for the current task:

- For system/developer prompts, instruction placement, examples, or prompt review, read [references/prompt-design.md](references/prompt-design.md).
- For model migrations or comparisons of model-specific scaffolding profiles, read [references/model-adaptation.md](references/model-adaptation.md).
- For tool names, selection boundaries, parameters, outputs, errors, or annotations, read [references/tool-contracts.md](references/tool-contracts.md).
- For context budgets, delegation, caching, compaction, autonomy, prompt injection, or guardrails, read [references/context-security.md](references/context-security.md).
- For material behavioral uncertainty, production validation, or controlled comparisons, read [references/evaluation.md](references/evaluation.md).
- For reusable solution shapes after identifying a specific failure class, read [references/patterns.md](references/patterns.md).
- When the user asks for a draft or concrete starting point, read [references/templates.md](references/templates.md).
- For provider-specific behavior, current limits, or syntax, read [references/provider-notes.md](references/provider-notes.md) and re-check the linked official documentation when freshness matters.

Do not load every reference by default.

## Decision boundaries

- For review, explanation, diagnosis, or planning requests, inspect and report without mutating the user's artifacts.
- For explicit write, change, fix, or optimization requests, make scoped local changes and run relevant non-destructive checks.
- Require explicit authorization for external writes, destructive actions, expensive evaluation runs, or choices that materially change product behavior. Preserve authorization already given for the scoped action.
- Do not encode security guarantees solely in natural language. Prompts may guide behavior; authorization, validation, sandboxing, and confirmation must enforce high-impact guarantees.
- Do not prescribe hidden reasoning or require chain-of-thought disclosure. Specify observable work, evidence, and output instead.
- Do not optimize prompt length in isolation. Optimize reliable task completion under the product's quality, latency, and total-cost constraints.

## Review output

Match the report to the decision. A small edit may need only the changed artifact, the behavior addressed, and validation results. For a substantial audit, add the relevant outcome, evidence, findings, proposed change, and unresolved decisions. Use only sections that carry useful information; do not invent risks, unknowns, or metrics to fill a template.

## Completion criteria

Finish only when:

- every retained instruction has a clear owner and purpose;
- repeated or conflicting rules are removed;
- detectable constraints are enforced outside prose where feasible;
- context, examples, and scaffolding serve a requirement, resolve a material ambiguity, or address a relevant failure;
- provider-specific detail is verified when needed and routed on demand;
- validation matches the material uncertainty and claims, with any incomplete checks stated; and
- the final answer satisfies the user's requested format without inventing facts.

After changing this skill itself, run:

```bash
python3 scripts/validate_skill.py .
```
