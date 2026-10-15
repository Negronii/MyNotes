# Evaluation-Driven Improvement

## Contents

- Define the evaluation target
- Build representative cases
- Choose graders
- Run controlled iterations
- Report results

## Define the evaluation target

Separate three questions:

1. **Activation:** Did the correct Skill, prompt route, or tool become available?
2. **Behavior:** Did the agent choose valid actions and respect boundaries?
3. **Outcome:** Is the final artifact or external state correct?

Outcome is primary. Use traces to diagnose why an outcome passed or failed, not as a substitute for outcome validation.

Before changing a prompt or tool, record a baseline and an acceptance threshold. Suitable metrics include:

- task success and required evidence completeness;
- activation precision/recall;
- valid tool selection and argument rate;
- abstention when no tool is appropriate;
- unauthorized or destructive action rate;
- unnecessary questions, approvals, calls, and retries;
- total tokens, latency, and cost.

For model-routing decisions, measure expected cost per accepted outcome rather than price per token alone. Include prompt and output tokens, retries, tool calls, latency penalties, human review, and the cost of failed or unsafe outcomes.

## Build representative cases

Start from real requests, failures, and traces. Cover:

- ordinary successful use;
- incomplete or ambiguous input;
- edge and failure recovery;
- near-miss cases where the behavior must not trigger;
- overlapping tools or instructions;
- unauthorized, adversarial, or untrusted inputs when relevant.

Use balanced positive and negative cases. Easy unrelated negatives do not test a boundary. Preserve a held-out validation set when optimizing wording, examples, or descriptions.

The files in `evals/` provide activation and behavior case formats for this skill. They are fixtures, not evidence of model performance until a host runs and records them.

## Choose graders

Prefer deterministic graders for detectable outcomes:

- schema validation;
- exact required fields;
- unit/integration tests;
- state and permission checks;
- file or database assertions;
- latency, call, and token counters.

Use rubric-based model graders for semantic quality that code cannot capture, and calibrate them against human review. Allow `unknown` when evidence is insufficient. Avoid graders that demand one exact tool-call sequence if several paths can produce the correct result.

## Run controlled iterations

1. Run the baseline on the same environment and model configuration.
2. Change one coherent instruction, example group, tool description, or schema boundary.
3. Run several trials for nondeterministic cases.
4. Inspect outcomes, traces, tool errors, and resource metrics.
5. Revert changes that do not improve the target metric or that create material regressions.
6. Confirm the result on held-out cases and every supported model/provider that matters.

When adapting one product across model tiers, compare a small matrix rather than assuming one universal prompt:

| Configuration | Purpose |
| --- | --- |
| Target model + lean core | Establish the minimum baseline |
| Target model + one scaffold layer | Attribute the value of decomposition, examples, recovery, or checks |
| Stronger model + lean core | Detect legacy over-prompting and establish an escalation baseline |
| Cheaper model + best validated profile | Measure cost-adjusted production viability |

Stop adding layers when held-out task success stops improving, regressions appear, or the added tokens and retries erase the model's price advantage. If a prompt requires many brittle workarounds, compare deterministic orchestration, retrieval, fine-tuning or distillation, and model escalation.

Do not quote a single successful run as proof. Do not combine model, prompt, tool, and grader changes in one comparison unless the evaluation explicitly studies the whole bundle.

## Report results

Include:

- model/provider and relevant settings;
- dataset version, case count, and trial count;
- baseline and candidate metrics;
- regressions and confidence limits when available;
- which cases were held out;
- known harness limitations;
- whether the result is measured, inferred, or still hypothetical.
