# Model-Adaptive Scaffolding

## Principle

Optimize for reliable accepted outcomes, not minimum prompt length or maximum instruction count. A strong reasoning model may perform best with a compact outcome contract. A less reliable instruction follower may need explicit decomposition, examples, recovery paths, and checks. Neither profile is a moral or universal best practice.

Do not infer the correct profile from provider, parameter count, benchmark rank, or price alone. Record the exact model version, reasoning mode or effort, serving template, active tools, and observed failures.

## Keep a stable core

Maintain one provider-neutral core containing only:

- the observable objective and audience;
- non-negotiable product and authorization boundaries;
- trusted capabilities and data sources;
- success evidence and output contract;
- runtime-enforced invariants referenced by the model.

Put model-specific assistance in a separate adapter block or prompt variant. This keeps product policy consistent while letting scaffolding evolve or disappear during model migrations.

## Scaffold ladder

Begin at level 0 for each new model or major version. Add one layer at a time only when representative traces show the corresponding failure.

| Level | Add | Use when traces show | Main risk |
| --- | --- | --- | --- |
| 0. Lean contract | Objective, hard boundaries, evidence, output | Model succeeds without procedural help | Missing implicit domain knowledge |
| 1. Explicit semantics | Definitions, decision boundary, consequence | Ambiguous terms or wrong routing | Redundant prose |
| 2. Decomposition | Short ordered phases and stopping conditions | Skipped dependencies or lost constraints | Suppressing a better strategy |
| 3. Boundary examples | One positive plus one near-miss or negative | Overgeneralization or format drift | Anchoring and example imitation |
| 4. Recovery guidance | Known failure signal, retry rule, workaround | Repeated dead ends or invalid tool use | Encoding stale incidents |
| 5. Verification gates | Observable checklist, validator, bounded retry | Premature completion or silent errors | Loops, latency, and over-verification |

Prefer schema constraints, deterministic validators, state machines, or orchestrator-owned retries when a failure is machine-detectable. Prompt repetition is a last-mile adapter, not an enforcement mechanism.

## Profile heuristics

### Strong reasoning and instruction following

- Start outcome-first and concise.
- Leave strategy open unless order is a true dependency.
- Remove legacy examples, reminders, and explicit verification rituals one group at a time.
- Preserve product-specific rules, unusual domain facts, and required output structure.
- Use effort or reasoning controls before adding hand-written chain-of-thought procedures when the provider exposes them.

### Less reliable or cost-optimized model

- Translate implicit expectations into short, concrete criteria.
- Break fragile workflows into numbered phases with inputs, completion signals, and bounded recovery.
- Add a positive example for the desired shape and a near-miss for a frequently confused boundary.
- State validation as observable checks; do not request hidden reasoning transcripts.
- Repeat a critical instruction only if ablation shows that reinforcement improves held-out behavior without new false positives.

### Prompting has reached its limit

Stop adding prose and change the system when:

- the model still misses simple constraints after targeted scaffolding;
- the prompt contains many incident-specific exceptions or contradictory workarounds;
- retries and review erase the cheaper model's cost advantage;
- the task depends on knowledge the model lacks rather than instructions it misunderstands; or
- errors are detectable and better handled deterministically.

Options include narrowing the task, splitting it into orchestrated calls, retrieving domain context, adding validators, fine-tuning or distillation, or escalating only difficult cases to a stronger model.

## Evaluate cost-adjusted reliability

For every candidate profile, run the same representative and held-out cases with multiple trials. Record:

- accepted outcome rate and decomposed constraint pass rate;
- tool selection, argument validity, recovery, and unauthorized-action rates;
- prompt, reasoning, output, and retry tokens;
- latency, tool calls, human review, and escalation rate;
- failures severe enough to dominate average cost.

Use an application-specific expected-cost model such as:

`expected cost per accepted outcome = (inference + tools + retries + review + failure loss) / accepted outcomes`

A model priced at one percent per token is not one percent of the system cost if it needs long contexts, repeated attempts, or frequent review. Conversely, a longer prompt is justified when it preserves the value model's price advantage while meeting the acceptance threshold.

## Migration procedure

1. Freeze representative cases and the current accepted-output baseline.
2. Run the old prompt unchanged on the new model.
3. Run a lean core variant to detect obsolete scaffolding.
4. Add scaffold levels independently; do not combine all legacy instructions at once.
5. Compare task success, regressions, and expected cost on held-out cases.
6. Ship a versioned core plus model adapter, with routing and fallback criteria.

Do not call one prompt “the best.” Name the supported model, configuration, workload, evaluation date, and evidence.
