# Evaluation-Driven Improvement

## Contents

- Choose validation depth
- Define the evaluation target
- Build representative cases
- Choose graders
- Run controlled iterations
- Report results

## Choose validation depth

Choose the smallest validation that supports the decision:

| Situation | Validation |
| --- | --- |
| Clear, small instruction or wording change | Inspect consistency and walk through the decisive scenarios |
| A conclusion depends on unresolved material behavior | Run the smallest actual case that resolves that uncertainty |
| Quantified gains, model migration, or reliability comparison | Use a controlled evaluation matched to the claim and affected configurations |

This choice governs the sections below. They are methods to select from, not a checklist for every edit. Static inspection is not a model run. Choosing not to claim an improvement does not remove the need to resolve material behavioral uncertainty. Bound conclusions to the evidence obtained; do not imply untested configurations passed.

## Define the evaluation target

Separate three questions:

1. **Activation:** Did the correct Skill, prompt route, or tool become available?
2. **Behavior:** Did the agent choose valid actions and respect boundaries?
3. **Outcome:** Is the final artifact or external state correct?

Outcome is primary. Use traces to diagnose why an outcome passed or failed, not as a substitute for outcome validation.

For a controlled comparison, record a baseline and an acceptance threshold before iterating. Choose only metrics relevant to the decision:

- task success and required evidence completeness;
- activation precision/recall;
- valid tool selection and argument rate;
- abstention when no tool is appropriate;
- unauthorized or destructive action rate;
- unnecessary questions, approvals, calls, and retries;
- total tokens, latency, and cost.

When comparing model-routing cost, measure expected cost per accepted outcome rather than price per token alone. Include the relevant prompt/output tokens, handoff and integration work, retries, tool calls, latency, human review, and failed outcomes.

## Build representative cases

Start from real requests, requirements, failures, and traces. Select cases that exercise the affected decisions or boundaries:

- ordinary successful use;
- incomplete or ambiguous input;
- edge and failure recovery;
- near-miss cases where the behavior must not trigger;
- overlapping tools or instructions;
- unauthorized, adversarial, or untrusted inputs when relevant.

For a routing or boundary change, include a positive case and a close near-miss. Easy unrelated negatives do not test that boundary. For controlled optimization, reserve held-out cases when repeated tuning could overfit the examples. A small, clear edit does not require a full case bank.

The files in `evals/` provide activation and behavior case formats for this skill. They are fixtures, not evidence of model performance until a host runs and records them.

## Choose graders

Prefer deterministic graders for detectable outcomes:

- schema validation;
- exact required fields;
- unit/integration tests;
- state and permission checks;
- file or database assertions;
- latency, call, and token counters.

When semantic quality needs systematic grading, use rubric-based model graders calibrated against human review. A focused manual check may suffice for a clear, small edit. Allow `unknown` when evidence is insufficient. Avoid graders that demand one exact tool-call sequence if several paths can produce the correct result.

## Run controlled iterations

Use this procedure when the chosen validation depth calls for a controlled comparison:

1. Run the baseline on the same environment and model configuration.
2. Change one coherent instruction, example group, tool description, or schema boundary.
3. Use enough trials to assess the nondeterminism material to the claim.
4. Inspect outcomes and the traces, tool errors, or resource metrics relevant to the decision.
5. Revert changes that do not improve the target metric or that create material regressions.
6. Confirm the result on the held-out cases and affected configurations needed to support the conclusion. Expand to other models/providers only when the claimed scope requires it.

When adapting one product across model tiers, select the configurations needed to answer the migration or cost question. Possible comparisons include:

| Configuration | Purpose |
| --- | --- |
| Target model + lean core | Establish the minimum baseline |
| Target model + one scaffold layer | Attribute the value of decomposition, examples, recovery, or checks |
| Stronger model + lean core | Detect legacy over-prompting and establish an escalation baseline |
| Cheaper model + best validated profile | Measure cost-adjusted production viability |

The matrix is optional; do not run every row by default. Stop adding layers when held-out task success stops improving, regressions appear, or the added tokens and retries erase the model's price advantage. If a prompt requires many brittle workarounds, compare the relevant alternatives, such as deterministic orchestration, retrieval, fine-tuning or distillation, and model escalation.

A single actual case can resolve a narrow question; it does not establish a general reliability or performance improvement. Do not combine model, prompt, tool, and grader changes in one comparison unless the evaluation explicitly studies the whole bundle.

## Report results

State the result, validation performed, and any evidence gap affecting the decision. Distinguish inspection, an actual case, and a measured comparison. For controlled comparisons, include the relevant details:

- model/provider and relevant settings;
- dataset version, case count, and trial count;
- baseline and candidate metrics;
- regressions and confidence limits when available;
- which cases were held out;
- known harness limitations;
- whether the result is measured, inferred, or still hypothetical.
