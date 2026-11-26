# MyNotes 笔记库

面向长期学习的 Markdown 知识库，覆盖 AI 工程、前端与共享工程基础。每章围绕一个完整问题展开，可以在 Obsidian 中阅读，也可以直接打开 Markdown。

## 阅读入口

| 阅读方式 | 入口 |
|---|---|
| 从具体问题开始，沿知识导航中的问题路线阅读，例如“AI 应用怎样凭证据回答？” | [知识导航](review/index.md) |
| 按领域系统阅读完整顺序 | [AI 工程](ai-engineering/index.md)、[前端](frontend/index.md)、[工程基础](engineering-foundations/index.md) |
| 连续阅读一个领域 | [三份连续阅读稿](#连续阅读稿) |
| 已知道要查的机制 | [按机制查找](review/index.md#按机制查找) |
| 记录这一轮读过的正文 | [本轮阅读进度](review/reading-progress.md) |

读完一条路线后，想深入某个机制时，可以沿章节中指向相关问题的链接继续阅读。论文与文章的来源、版本和正文落点见[AI 好文集](review/ai-literature-index.md)，课程推导与原始材料见[归档索引](archive/index.md)。归档表示低频或暂停维护，不代表内容错误或废弃。

## 连续阅读稿

各领域地图列出该领域的完整阅读顺序，连续阅读稿按地图中的 `## Reading order / 阅读顺序` 小节生成：

- [AI 工程连续阅读稿](review/generated/ai-engineering.md)
- [前端连续阅读稿](review/generated/frontend.md)
- [工程基础连续阅读稿](review/generated/engineering-foundations.md)

调整顺序或修改已纳入阅读稿的正文后，在仓库根目录运行：

```sh
python3 maintenance/build-reading-docs.py
```

直接维护正文与领域地图，由生成器更新阅读稿。要检查地图、正文与阅读稿中的本地链接，并核对生成结果，可运行以下命令。

```sh
python3 maintenance/build-reading-docs.py --check
```

生成器只写入阅读稿，不会暂存或提交 Git 改动。

## 本轮阅读进度

阅读进度页只记录这一轮是否完整读过某章。新增章节、调整顺序或只改地图上的章节标题后，在仓库根目录同步清单并查看进度。

```sh
python3 maintenance/sync-reading-progress.py
python3 maintenance/sync-reading-progress.py --status
```

`--status` 会先校验清单，再显示阅读统计。自动检查使用 `--check` 校验同一份清单。

同步会保留已有勾选，新章节默认未读。若要从头开始新一轮，先将进度页备份到仓库外，再清除清单中的所有勾选。

如果已有章节的文件路径发生变化、从地图中移除，或改归另一个领域，同步会停止并指出原路径。确认这次调整符合预期后，按以下步骤接回旧记录。

1. 将 `review/reading-progress.md` 复制到仓库外保存旧清单备份。
2. 保留这份备份，将仓库中的旧进度页暂时移出仓库，再运行同步以生成新清单。
3. 对照备份，手动恢复已完整读过章节的勾选和个人备注。

合并章节后，只有完整读过合并后的正文才勾选为已读；若合并后的正文含有尚未读过的内容，保留备份中的旧章节勾选作追溯，合并后的章节保持未勾选。清单中的标题、路径和顺序由同步器维护，手动只改勾选框。

## Obsidian

本仓库可作为标准 Markdown Vault 使用。Obsidian 适合展开卡片并沿链接深入；连续阅读稿的小节链接按 Obsidian 的标题规则生成，GitHub 等平台可能使用不同的跳转格式。若跳转没有落到目标小节，可按小节标题查找。

## 贡献与维护

读到值得留下的材料，可以在 Codex 中打开本仓库，新建或继续一个对话，贴上原文链接，说说你最想弄懂或记住什么。一批材料可以一起发，有相关讨论或特定版本时一并附上。维护者逐篇读原文、按知识点核对后续证据，再决定补进哪一章。

[写作规范](maintenance/writing-guide.md)是知识正文的统一内容标准，可在 Obsidian 中直接阅读。以下是维护者使用的技能。

- [MyNotes 维护流程](https://github.com/Negronii/MyNotes/blob/main/.agents/skills/mynotes-maintainer/SKILL.md) — 来源整合、正文编写、阅读路线与仓库维护。
- [Agent 提示词与工具设计](https://github.com/Negronii/MyNotes/blob/main/.agents/skills/design-agent-prompts-tools/SKILL.md)
- [文档冷读](https://github.com/Negronii/MyNotes/blob/main/.agents/skills/document-cold-read/SKILL.md)

向 `main` 推送提交或向其发起 PR 时，GitHub Actions 会运行上文的阅读稿和进度检查，并执行维护脚本的单元测试（`python3 -m unittest discover -s maintenance/tests`）。直接推送前先在本地检查，推送后可在 GitHub 的 Actions 页面看到该提交的结果。
