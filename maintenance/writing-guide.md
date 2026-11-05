# Writing Guide

This is the single source of writing rules for MyNotes. Notes are a durable knowledge base; interview review is one way to use them, not the limit of what belongs here.

## Organize knowledge

- A knowledge note answers one coherent question. Give the reader a complete answer on the page. Give a follow-up its own page when it can support an independent explanation or be reused in other questions.
- Use the six domain roots as the top-level boundary: `ai-engineering`, `frontend`, `engineering-foundations`, `archive`, `review`, and `maintenance`. Engineering foundations holds shared networking, operating systems, databases, API reliability, security, testing, deployment, backend, and system-design knowledge. Create topic folders when substantive notes need them; authorized, source-backed additions may fill knowledge gaps.
- Keep this open-source repository to general, reusable knowledge. Exclude personal résumé or project-experience material, internal project, system, code, or organization details, and unpublished results or data.
- Use English kebab-case filenames without numeric prefixes for new pages. Use subdirectories where they clarify ownership. Domain maps own the complete reading order. The knowledge navigator offers shorter routes through shared questions.
- Keep original attachments, source files, and prompts intact as a classified package. Course Markdown is part of the knowledge review.

## Write for understanding and reuse

- Put the question in the title and give a short answer first. For a process, explain what enters each step, what changes, why it matters, and what comes out. For a decision, connect the constraints to the choices and their tradeoffs. Keep tables, commands, and worked examples in the form the reader can best use.
- Use bilingual titles, short answers, key terms, and interview answers where included. Detailed derivations, mechanisms, and examples may use whichever language makes them clearest.
- Preserve useful knowledge and distinctive examples when rewriting, merging, or splitting notes. Remove genuine duplication, but do not delete lasting material only because it is not currently an interview topic.
- Explain a linked mechanism's role at the point where the reader needs it. Link to the page that owns the detailed answer. Use a section link when it helps the reader find a particular part, and verify the heading in the intended readers.
- Use Mermaid when a flow, state change, or interaction is easier to follow visually. Put new static assets in a nearby `resources` folder and use relative Markdown links. Explain the main point in prose so the page remains usable without the figure.
- Do not manufacture a gotcha, code example, or interview framing. Every example should clarify a point or show a real use.

## Check factual claims

Model memory is a prompt to investigate, not evidence. For uncertain or consequential claims, check authoritative documentation, papers, or reproducible behavior. Distinguish an error from a version change, a conditional conclusion, and insufficient evidence. Do not describe an unverified claim as confirmed. Record a source, version, and verification date in the note when they matter to a key decision; omit them when they add no value.

## Keep maintenance lightweight

- Obsidian is a reading interface; notes remain ordinary Markdown and should work outside Obsidian. For targeted native checks after link, path, or rendering changes, follow the [MyNotes maintenance workflow](../.agents/skills/mynotes-maintainer/SKILL.md).
- Do not add blanket YAML metadata, per-note learning or mastery status, or scheduled per-note review dates. When the user authorizes a central current-round checklist, it may record only read/not-read for that round; it is not a mastery claim or durable per-note status and must not be expanded into per-note YAML or scheduled reviews.
- `archive` means low-frequency or paused maintenance. It does not imply that content is wrong, obsolete, or deprecated.
- Domain `index.md` files are topic maps. Their one `## Reading order / 阅读顺序` section is the complete ordered list used to build continuous-reading documents. Keep each eligible article there once, with a working relative Markdown link. The map also handles navigation; do not create a second ordering source.
- If an included note's content, title, or link changes, or its reading order changes, regenerate continuous-reading documents with `python3 maintenance/build-reading-docs.py` from the repository root. Treat `review/generated/` as generated output: review it after generation, and do not edit it by hand. Run the same command with `--check` to validate the maps, source notes, and generated links without building output.
