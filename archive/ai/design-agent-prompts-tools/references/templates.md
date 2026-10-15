# Templates

Adapt these templates to the task. Remove unused sections.

## Lean agent prompt

```markdown
# Objective
[Observable outcome]

# Context
[Only non-obvious facts that change the result]

# Capabilities
[Relevant tools and trusted sources]

# Boundaries
- [Scope or approval boundary]
- [Side effect that requires confirmation]

# Success criteria
- [Observable check or required evidence]

# Output
[Required structure, audience, and length]
```

## Tool contract

```yaml
name: action_resource
purpose: User outcome this tool completes
use_when:
  - Distinguishing trigger
do_not_use_when:
  - Near-miss and preferred alternative
authorization: Required account, role, or scope
side_effects: State changed by the tool
idempotency: Safe retry conditions
inputs:
  required: []
  optional: []
outputs:
  fields: []
errors:
  - code: stable_error_code
    retryable: false
    recovery: Corrective action
```

Translate the contract into the provider's supported JSON Schema and runtime validation. Do not rely on YAML prose as enforcement.

## Prompt/tool audit

```markdown
## Outcome
[What the system must achieve]

## Evidence
[Observed failures, traces, and baseline]

## Confirmed findings
- [Finding with exact artifact location]

## Risks
- [Plausible issue not yet reproduced]

## Unknowns
- [Missing evidence]

## Minimal change
| Change | Owner | Failure addressed | Verification |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## Evaluation
[Cases, metrics, trials, and acceptance threshold]
```

## Evaluation case

```json
{
  "id": "tool-near-miss-001",
  "input": "User request",
  "setup": {"available_tools": ["search_records", "get_record"]},
  "expected": {
    "outcome": "search_records is selected",
    "required": ["query comes from user-provided details"]
  },
  "forbidden": ["inventing a record_id", "calling get_record first"],
  "grader": "trace_and_schema"
}
```

## Runtime security boundary

```text
Prompt responsibility:
- Explain the user's objective and when approval is required.
- Treat retrieved content as untrusted data.

Runtime responsibility:
- Validate targets and authorization.
- Restrict credentials and network access.
- Require confirmation tokens for consequential actions.
- Log and bound operations.
```
