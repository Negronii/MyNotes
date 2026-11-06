# MyNotes 笔记库

面向长期学习的 Markdown 知识库，覆盖 AI 工程、前端与共享工程基础。每章围绕一个完整问题展开，正文讲清过程，内部链接用于深入相关机制。可以用 Obsidian 阅读，也可以直接打开 Markdown。

## 从这里开始

- [知识导航](review/index.md) — 从问题路线进入，也可以打开整册连续阅读稿。
- [本轮阅读进度](review/reading-progress.md) — 按领域阅读顺序记录这一轮读过的章节。
- [AI 工程](ai-engineering/index.md)、[前端](frontend/index.md)、[工程基础](engineering-foundations/index.md) — 各领域的问题入口与完整阅读顺序。
- [AI 好文集](review/ai-literature-index.md) — 论文与文章的贡献、版本及知识沉淀位置。
- [归档索引](archive/index.md) — 课程演算、早期示例与原始材料。
- [写作规范](maintenance/writing-guide.md)、[知识正文重写记录](maintenance/rewrite-plan.md) — 内容标准、本轮范围和 DeepSeek 三篇的沉淀去向。
- [2026-10-27 全库知识审查记录](maintenance/knowledge-review-2026-10-27.md) — 当时 140 篇原始文章的审查范围、证据与修正。
- [迁移说明](maintenance/migration-notes.md)
- [Agent 提示词与工具设计](.agents/skills/design-agent-prompts-tools/SKILL.md) — 在本仓库持续维护的可复用 Skill。

`archive` 表示低频或暂停维护，`review` 保存导航与阅读入口，`maintenance` 保存仓库规范和工具。

## 连续阅读稿

在仓库根目录运行：

```sh
python3 maintenance/build-reading-docs.py
```

命令读取各领域索引唯一的 `## Reading order / 阅读顺序` 小节，生成：

- `review/generated/ai-engineering.md`
- `review/generated/frontend.md`
- `review/generated/engineering-foundations.md`

要调整阅读顺序，修改领域索引后重新生成。直接维护正文与索引，不手改生成稿；生成器不会暂存或提交 Git 改动。

只检查索引、正文链接及生成结果是否一致，可运行：

```sh
python3 maintenance/build-reading-docs.py --check
```

## 本轮阅读进度

`review/reading-progress.md` 只记录这一轮是否读过某章。改变阅读顺序后，同步清单并检查统计：

```sh
python3 maintenance/sync-reading-progress.py
python3 maintenance/sync-reading-progress.py --status
```

同步会保留已勾选章节，新章节默认不勾选。开始新一轮前，先备份进度页，再手动清空勾选。

章节改名或删除时，同步会停止，以免丢失阅读记录。先把进度页备份到 Vault 外，再移开当前页并运行同步，生成新清单；随后对照备份恢复对应章节的勾选及个人备注。不要直接修改托管区内的路径，快照检查会拒绝这类变动。

## Obsidian

本仓库可作为标准 Markdown Vault 使用。Obsidian 适合阅读、展开卡片和沿链接深入；已安装的 `obsidian-cli` Skill 提供原生链接与渲染检查命令。这些检查属于 [MyNotes 维护流程](.agents/skills/mynotes-maintainer/SKILL.md)，仍需生成连续阅读稿并运行 `--check`。

三册合并稿使用经过 URL 编码的完整标题片段，供 Obsidian 跳转。不同 Markdown 阅读器处理标题片段的方式不同，因此不保证 GitHub 中的小节跳转行为相同。
