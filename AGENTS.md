# MyNotes instructions

Use [`.agents/skills/mynotes-maintainer/SKILL.md`](.agents/skills/mynotes-maintainer/SKILL.md) for repository-specific maintenance work. [The writing guide](maintenance/writing-guide.md) is the single source of content rules; this file is the operating entry point and should not restate that guide.

The repository has six top-level domains: `ai-engineering`, `frontend`, `engineering-foundations`, `archive`, `review`, and `maintenance`. Engineering foundations covers shared networking, operating systems, databases, API reliability, security, testing, deployment, backend, and system design. Create topic folders when substantive notes need them; authorized, source-backed additions may fill knowledge gaps. Treat archive as low-frequency or paused maintenance, not as a claim that its content is wrong or deprecated.

Prefer the smallest sufficient change that fixes the root cause. Keep documents information-dense. Do not use or install RTK.

For difficult work, have one Sol XHigh propose a plan and another Sol XHigh challenge it, with at most one challenge round; the main agent decides. After the plan is settled, or for simple implementation and information gathering, use Luna Max. The proposing Sol XHigh reviews implementations based on a proposal; for simple code work without a proposal, a different Luna Max cross-checks the result. Create a new Chat only for a large, difficult effort led by a Sol XHigh; otherwise use the current Chat or Subagents. Give each assignee a distinct scope and concrete deliverable, and provide enough context for them to start from a blank task. Wait for completion or mailbox events instead of polling progress.

After each batch passes its appropriate review and checks, commit and push it to `origin` promptly; include only in-scope, reviewed changes and exclude unrelated or unreviewed files so completed work does not accumulate locally.
