---
name: mynotes-maintainer
description: Maintain, review, reorganize, and document the MyNotes knowledge repository using its domain maps and writing rules.
---

# MyNotes Maintainer

Use this skill only for work in the MyNotes repository. Read the repository [AGENTS.md](../../../AGENTS.md) for operating constraints and [writing guide](../../../maintenance/writing-guide.md) for the content standard; keep detailed writing rules there rather than duplicating them here.

## Workflow

1. Identify the affected domain and read its `index.md` plus the relevant notes before changing content. Preserve useful explanations and distinctive examples.
2. For factual uncertainty, verify against authoritative documentation, papers, or reproducible behavior. Treat model memory as a lead only, and distinguish errors, version changes, conditional conclusions, and unresolved evidence. Add sources, versions, or verification dates to the note when they support an important decision.
3. Keep knowledge in its canonical note. Update a domain map or `review/index.md` when a path or useful navigation relationship changes; link to the note instead of copying its answer.
4. If an included note's content, title, or link changes, or its reading order changes, regenerate from the repository root with `python3 maintenance/build-reading-docs.py`, then run `python3 maintenance/build-reading-docs.py --check` to validate maps, source notes, and generated links. Review the output; do not edit generated files by hand. From another working directory, invoke the same script by its absolute path.
5. When a change affects links, paths, or Obsidian-rendered output, consult the installed `obsidian-cli` skill and run targeted native checks for that behavior. The CLI requires the desktop app to be running. `unresolved` reports unresolved links but does not verify heading fragments; manually verify representative heading navigation when it matters. Use DOM or screenshot inspection only when rendered output is part of the change. These checks supplement the Markdown and generator workflow; they are not required for routine small edits.

## Boundaries

- Keep the six domain roots and existing topic ownership. Use English kebab-case paths without numeric prefixes; create folders only when substantive notes need them. Authorized, source-backed additions may fill knowledge gaps.
- Treat `archive` as paused or low-frequency maintenance, not as a correctness label.
- Preserve raw attachments, source files, and prompts as-is. Include course Markdown in knowledge review.
- Avoid broad metadata, personal learning-status fields, recurring review schedules, or a publishing system.
- The legacy domain merge scripts are not the current reading-document entry point.
