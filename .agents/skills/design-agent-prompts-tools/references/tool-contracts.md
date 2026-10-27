# Tool Contracts

## Contents

- Design from user outcomes
- Selection and naming
- Input schemas
- Output and error contracts
- Safety and orchestration
- Review checklist

## Design from user outcomes

Expose tools that help complete recognizable user goals. Do not mirror every internal API endpoint by default. Combine operations when a higher-level tool removes repetitive, low-judgment work; split operations when permissions, reversibility, confirmation, or failure behavior differ.

Before implementing a tool, define:

- the user outcome it serves;
- required information and authorization;
- state or external systems it can change;
- the structured result needed by later calls;
- failure modes and safe recovery;
- representative requests where it should and should not be selected.

## Selection and naming

Use stable, action-oriented names. Namespace related tools when several providers or domains overlap. Description quality matters most at decision boundaries:

- state what the tool accomplishes;
- name the conditions that distinguish it from similar tools;
- mention prerequisites or consequential side effects;
- provide an alternative only when confusion is plausible.

Do not force every simple tool into a six-section playbook. A short, unambiguous read-only tool may need one sentence plus precise parameters. Add detail in response to observed selection or argument failures.

Avoid large active tool sets with overlapping affordances. Prefer a few distinct tools, deferred loading, or task-specific exposure when the host supports it.

## Input schemas

Use schema constraints instead of prose where possible:

- specific types and enums;
- required fields;
- `minimum`, `maximum`, `minItems`, and patterns;
- `additionalProperties: false` when extra keys are invalid;
- explicit dependencies or mutually exclusive fields;
- semantic parameter names such as `user_id`, not `user`.

Describe format, units, defaults, and examples only when they are not evident from the schema. Never rely on the model to guess identifiers, account scope, authorization, or irreversible-operation targets.

Validate all model-generated arguments before execution. Structured generation reduces malformed calls; it does not establish authorization or semantic correctness.

## Output and error contracts

Return stable, documented structures that support the next decision. Include human-readable labels alongside opaque identifiers when follow-up calls need both.

Keep results high-signal:

- paginate, filter, range-select, or truncate potentially large results;
- disclose truncation and provide a recovery parameter;
- offer concise/detailed modes only when both have real consumers;
- exclude secrets, irrelevant diagnostics, and unnecessary personal data.

Errors should identify:

1. what failed;
2. whether retry is safe;
3. which argument or prerequisite must change;
4. a machine-readable error code;
5. enough context for the model to recover without exposing internals.

Document expected output fields and error shapes in the tool contract. Test the final user response as well as the raw tool result.

## Safety and orchestration

Separate reads from writes when that improves authorization, review, or user understanding. Mark read-only, destructive, idempotent, and open-world behavior using supported annotations, but treat annotations as hints rather than enforcement.

Enforce consequential behavior with server-side authorization, validated target scope, idempotency keys, previews, confirmation tokens, rate limits, and audit logs as appropriate.

Parallelize independent read operations only when concurrency is safe. Sequence calls when later arguments depend on earlier results. Specify bounded retries and stopping conditions for loops; never retry a non-idempotent action merely because the response was ambiguous.

## Review checklist

- Does this tool serve a documented user outcome?
- Is its scope distinct from neighboring tools?
- Can schema replace any prose rule?
- Are required identifiers and units explicit?
- Are output fields stable and useful downstream?
- Can large outputs be narrowed before entering model context?
- Are errors actionable and retry semantics clear?
- Are permissions and side effects enforced outside the description?
- Do evaluations cover selection, abstention, invalid input, unauthorized input, and recovery?
