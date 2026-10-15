# Writing Guide

This is the single source of writing rules for MyNotes. Notes are a durable knowledge base; interview review is one way to use them, not the limit of what belongs here.

## Organize knowledge

- A note covers one coherent topic that a reader can understand and reuse on its own. Do not force every detail into an atomic note.
- Use the six domain roots as the top-level boundary: `ai-engineering`, `frontend`, `engineering-foundations`, `archive`, `review`, and `maintenance`. Engineering foundations holds shared networking, operating systems, databases, API reliability, security, testing, deployment, backend, and system-design knowledge. Create topic folders when substantive notes need them; authorized, source-backed additions may fill knowledge gaps.
- Use English kebab-case filenames without numeric prefixes. Use a small number of subdirectories where they clarify topic ownership. Put reading and interview sequences in the domain map rather than encoding order in filenames. Do not add empty topic folders.
- Keep original attachments, source files, and prompts intact as a classified package. Course Markdown is part of the knowledge review.

## Write for understanding and reuse

- Lead with the conclusion or useful mental model, then explain the mechanism and evidence. Prefer concrete examples and concise explanations; remove setup that does not help understanding.
- Keep the shape that serves the material. Concept notes explain how or why something works. Reference notes keep useful tables, commands, and catalogs easy to scan. System-design questions explain requirements, architecture, key decisions, and tradeoffs. Do not force every note into interview questions or a fixed template.
- Use bilingual titles, key terms, core explanations, and interview answers. Detailed derivations, mechanisms, and examples may use whichever one language makes them clearest; do not translate every paragraph just for symmetry.
- Preserve useful knowledge and distinctive examples when rewriting, merging, or splitting notes. Remove genuine duplication, but do not delete lasting material only because it is not currently an interview topic.
- Cross-link related notes when the connection helps the reader, and say why the link matters. Link to the canonical explanation instead of copying it.
- Do not manufacture a gotcha, code example, or interview framing. Every example should clarify a point or show a real use.

## Check factual claims

Model memory is a prompt to investigate, not evidence. For uncertain or consequential claims, check authoritative documentation, papers, or reproducible behavior. Distinguish an error from a version change, a conditional conclusion, and insufficient evidence. Do not describe an unverified claim as confirmed. Record a source, version, and verification date in the note when they matter to a key decision; omit them when they add no value.

## Keep maintenance lightweight

- Obsidian is a reading interface; notes remain ordinary Markdown and should work outside Obsidian. For targeted native checks after link, path, or rendering changes, follow the [MyNotes maintenance workflow](../.agents/skills/mynotes-maintainer/SKILL.md).
- Do not add blanket YAML metadata, learning or mastery status, or scheduled per-note review dates.
- `archive` means low-frequency or paused maintenance. It does not imply that content is wrong, obsolete, or deprecated.
- Domain `index.md` files are topic maps. Their one `## Reading order / 阅读顺序` section is the complete ordered list used to build continuous-reading documents. Keep each eligible article there once, with a working relative Markdown link. The map also handles navigation; do not create a second ordering source.
- If an included note's content, title, or link changes, or its reading order changes, regenerate continuous-reading documents with `python3 maintenance/build-reading-docs.py` from the repository root. Treat `review/generated/` as generated output: review it after generation, and do not edit it by hand. Run the same command with `--check` to validate the maps, source notes, and generated links without building output.
