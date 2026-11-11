---
name: mynotes-maintainer
description: Maintain, review, reorganize, and document the MyNotes knowledge repository using its domain maps and writing rules.
---

# MyNotes Maintainer

Use this skill only for work in the MyNotes repository. Read the repository [AGENTS.md](../../../AGENTS.md) for operating constraints and [writing guide](../../../maintenance/writing-guide.md) for the content standard; keep detailed writing rules there rather than duplicating them here.

## Workflow

1. Identify the affected domain and read its `index.md` plus the relevant notes before changing content. Apply the writing guide's reader and language conventions to the affected content. Preserve useful explanations and distinctive examples.
2. For factual uncertainty, verify against authoritative documentation, papers, or reproducible behavior. Treat model memory as a lead only, and distinguish errors, version changes, conditional conclusions, and unresolved evidence. Add sources, versions, or verification dates to the note when they support an important decision. In a broad review, report the material screened separately from the claims verified against sources or by reproduction.
3. Before merging or moving content, identify the canonical chapter, inspect inbound links, and record where the old paths, linked headings, distinctive examples, and evidence will go. Update affected links, domain maps, `review/index.md`, and literature entries. If the reading order changes, sync [current-round reading progress](../../../review/reading-progress.md) using the [README](../../../readme.md) and follow its backup and recovery steps for renamed or removed paths. When recovering progress after a merge, transfer a checkmark only if the user's reading covered the full resulting chapter. Keep partial progress in the backup.
4. Before accepting a new main-route chapter or a substantial rewrite, read the canonical chapter straight through and check that its main answer stands on its own. For any case it passes to or takes up from an adjacent chapter on the main route, check that both chapters agree on the handoff state and that readers can follow the transition. Replay its main worked example, if present, and check the intermediate values or state changes that support the answer.

   For explanatory figures, use the writing guide's [planning method and acceptance checklist](../../../maintenance/writing-guide.md#plan-and-accept-explanatory-figures) before drafting and at final review. Check the complete picture-and-prose explanation, including handoffs between panels.

   For a new main-route chapter, a substantial rewrite, or a requested cold read, ask a separate Sol to review from a fresh context. Give the reviewer only the current draft path and the intended reader's background; when reviewing a reading route, also give the actual entry wording. With links unopened, have them record the scope they expect from the title and opening before reading the rest, then retell the main reasoning and where its conclusions apply. Ask for specific wording or visuals that forced a guess or reread, left an important condition implicit, or could lead to a wrong conclusion. Resolve material findings and have the reviewer reread the affected passages when needed; report this as a reread, not another independent cold read.

5. If an included note's content, title, or link changes, or its reading order changes, regenerate from the repository root with `python3 maintenance/build-reading-docs.py`, then run `python3 maintenance/build-reading-docs.py --check` to validate maps, source notes, and generated links. Review the generated output. From another working directory, invoke the same script by its absolute path.
6. When a change affects internal navigation or rendered output, consult the installed `obsidian-cli` skill and run targeted native checks for the affected behavior. The CLI requires the desktop app to be running. `unresolved` checks link targets at the file level. For changed heading links, click representative links in the affected source notes and continuous-reading documents and confirm they reach the intended headings. Include a cross-file jump when affected. In Reading view, sample changed callouts (including their links), diagrams, and formulas in the source note and its continuous-reading copy when present.

## Paper and article integration

When incorporating a user-supplied paper, article, or related discussion into MyNotes:

1. Read the primary source at the specified version. Use discussion to identify the user's focus. Ground claims in the source's evidence and keep experimental findings within their tested scope. Reconcile conflicting claims with the current notes using Workflow step 2. Before updating a current recommendation based on a foundational paper, apply the writing guide's [check for foundational sources](../../../maintenance/writing-guide.md#check-factual-claims).
2. Integrate reusable knowledge into the canonical question it helps answer. Use the writing guide to decide when a separate question warrants a new page. Keep the source's mechanism, conditions, and limits with the claim, and distinguish them from engineering extensions.
3. Follow the writing guide's source presentation rules to preserve the canonical chapter's evidence and claim mapping.
4. For AI sources, add or update an entry in the [AI literature index](../../../review/ai-literature-index.md) using its existing fields: title, original URL, version/date, one-sentence contribution following the writing guide's language convention, and canonical destinations. Place it under the relevant topic and link the actual integration points without duplicating their explanations. Reuse entries for repeated sources; for a new version, check changed claims and record the version(s) actually integrated.
5. Mark a canonical note as read only when the user's reading covers the whole note. Use Workflow step 3 for changes to the reading order.

Use the Workflow above for cross-links, maps, continuous-reading generation and validation, and AGENTS.md for reviewed delivery. Do not introduce a second maintenance or progress process.

## Boundaries

- Keep the six domain roots and existing topic ownership. Use English kebab-case paths without numeric prefixes; create folders only when substantive notes need them. Authorized, source-backed additions may fill knowledge gaps.
- Treat `archive` as paused or low-frequency maintenance, not as a correctness label.
- In an audit for public sharing, include archived notes, relevant attachments, and generated reading copies. Keep any evidence containing private material outside the repository.
- Preserve raw attachments, source files, and prompts as-is. Include course Markdown in knowledge review.
- Avoid broad metadata, per-note learning-status fields, recurring review schedules, or a publishing system.
- The legacy domain merge scripts are not the current reading-document entry point.
