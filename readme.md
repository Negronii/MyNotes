# MyNotes / 笔记库

A Markdown knowledge base for AI engineering, frontend, and shared engineering foundations. Obsidian can improve navigation, while the notes remain usable as standard Markdown.

## Start here / 从这里开始

- [Knowledge Navigator / 知识导航](review/index.md) — a short learning and reference route through selected AI/agent, frontend, and networking topics.
- [Reading progress / 本轮复习进度](review/reading-progress.md) — track notes read in this pass from the canonical domain reading orders.
- [AI engineering topics / AI 工程主题](ai-engineering/index.md)
- [Frontend topics / 前端主题](frontend/index.md)
- [Engineering foundations topics / 工程基础主题](engineering-foundations/index.md)
- [Archive / 归档区](archive/index.md)
- [Writing guide / 写作规范](maintenance/writing-guide.md)
- [Full knowledge review audit / 全库知识审查](maintenance/knowledge-review-audit.md) — reviewed scope, source-backed corrections, and validation limits.
- [Migration notes / 迁移说明](maintenance/migration-notes.md)
- [Agent Prompt & Tool Design / Agent 提示词与工具设计](.agents/skills/design-agent-prompts-tools/SKILL.md) — an active reusable Skill maintained in this repository.

The other domain roots are `archive`, for low-frequency or paused material, `review`, for navigation, and `maintenance`, for repository guidance and tools.

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

## Reading progress / 本轮复习进度

The checklist in `review/reading-progress.md` records only whether each note was read in the current pass. Sync it after changing a domain reading order, and inspect validated counts with:

```sh
python3 maintenance/sync-reading-progress.py
python3 maintenance/sync-reading-progress.py --status
```

Sync preserves checked notes and adds new entries unchecked. Before a new pass, back up the page and manually clear the checkboxes.
If a note is renamed or removed, sync stops to protect its reading state. Back up the progress page outside the vault, move the current page aside, run sync to create a fresh checklist, then use the backup to recheck the corresponding current paths and restore personal notes. Do not edit paths inside the managed block: its snapshot guard will reject the edit.

## Obsidian

This repository remains a standard Markdown vault. Use Obsidian for navigation and reading; the installed `obsidian-cli` skill is the command reference for targeted native link or rendering checks. Those checks supplement the [MyNotes maintenance workflow](.agents/skills/mynotes-maintainer/SKILL.md) and do not replace reading-document generation or `--check`. The three generated reading documents use URL-encoded full-heading fragments for Obsidian navigation; Markdown fragment handling varies by renderer, so GitHub section navigation is not guaranteed.
