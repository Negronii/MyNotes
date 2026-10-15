# Focused Patterns

Use a pattern only after identifying the failure it addresses.

## Contrastive boundary

Use when a rule is overgeneralized.

```xml
<example kind="positive">
Input: [case where behavior should occur]
Output: [minimum correct behavior]
</example>
<example kind="near-miss">
Input: [similar case where behavior must not occur]
Output: [correct abstention or alternative]
</example>
```

Keep both examples structurally consistent. Explain the differentiating feature, not hidden reasoning.

## Tool disambiguation

Use when two tools overlap.

```text
Use search_records when the user needs to discover records from partial details.
Use get_record when a stable record_id is already known.
Do not guess record_id; search first when it is missing.
```

Prefer fixing names or scope over adding a large routing table.

## Failure with recovery

Use for errors the model can correct.

```json
{
  "error": "invalid_date_range",
  "message": "start_date must be on or before end_date",
  "retryable": true,
  "invalid_fields": ["start_date", "end_date"],
  "example": {"start_date": "2026-08-01", "end_date": "2026-08-05"}
}
```

Never mark an ambiguous non-idempotent write as safely retryable.

## Detectable completion gate

Use when completion depends on persisted evidence.

```text
Trigger: an artifact is ready for external publication.
State: publication_review.status == "approved".
Check: a validator exits nonzero until the state exists and is valid.
Action: stop before publication when the check fails.
```

The prompt explains the gate; the runtime or validator enforces it.

## Bounded loop

Use for recoverable iterative work.

```text
Attempt the operation.
If a transient and idempotent failure occurs, retry at most 2 times.
If validation fails, change the relevant input and validate again.
If evidence does not support a new attempt, stop and report the blocker.
```

## Structured handoff

Use when another process must resume work.

```json
{
  "objective": "...",
  "success_criteria": ["..."],
  "completed": ["..."],
  "pending": ["..."],
  "decisions": [{"choice": "...", "reason": "..."}],
  "artifacts": [{"path": "...", "verification": "..."}],
  "blockers": ["..."]
}
```

Keep the schema stable when downstream automation parses it.
