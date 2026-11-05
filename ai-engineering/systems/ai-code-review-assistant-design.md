# How do you design a code-review assistant developers can trust? / 如何设计开发者愿意信任的代码审查助手？

**Core explanation / 核心解释：** Start with advisory findings tied to changed lines and visible code evidence, keep a person responsible for review decisions, and suppress weak claims when false positives are costly. Build evaluation cases from reviewed changes and clean examples; measure issue detection, false positives, valid locations, and workflow cost before increasing automation. / 先输出指向变更行且展示代码依据的建议，保留人工审查决策权，并在误报代价高时抑制依据薄弱的发现。用已审查变更和无问题样例构建评估集；在提高自动化程度前，测量问题检出、误报、位置有效性和流程成本。

## Design: code review assistant / 代码审查助手

**Clarify first:** Which languages and review types are in scope? Should findings be advisory or posted automatically? How is repository context selected? What level of false positives will developers tolerate? Which code or metadata may leave the repository boundary?

**Worked choice / 方案选择：** Suppose the team has low tolerance for noisy comments and wants a human to retain review authority. I would begin with advisory draft comments, require each finding to point to changed lines and cite the relevant code evidence, and suppress weak findings rather than posting every possible concern. I would not auto-approve or block a pull request. This favors developer trust and gives the team dismissal data before considering more automation.

**Illustrative architecture / 架构示意:**

~~~text
Pull request event → diff and repository context
                   → one or more review passes
                   → schema and location validation
                   → deduplicate and rank findings
                   → draft comments for human review
                   → collect feedback and measure outcomes
~~~

**Deep-dive topics:**

- **Context selection:** include changed lines, nearby code, relevant callers, and repository guidance as available. Record what was omitted when size limits require truncation.
- **Review passes:** separate correctness, security, and style checks when that makes evaluation or prompts clearer. Keep each pass tied to a defined review rubric.
- **Output validation:** require a finding category, explanation, location within the diff, and actionable suggestion; reject locations or structures that do not match the submitted change.
- **Noise management:** rank or suppress uncertain findings, show evidence, and make dismissal easy. The acceptable precision/recall balance depends on developer workflow and risk.
- **Large or generated changes:** segment by file or coherent unit, avoid irrelevant generated content, then deduplicate before presenting results.

**Evaluation and operations:** build a held-out set of reviewed changes with known issues and clean examples. Measure issue detection by category, false positives, location validity, developer acceptance or dismissal, cost per review, and delay added to the workflow. Compare against a no-assistant baseline; do not claim to outperform human review without evidence.

**Related design method / 相关设计方法：** [How do you turn an AI system design prompt into a defensible architecture? / 如何把 AI 系统设计题转化为有依据的架构？](./ai-system-design-interview-questions.md) covers the reusable scoping and trade-off sequence.
