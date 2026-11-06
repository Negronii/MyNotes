# Writing Guide

This is the single source of writing rules for MyNotes. Notes are a durable knowledge base; interview review is one way to use them, not the limit of what belongs here.

## Organize knowledge

- A chapter answers one question at the scale of a complete mechanism or decision. Keep the steps a reader needs for that answer as sections of the same chapter. Give a mechanism its own chapter when it has an independent question and meaningful use in at least two different contexts. A map entry, glossary mention, or backlink to its parent does not count as a second use.
- Use the six domain roots as the top-level boundary: `ai-engineering`, `frontend`, `engineering-foundations`, `archive`, `review`, and `maintenance`. Engineering foundations holds shared networking, operating systems, databases, API reliability, security, testing, deployment, backend, and system-design knowledge. Create topic folders when substantive notes need them; authorized, source-backed additions may fill knowledge gaps.
- Keep this open-source repository to general, reusable knowledge. Exclude personal résumé or project-experience material, internal project, system, code, or organization details, and unpublished results or data.
- Use English kebab-case filenames without numeric prefixes for new pages. Use subdirectories where they clarify ownership. Domain maps own the complete reading order. The knowledge navigator offers shorter routes through shared questions.
- Keep original attachments, source files, and prompts intact as a classified package. Course Markdown is part of the knowledge review.

## Plan a reading route

- Put a few questions at the top of each active domain map and identify a good first chapter. Each route follows one concrete run, failure, or decision from an observable starting point to an outcome. Carry the same case across steps and end once the question is answered.
- When changing a route, identify where readers first learn a mechanism, where they reuse it, and which material they can look up as needed.
- Before reorganizing multiple domains, try the proposed reading experience on one existing chapter and one path the current chapters do not connect. Use forced jumps and points where a reader loses the causal chain to decide where better navigation or more explanation is needed.

## Write for understanding and reuse

- Put the question in the title and give a short answer first. For a process, follow a concrete input through the transformations and show the relevant intermediate state, such as tensor shapes, protocol messages, or ownership changes. For a decision, connect the constraints to the choices and show how to tell when a choice fails. Use diagrams or runnable examples where they explain a step better than prose.
- Make an end-to-end chapter readable without opening its links. For each handoff, state what the preceding step produced and why the next step needs it. Work backward from the answer to the prerequisites that explain it. Assume an undergraduate computing background, including introductory linear algebra and statistics, and explain any domain-specific knowledge needed to bridge the steps.
- Use bilingual titles, short answers, key terms, and interview answers where included. Detailed derivations, mechanisms, and examples may use whichever language makes them clearest.
- Preserve useful knowledge and distinctive examples when rewriting, merging, or splitting notes. Remove genuine duplication, but do not delete lasting material only because it is not currently an interview topic.
- Explain a linked mechanism's role at the point where the reader needs it. Link to the page that owns the detailed answer. Use a section link when it helps the reader find a particular part, and verify the heading in the intended readers.
- Use Mermaid when a flow, state change, or interaction is easier to follow visually. Put new static assets in a nearby `resources` folder and use relative Markdown links. Explain the main point in prose so the page remains usable without the figure.
- End an end-to-end chapter with two short self-checks. Ask the reader to retell the chain from memory, then change one condition and ask what would happen or what evidence would distinguish the possible outcomes.
- Do not manufacture a gotcha, code example, or interview framing. Every example should clarify a point or show a real use.

## Check factual claims

Model memory is a prompt to investigate, not evidence. For uncertain or consequential claims, check authoritative documentation, papers, or reproducible behavior. Distinguish an error from a version change, a conditional conclusion, and insufficient evidence. Do not describe an unverified claim as confirmed. Record a source, version, and verification date in the note when they matter to a key decision; omit them when they add no value.

State the conditions that make a mechanism hold. For version-sensitive APIs or examples, give the applicable version and identify the version actually run when verified. For an engineering recommendation, name what it optimizes, what it costs, and what condition would change the choice.

When a foundational paper informs current practice, read follow-up research and a current reference implementation. Teach the durable mechanism and the applicable current practice in one account. Keep older methods only where their assumptions explain the current design or help maintain an existing system. Keep study results scoped to the tested task, model, workload, and baseline.

## Keep maintenance lightweight

- Obsidian is a reading interface; notes remain ordinary Markdown and should work outside Obsidian. For targeted native checks after link, path, or rendering changes, follow the [MyNotes maintenance workflow](../.agents/skills/mynotes-maintainer/SKILL.md).
- Do not add blanket YAML metadata, per-note learning or mastery status, or scheduled per-note review dates. When the user authorizes a central current-round checklist, it may record only read/not-read for that round; it is not a mastery claim or durable per-note status and must not be expanded into per-note YAML or scheduled reviews.
- `archive` means low-frequency or paused maintenance. It does not imply that content is wrong, obsolete, or deprecated.
- Domain `index.md` files are topic maps. Their one `## Reading order / 阅读顺序` section is the complete ordered list used to build continuous-reading documents. Keep each eligible article there once, with a working relative Markdown link. The map also handles navigation; do not create a second ordering source.
- If an included note's content, title, or link changes, or its reading order changes, regenerate continuous-reading documents with `python3 maintenance/build-reading-docs.py` from the repository root. Treat `review/generated/` as generated output: review it after generation, and do not edit it by hand. Run the same command with `--check` to validate the maps, source notes, and generated links without building output.
