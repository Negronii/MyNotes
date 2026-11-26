# MyNotes instructions

Use the [MyNotes maintenance skill](.agents/skills/mynotes-maintainer/SKILL.md) for repository work. The [writing guide](maintenance/writing-guide.md) owns domain boundaries, chapter design and content standards.

Prefer the smallest sufficient change that fixes the root cause. Keep documents information-dense. Do not use or install RTK.

Carry an authorized knowledge-review scope through to completion without per-topic approval pauses; coordinate internal owners and report one consolidated result.

For difficult work, have one Sol XHigh propose a plan and another Sol XHigh challenge it, with at most one challenge round; the main agent decides. After the plan is settled, or for simple implementation and information gathering, use Luna Max. The proposing Sol XHigh reviews implementations based on a proposal; for simple code work without a proposal, a different Luna Max cross-checks the result. Create a new Chat only for a large, difficult effort led by a Sol XHigh; otherwise use the current Chat or Subagents. Give each assignee a distinct scope and concrete deliverable, and provide enough context for them to start from a blank task. Wait for completion or mailbox events instead of polling progress.

Work directly on `main` by default. After each batch passes its appropriate review and checks, commit and push it to `origin/main` promptly; include only in-scope, reviewed changes and exclude unrelated or unreviewed files so completed work does not accumulate locally.
