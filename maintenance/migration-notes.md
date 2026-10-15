# Migration notes / 迁移说明

## Result / 结果

At the structural-migration checkpoint, the 61 substantive articles from the two former main folders were placed under three topic domains: AI Engineering had 14, Frontend 36, and Engineering Foundations 11. The foundations index also included one retained Docker operations reference, for 12 entries. These are historical migration counts, before the three later foundations additions. Article filenames used stable English kebab-case paths without numeric prefixes. At that checkpoint, the 61 article bodies had only planned relative Markdown link-target changes.

Those counts and integrity results describe structural placement and byte preservation at that earlier checkpoint, not a content-review verdict. The later review of knowledge Markdown and its source-validation limits are recorded in the [full knowledge review audit](knowledge-review-audit.md).

During that structural migration, shared HTTP and web security, algorithms and data structures, Node.js runtime basics, general design principles and patterns, interview preparation, Agile, and Git were grouped under Engineering Foundations. Browser, HTML/CSS, JavaScript, TypeScript, frontend build tooling, React, browser APIs, performance, libraries, and frontend testing were grouped in Frontend.

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

At the structural-migration checkpoint, the old generated bundles were compared with their source articles after normalizing heading depth and removing generator-inserted numeric wrappers. Neither bundle contained a unique non-heading body line or example absent from its source set. Catalogue labels were replaced by the new indexes; four frontend source lines occurred only in the source articles, which remained preserved. The old scripts were not run.

## Archives and retained older notes / 归档与旧笔记

`archive/index.md` links the preserved packs. At the structural-migration checkpoint, the AI source, prompt, and skill trees; old frontend learning pack; mobile, machine-learning, quantitative-trading, university-course, backend, and Jest materials retained their internal paths and archive bytes. The five course Markdown files were listed in the inventory for later review at that time. This describes the migration snapshot; the later content review of substantive knowledge Markdown is summarized in the [full knowledge review audit](knowledge-review-audit.md). Folder age or former names do not imply that archived content is obsolete.

At the structural checkpoint, `back-end/Backend-Concepts.md`, ASP.NET Core, Spring, and shell setup remained in the archive as separate framework and environment-setup references. Their placement recorded the migration decision; those notes later received scoped content review, as described in the audit. The Docker operations note moved to Engineering Foundations. The two old `_product` guides were removed after the rule owner reconciled their applicable guidance from `HEAD` into root-level documentation.

## Integrity / 完整性

The following figures are the structural-migration checkpoint comparison, before later editorial body changes. SHA-256 comparison covered every tracked file in the migrated source trees. At that checkpoint, 2354 files in archived packs and historical scripts were byte-identical at their new paths. The 61 primary articles and Docker note matched their source bytes after only planned relative-link updates; 58 notes required link updates (169 destinations). The active-domain link scan checked 236 relative Markdown links and found no missing targets at that time. Thirty-three tracked legacy files were intentionally replaced or removed: 24 empty topic placeholders, one empty `temp.md`, two catalogues, two generated bundles, and four merged writing-guide files. No archived source, course attachment, or retained article failed its hash check in that migration comparison. A broad archived-material scan at the time found 21 unresolved local-link-looking targets, including prompt examples and source-pack references; they were not individually classified and remained unchanged in the archived materials.

`maintenance/knowledge-inventory.tsv` records old/new paths, classifications, migration handling, and SHA-256 values from that same checkpoint; these hashes are a snapshot, not a live body check. The baseline commit is `e79514184b2f169e86c96783b0a11e3213116db4`; later sample rewrites are documented in [AI agent audit](ai-agent-audit.md) and [bilingual sample audit](bilingual-samples-audit.md).
