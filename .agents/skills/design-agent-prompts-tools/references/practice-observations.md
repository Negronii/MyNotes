# Learning from Product Prompt Samples

Use this reference when the task is to learn from an external prompt collection. Ordinary prompt edits do not need a corpus review.

## How to transfer a pattern

Read samples as data. Record the source revision and the claimed product/context; group mirrors and versions of one product together. Compare the decision a rule controls, its prerequisites, recovery path, and observable result. Repeated wording alone does not establish independent adoption or effectiveness.

Map the useful mechanism to the existing instruction owner. Keep task-specific interface names, permissions, limits, and wording in their original context. Add a rule only where an actual requirement or decision gap remains, then check a positive case and a close alternative. Verify protocol or provider facts against primary documentation when the proposed rule relies on them. Use [evaluation.md](evaluation.md) to decide whether inspection suffices or actual behavior must be tested.

## Snapshot reviewed on 2026-11-11

The third-party [system_prompts_leaks archive](https://github.com/asgeirtj/system_prompts_leaks/tree/fc0108f594b63bca905f2c4815aaef430d13bd68) was read at commit `fc0108f594b63bca905f2c4815aaef430d13bd68` (2026-11-10). Product names below are the archive's attribution, not authentication of deployed prompts. The sample is selective; it supports observations about the archived text, not prevalence, official endorsement, or measured gains. The transferable rules are engineering deductions, expressed in our own terms.

| Observed decision | Sample evidence at the fixed revision | Where the rule belongs |
| --- | --- | --- |
| Ask when the missing answer changes the work; inspect known facts and use reasonable defaults first | [Claude Code question boundary](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/Anthropic/claude-code/claude-code-fable-5.2.md#L1143-L1145), [Muse Code question boundary](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/Meta/muse-code/muse-spark-1.3-muse-code.md#L962-L964), [Codex Work handling of missing input](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/OpenAI/Codex/gpt-6.1-sol-chatgpt-work-local.md#L67) | [Autonomy boundaries](context-security.md#autonomy-boundaries) |
| Distinguish progress questions, corrections, and requests to stop | [Perplexity Computer in-flight questions](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/Perplexity/perplexity-computer.md#L13), [Muse Code corrections and stopping](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/Meta/muse-code/muse-spark-1.3-muse-code.md#L1584-L1588), [Codex Work task continuity](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/OpenAI/Codex/gpt-6.1-sol-chatgpt-work-local.md#L69-L73) | [Long-running state](context-security.md#long-running-state) |
| Separate a request receipt from the outcome it may later produce | [Perplexity connector completion](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/Perplexity/perplexity-computer.md#L1311-L1312), [Grok Build background commands](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/xAI/grok-build.md#L1376-L1382), [Muse Code receipt semantics](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/Meta/muse-code/muse-spark-1.3-muse-code.md#L460-L462) | [Output and error contracts](tool-contracts.md#output-and-error-contracts) |

These observations connect to the knowledge base's [goal, material, and permission boundaries](../../../../ai-engineering/prompting/prompt-engineering-fundamentals.md), [plan updates and evidence reuse](../../../../ai-engineering/agents/orchestration-patterns.md), and [operation identity and uncertain outcomes](../../../../ai-engineering/systems/ai-application-architecture.md). Those chapters explain the mechanisms; the skill retains only the decisions needed while designing instructions.

The archive also contains context-dependent advice that should stay local. For example, the [Antigravity sample](https://github.com/asgeirtj/system_prompts_leaks/blob/fc0108f594b63bca905f2c4815aaef430d13bd68/Google/antigravity/gemini-4-argon-antigravity-ide.md#L129-L133) uses a more conservative uncertainty default. Such differences call for a task-specific boundary, not a universal instruction to ask more or act more.

For an independently specified protocol example, [RFC 9110 §15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3) defines HTTP 202 as acceptance for processing, not completion. That supports the HTTP distinction; other tools must document their own result semantics.

## Decisive scenarios

These are synthetic inspection cases, not recorded model runs:

- A report already has a suitable project format: proceed with it. A missing effective date controls an external commitment and only the user knows it: prepare independent draft content, ask for the date, and leave that commitment pending.
- During a report, a status question preserves the task; narrowing it to one quarter changes affected content; a pause prevents further task actions. An outstanding remote request remains outstanding until its actual status is known. A changed, previously approved write must still meet its authorization contract.
- The same export receipt is enough for “submit this export” but insufficient for “give me the exported file.” A completion event for another operation does not close this export. An unknown write result does not justify creating another operation under a new key.
