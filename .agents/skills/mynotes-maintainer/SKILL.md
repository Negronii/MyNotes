---
name: mynotes-maintainer
description: Integrate readings into the MyNotes textbook, review factual claims and learning routes, and maintain the repository's navigation and reading copies.
---

# MyNotes Maintainer

Use [AGENTS.md](../../../AGENTS.md) for repository operations. The public [writing guide](../../../maintenance/writing-guide.md) owns the editorial standard. Read the guidance that applies to the change.

## Choose the workflow

- **Bring in a paper, article, discussion, or reading batch.** Read each original. For each point selected for teaching, look for related primary sources on the same question and use [source integration](references/source-integration.md) to check later evidence or current practice. Show what still holds, what changed or what evidence is missing, in the chapter that answers the reader's question. Then place each point in the conversation, without storing the list: strengthen a section, add a section, add a chapter under the guide's chapter rule, change a main line, or leave it out with a reason. A new main-line question or a changed answer outline changes the domain pyramid; show the revised pyramid sketch and wait for approval before restructuring the map, unless the user has already authorized restructuring that domain. In a broad audit, distinguish sources screened from claims verified. For each AI source used, update its entry in the [AI literature index](../../../review/ai-literature-index.md) or add one with the original URL, version/date, contribution and teaching destinations. Reuse the entry for repeat sources and review changed claims in a new version.
- **Restructure a domain or rewrite at scale.** Treat existing chapters as material, not structure. Inventory the knowledge first, then derive the pyramid and chapter boundaries, following [knowledge restructuring](references/knowledge-restructuring.md).
- **Write a chapter or change a learning route.** Read the relevant domain map and notes. The domain map owns the complete order. The [knowledge navigator](../../../review/index.md) offers shorter routes. Use the guide's [route design](../../../maintenance/writing-guide.md#plan-a-reading-route) for chapter handoffs and its [figure checklist](../../../maintenance/writing-guide.md#plan-and-accept-explanatory-figures) for explanatory visuals.
- **Move, merge or retire notes.** Account for old paths, linked headings, distinctive examples and evidence. Update affected links and indexes. If an existing path disappears from the reading map or changes domains, follow the [progress backup and recovery procedure](../../../readme.md#本轮阅读进度). Carry a checkmark across a merge only if the reader covered the whole resulting chapter. Keep partial progress in the backup.
- **Audit for public sharing.** Include archived notes, relevant attachments and generated copies. Keep private evidence outside the repository.

## Checks that apply to the change

- For a new main-route chapter or a substantial rewrite, read the full explanation, replay its worked example and check the case at each chapter handoff. Use an independent Sol reviewer for these changes and for an explicitly requested cold read. Give a route reviewer the actual reader entry point. Follow [document-cold-read](../document-cold-read/SKILL.md).
- When an included note or its order changes, regenerate, inspect and check the [reading copies](../../../readme.md#连续阅读稿). Sync and check reading progress when the map entries change. Use the existing scripts in `maintenance/` from the repository root.
- For navigation or rendering changes, use the installed `obsidian-cli` skill with Obsidian running. The `unresolved` command checks file targets. Click affected heading links in representative source notes and reading copies, including a cross-file jump when relevant. Sample changed callouts and their links, diagrams and formulas in Reading view.
