# Migration notes / 迁移说明

## Result / 结果

The 61 substantive articles from the two former main folders now live under three topic domains: AI Engineering has 14, Frontend has 36, and Engineering Foundations has 11. The foundations index also includes one retained Docker operations reference, so it lists 12 articles in total. Article filenames use stable English kebab-case paths without numeric prefixes. At the structural-migration checkpoint before the first six sample-article rewrites, the 61 article bodies had only planned relative Markdown link-target changes.

Shared HTTP and web security, algorithms and data structures, Node.js runtime basics, general design principles and patterns, interview preparation, Agile, and Git moved to Engineering Foundations. Browser, HTML/CSS, JavaScript, TypeScript, frontend build tooling, React, browser APIs, performance, libraries, and frontend testing remain in Frontend.

## Old paths and generator / 旧路径与生成器

| Former path | Current path or replacement |
|---|---|
| `AI_Engineering_Notes/` | `ai-engineering/` |
| `Frontend_Notes/` | `frontend/` plus shared topics in `engineering-foundations/` |
| `AI_Engineering_Notes/merge-md.sh` | `archive/historical-scripts/AI_Engineering_Notes/merge-md.sh` (historical copy only) |
| `Frontend_Notes/merge-md.sh` | `archive/historical-scripts/Frontend_Notes/merge-md.sh` (historical copy only) |
| `AI_Engineering_Notes/Interview-All-In-One.md` | `review/generated/ai-engineering.md` |
| `Frontend_Notes/Interview-All-In-One.md` | `review/generated/frontend.md` |
| No former foundations bundle | `review/generated/engineering-foundations.md` |
| Old per-folder script invocation | `python3 maintenance/build-reading-docs.py` (use `--check` to validate) |

The old generated bundles were compared with their current source articles after normalizing heading depth and removing generator-inserted numeric wrappers. Neither bundle contained a unique non-heading body line or example absent from the source set. Catalogue labels are replaced by the new indexes; four current frontend source lines occur only in the source articles, which remain preserved. The old scripts were not run.

## Archives and retained older notes / 归档与旧笔记

`archive/index.md` links the preserved packs. The AI source, prompt, and skill trees; old frontend learning pack; mobile, machine-learning, quantitative-trading, university-course, backend, and Jest materials keep their internal paths and bytes. The five course Markdown files are individually listed in the inventory for later review. Folder age or former names do not imply that archived content is obsolete.

The mixed `back-end/Backend-Concepts.md`, ASP.NET Core, Spring, and shell setup notes remain archived intact because they mix narrow framework or personal setup details with topics that need review. The Docker operations note moved into Engineering Foundations. The two old `_product` guides were removed after the rule owner reconciled their applicable guidance from `HEAD` into root-level documentation.

## Integrity / 完整性

SHA-256 comparison covered every tracked file in the migrated source trees. 2354 files in archived packs and historical scripts are byte-identical at their new paths. At that checkpoint, all 61 primary articles and the Docker note matched the source bytes after only planned relative-link updates; 58 notes required link updates (169 link destinations). The link scan checked 236 relative Markdown links across all three active domains and found no missing targets. 33 tracked legacy files were intentionally replaced or removed: 24 empty topic placeholders, one empty `temp.md`, two catalogues, two generated bundles, and four merged writing-guide files. No archived source, course attachment, or retained article failed its hash check. A broad scan also found 21 unresolved local-link-looking targets inside archived material; these include prompt examples and source-pack references, were not individually classified, and remain unchanged to preserve the archived bytes. Their internal source-pack paths were retained as-is.

`maintenance/knowledge-inventory.tsv` records old/new paths, classifications, migration handling, and SHA-256 values from that same checkpoint; these hashes are a snapshot, not a live body check. The baseline commit is `e79514184b2f169e86c96783b0a11e3213116db4`; current sample rewrites are documented in [AI agent audit](ai-agent-audit.md) and [bilingual sample audit](bilingual-samples-audit.md).
