---
name: design-agent-prompts-tools
description: Design, audit, and improve standalone system or developer prompts, tool descriptions, JSON parameter schemas, and tool-result contracts for LLM agents. Use when a user asks to write or review agent instructions, adapt prompt scaffolding to a target model's reasoning or instruction-following capability and cost profile, reduce conflicts or bloat, improve tool selection or arguments, define structured outputs, or diagnose prompt/tool behavior from traces. Do not use for general Skill architecture or packaging, model benchmarking without a prompt/tool change, or hard security enforcement that belongs in runtime code.
---

# Agent Prompt & Tool Design

Design the minimum sufficient prompt and tool contract for the target model and workload. That may be a lean outcome contract for a strong reasoning model or explicit scaffolding for a less reliable model. Treat every recommendation as a hypothesis until representative evaluations support it.

## Workflow

1. **Scope the artifact.** Identify whether the task concerns a prompt, one or more tools, tool results, or their orchestration. Record the exact provider/model, reasoning mode, available capabilities, side effects, approval boundaries, required output, cost or latency target, and known failures. Proceed with explicit assumptions when missing details are low-risk.
2. **Define success before editing.** Prefer existing traces, user reports, and production failures. Otherwise create a compact baseline with a normal case, an edge case, and a near-miss where the behavior must not occur.
3. **Audit ownership and signal.** Find contradictions, repeated rules, ambiguous terms, overlapping tool scopes, prose that should be schema or runtime enforcement, irrelevant context, volatile facts, and unsupported universal claims.
4. **Select a model profile.** Start lean, then add the smallest layer that repairs an observed failure: definitions, decomposition, examples, recovery guidance, or verification gates. Do not infer the profile from price, parameter count, or provider name alone.
5. **Make the minimum sufficient change.** State each rule once at the narrowest effective layer unless measured reinforcement is necessary. Preserve model judgment for context-dependent decisions. Use schema, code, permissions, or state checks for detectable invariants.
6. **Evaluate the change.** Compare the same cases before and after on every supported model/profile. Use multiple trials for nondeterministic behavior and keep held-out cases for material changes. Measure task success first, then tool errors, unnecessary calls or approvals, retries, tokens, latency, and total expected cost.
7. **Report evidence honestly.** Separate confirmed findings, risks, and unknowns. Distinguish measured improvements from unvalidated recommendations. Never claim cross-model or cross-provider generality without evidence.

## Resource routing

Read only the references needed for the current task:

- For system/developer prompts, instruction placement, examples, or prompt review, read [references/prompt-design.md](references/prompt-design.md).
- When comparing frontier and value models, migrating a legacy prompt, or deciding how much procedure, examples, recovery guidance, repetition, or verification to add, read [references/model-adaptation.md](references/model-adaptation.md).
- For tool names, selection boundaries, parameters, outputs, errors, or annotations, read [references/tool-contracts.md](references/tool-contracts.md).
- For context budgets, caching, compaction, autonomy, prompt injection, or guardrails, read [references/context-security.md](references/context-security.md).
- Before recommending a production change or designing tests, read [references/evaluation.md](references/evaluation.md).
- For reusable solution shapes after identifying a specific failure class, read [references/patterns.md](references/patterns.md).
- When the user asks for a draft or concrete starting point, read [references/templates.md](references/templates.md).
- For provider-specific behavior, current limits, or syntax, read [references/provider-notes.md](references/provider-notes.md) and re-check the linked official documentation when freshness matters.

Do not load every reference by default.

## Decision boundaries

- For review, explanation, diagnosis, or planning requests, inspect and report without mutating the user's artifacts.
- For explicit write, change, fix, or optimization requests, make scoped local changes and run relevant non-destructive checks.
- Ask before external writes, destructive actions, expensive evaluation runs, or choices that materially change product behavior.
- Do not encode security guarantees solely in natural language. Prompts may guide behavior; authorization, validation, sandboxing, and confirmation must enforce high-impact guarantees.
- Do not prescribe hidden reasoning or require chain-of-thought disclosure. Specify observable work, evidence, and output instead.
- Do not optimize prompt length in isolation. Optimize reliable task completion under the product's quality, latency, and total-cost constraints.

## Review output

For audits, return:

1. the desired outcome and current failure evidence;
2. confirmed findings, risks, and unknowns;
3. the smallest recommended change, with each change mapped to a failure or requirement;
4. verification cases, metrics, and remaining manual decisions.

For edits, also list changed files and validation results.

## Completion criteria

Finish only when:

- every retained instruction has a clear owner and purpose;
- repeated or conflicting rules are removed;
- detectable constraints are enforced outside prose where feasible;
- examples and provider-specific claims are justified and routed on demand;
- the selected scaffold level is supported by failures or model-specific evaluations;
- evaluation evidence exists, or the lack of validation is explicit; and
- the final answer satisfies the user's requested format without inventing facts.

After changing this skill itself, run:

```bash
python3 scripts/validate_skill.py .
```
