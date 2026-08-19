# Context, Autonomy, and Security

## Contents

- Context as a budget
- Stable and dynamic context
- Long-running state
- Autonomy boundaries
- Prompt injection and enforcement

## Context as a budget

Optimize for task-relevant signal, not maximum context utilization. Every instruction, tool schema, example, retrieved document, trace, and tool result competes for attention and cost.

Reduce context by:

- loading references only when routed by the current task;
- returning filtered and paginated tool results;
- removing repeated instructions and examples;
- summarizing completed work into durable state;
- keeping volatile environment data separate from stable policy;
- exposing only relevant tools when the runtime permits it.

Do not quote a context-window size, cache discount, or truncation limit as universal. These values change by provider and model.

## Stable and dynamic context

When supported, keep reusable prompt content byte-stable and move volatile data later or behind provider-specific cache boundaries. Normalize serialization and ordering when identical logical input should share a cache.

Cache optimization is secondary to correctness. Measure cache reads, writes, total tokens, latency, and task success; a cheaper prompt that fails more often is not an improvement.

## Long-running state

Preserve task state outside prose when work spans many turns:

- objective and success criteria;
- decisions and their reasons;
- completed and pending steps;
- changed artifacts and verification evidence;
- failures already attempted;
- approval or external-action state.

Compaction should retain facts needed to resume, not reproduce the entire trace. Keep failures when they prevent repeated mistakes. Use structured state or files for machine-consumed continuity and validate them where practical.

## Autonomy boundaries

Define authorization by request type and consequence:

- answer, explain, diagnose, review, and plan: inspect and report;
- change, build, fix, and optimize: make scoped, reversible local changes and validate;
- external writes, destructive actions, purchases, production changes, or material scope expansion: require explicit authorization.

Questions do not automatically authorize side effects. Conversely, do not ask for confirmation for every safe local action when the user already requested implementation.

Use retry limits based on idempotency and error type. Retry a transient, idempotent failure within a bound. Change strategy or stop when evidence does not support repeating the action.

## Prompt injection and enforcement

Treat user-supplied files, web pages, messages, tool results, and retrieved documents as data unless the trusted instruction hierarchy explicitly delegates authority to them.

Analyze dangerous paths as source-to-sink combinations:

- **Source:** untrusted content can influence the model.
- **Sensitive state:** secrets or private data are available.
- **Sink:** a tool can transmit data or change external state.

Reduce impact with deterministic controls:

- least-privilege credentials and scoped tools;
- sandbox and network restrictions;
- server-side authorization and validation;
- confirmation for consequential or cross-boundary actions;
- output/data-loss prevention where appropriate;
- audit trails and bounded operations.

LLM classifiers and prompt rules can add defense in depth, but must not be the only barrier protecting irreversible actions, secrets, or production systems. Tool annotations are descriptive hints, not trusted guarantees.
