# MyNotes / 笔记库

A Markdown knowledge base for AI engineering, frontend, and shared engineering foundations. Obsidian can improve navigation, while the notes remain usable as standard Markdown.

## Start here / 从这里开始

- [Interview review map / 面试复习地图](review/index.md) — a short route through selected AI/agent, frontend, and networking topics.
- [AI engineering topics / AI 工程主题](ai-engineering/index.md)
- [Frontend topics / 前端主题](frontend/index.md)
- [Engineering foundations topics / 工程基础主题](engineering-foundations/index.md)
- [Archive / 归档区](archive/index.md)
- [Writing guide / 写作规范](maintenance/writing-guide.md)
- [Migration notes / 迁移说明](maintenance/migration-notes.md)

The other domain roots are `archive`, for low-frequency or paused material, `review`, for navigation, and `maintenance`, for repository guidance and tools.

## Review coverage / 审核范围与进度

The original inventory contained 61 substantive notes: 14 in AI engineering and 47 in frontend. Migration added the existing Docker note as an active engineering-foundations note, so the current library has 62: 14 in AI engineering, 36 in frontend, and 12 in engineering foundations. The inventory work covered directory structure, samples, and titles; it does not mean the full library has been content-audited or made bilingual.

The first deep-review batch covers four AI/agent notes and one sample each from frontend and engineering foundations. All six have received full-text review, key fact checks, and bilingual revision, and have passed final review. See the [AI/agent audit / AI Agent 审计](maintenance/ai-agent-audit.md) and [bilingual samples audit / 双语样板审计](maintenance/bilingual-samples-audit.md) for the reviewed scope and evidence.

The second batch covers [RAG](ai-engineering/rag/rag-architecture-and-implementation.md), [LLM evaluation](ai-engineering/evaluation/llm-evaluation-methods.md), and [production safety](ai-engineering/safety/ai-safety-in-production.md). These three notes have received full-text review, key source checks, bilingual revision, and final content review. See the [RAG, evaluation, and production safety audit / RAG、评估与生产安全审计](maintenance/ai-quality-audit.md) for its scope and validation limits. Together, the two earlier batches reviewed nine of 62 active notes. The [review map / 面试复习地图](review/index.md) links to selected interview topics.

A broader review is underway: two of the 116 remaining substantive original notes have been accepted—[Model Selection](ai-engineering/foundations/model-selection-and-ecosystem.md) and [Prompt Engineering Fundamentals](ai-engineering/prompting/prompt-engineering-fundamentals.md). Its fixed scope covers 53 remaining active and 63 archived knowledge Markdown notes; three selected new foundations notes are tracked separately. See the [full knowledge review audit / 全库知识审查](maintenance/knowledge-review-audit.md) for accepted work and checks. This is not a completion claim for the broader scope.

## Continuous-reading documents / 连续阅读稿

From the repository root, run:

```sh
python3 maintenance/build-reading-docs.py
```

The command reads each domain's single `## Reading order / 阅读顺序` section and writes:

- `review/generated/ai-engineering.md`
- `review/generated/frontend.md`
- `review/generated/engineering-foundations.md`

Edit the domain index to change the order, then regenerate. Generated files are outputs and should not be edited by hand. The generator does not stage or commit changes.

To validate that domain maps, source notes, and generated links are current without rebuilding output, run:

```sh
python3 maintenance/build-reading-docs.py --check
```

## Obsidian

This repository remains a standard Markdown vault. Use Obsidian for navigation and reading; the installed `obsidian-cli` skill is the command reference for targeted native link or rendering checks. Those checks supplement the [MyNotes maintenance workflow](.agents/skills/mynotes-maintainer/SKILL.md) and do not replace reading-document generation or `--check`. The three generated reading documents use URL-encoded full-heading fragments for Obsidian navigation; Markdown fragment handling varies by renderer, so GitHub section navigation is not guaranteed.
