# Git 怎样记录一次改动，出错时又怎样按层撤回？

本章回答：Git 把一次改动依次存在哪几层，怎样保证提交里的内容正是测试过的那份快照，整合别人的提交时怎样守住语义，以及出错时怎样按改动所在的层选恢复命令。读者手上有上一章通过的测试和修复后的代码，它们此刻还只是磁盘上的文件。

**案例。** 沿用主线五的报表服务修复。修复只涉及两个文件：`src/reports.py` 把读取改成按 `(account_id, report_id)` 显式查询，`tests/test_report_scope.py` 加入跨账户反例。开发者在分支 `fix/report-account-scope` 上工作，要把这份已审查的源码快照变成一个可追溯的提交，交给 CI 构建。文中的提交 ID 是示意值：rebase 前的修复提交记作 `6ab06f8`，rebase 后成为 `c4f2a91`，后续构建章都从 `c4f2a91` 接手。

## 一次改动停在哪一层

Git 里的改动依次经过四层状态：

| 层 | 是什么 | 怎样进入下一层 |
| --- | --- | --- |
| working tree (工作区) | 磁盘上正在编辑的文件 | `git add` 把文件当前内容复制进暂存区 |
| index (暂存区) | 准备放进下一次提交的快照 | `git commit` 把暂存区写成提交 |
| commit (提交) | 一份完整的目录快照（tree）及其父提交 | 分支引用移动到新提交 |
| branch (分支) | 指向某个提交的可移动引用；`HEAD` 指向当前分支 | `git push` 等操作把引用共享出去 |

本章只讨论在分支上工作的常见情况：`HEAD` 指向当前分支，分支指向当前提交，提交成功后分支移动到新提交。分清改动停在哪一层，后面才能选对比较命令和恢复命令。

## 被测快照必须等于提交快照

`git add` 复制的是**执行那一刻**的文件内容。之后继续编辑，暂存区不会跟着变。下面追踪 `src/reports.py` 的三个版本：`v0` 是原内容，`v1` 加上账户条件，`v2` 又补了错误处理。表中每格是该层保存的文件内容：

| 执行到哪一步 | 工作区 | 暂存区 | HEAD 提交 |
| --- | --- | --- | --- |
| 编辑为 `v1` | `v1` | `v0` | `v0` |
| `git add src/reports.py` | `v1` | `v1` | `v0` |
| 再编辑为 `v2`，没有再次 add | `v2` | `v1` | `v0` |
| `git commit` | `v2` | `v1` | `v1` |

最后一步只提交了账户条件，错误处理仍是未暂存的改动。两条比较命令各看一段：

- `git diff`：工作区对暂存区，即“还没暂存的改动”。
- `git diff --cached`：暂存区对 HEAD，即“这次会提交的改动”。

问题在于测试通常读取工作区里的文件。`v2` 通过了测试，不能说明只含 `v1` 的提交也能通过。所以验收要让被测内容与准备提交的快照一致：要么先把工作区整理到与暂存区相同再测试，要么在隔离目录里测试待提交的快照，例如用 `git worktree` 检出一份干净副本。工作区混有其他任务的改动时，后一种做法更可靠。

## 只把这次修复放进提交

两个常见误解会让提交混进无关内容：

- **创建分支不保存改动。** `git switch -c <name>` 只新建一个指向当前提交的引用，未提交的改动会跟着留在工作区和暂存区。切换任务前要保护它们，应先提交，或用 `git stash` 搁置。
- **按路径暂存不是“只暂存这次修复”。** `git add <path>` 不会移除暂存区里原有的其他改动，而且会暂存所选文件的**全部**修改，包括与本次修复无关的部分。

所以流程是：先看全貌，再按路径暂存，最后检查完整的暂存差异。

~~~bash
git status --short
git diff -- src/reports.py tests/test_report_scope.py

git add src/reports.py tests/test_report_scope.py
git diff --cached           # 只应出现本次修复的文件和代码块
git diff --cached --check   # 检查空白错误和遗留的冲突标记
~~~

## 把提交和验收证据绑在同一个 ID 上

对准备提交的同一份内容跑完测试，再创建提交：

~~~bash
git commit -m "fix(reports): scope report reads by account"
git show --stat --oneline HEAD
~~~

提交 ID 是后续一切证据的锚点：CI 在哪个提交上运行、镜像由哪个提交构建、发布了哪个镜像，都要能追溯到它。若验收依赖提交后的 CI，就核对实际通过检查的是哪一个提交 ID，再晋级产物。任何会改变提交 ID 的操作（rebase、cherry-pick、squash）之后，旧 ID 上的检查结果不再自动适用于新提交。

commit message (提交说明) 描述改了什么、改的对象是谁。`fix(reports): ...` 是 Conventional Commits (约定式提交) 格式，属于团队约定，不是 Git 的要求；仓库若规定 squash、merge commit 或签名提交，按仓库策略执行。标题写得好不代表测试通过，审查要看实际的差异和测试覆盖。

## 整合前先看清两边：fetch 与三点比较

提交只在本地分支上。推送或发起合并前，先看远端 `main` 在此期间是否有了新提交：

- `git fetch`（获取）只更新 `origin/main` 这类远程跟踪引用，不改当前分支。
- `git pull`（拉取）在获取后立即按配置执行合并或变基。

更稳妥的做法是先获取，看清两边差异，再决定怎样整合：

~~~bash
git fetch origin
git log --left-right --oneline --graph HEAD...origin/main
~~~

三点写法 `HEAD...origin/main` 配合 `--left-right`，列出两边各自独有的提交：`<` 表示只能从当前 `HEAD` 到达，`>` 表示只能从 `origin/main` 到达。两点写法 `HEAD..origin/main` 只列远端独有的提交，看不出本地是否还有没推送的提交。

在本案例中，`>` 一侧出现了同事的提交 `perf(reports): defer report body`：为减少读取量，他把同一行改成了延迟加载报表正文。

## merge 还是 rebase

| 当前状态 | 常见做法 | 原因 |
| --- | --- | --- |
| 本地分支还没推送，只有自己用过 | 按仓库策略 rebase (变基) 或 merge (合并) | rebase 把本地提交重放到新基点上，生成新的提交 ID；merge 保留两侧历史，必要时生成合并提交 |
| 别人已基于这个分支继续提交 | 先协调，通常不改写共享提交 | 改写后提交 ID 不同，别人的分支仍基于旧提交，要重新整合两条历史 |
| 仓库要求保留合并节点 | `git merge --no-ff` | 普通 merge 在可快进时只移动分支；`--no-ff` 为这次合并创建节点 |

两个容易误解的边界：如果当前提交是远端提交的祖先（本地没有新提交），`git merge` 会 fast-forward (快进)，直接移动分支，不新增合并提交；如果远端没有本地缺少的提交，就没有需要整合的东西，也不会凭空生成合并节点。具体用哪种，以仓库现行策略为准，不要套用某个通用分支模型。

本案例的分支还没推送，团队约定用 rebase：`git rebase origin/main`。

## 冲突按语义不变量解决

rebase 在 `src/reports.py` 上停了下来，因为两边改了同一行：

~~~text
<<<<<<< HEAD
    report = session.get(Report, report_id, options=[defer(Report.body)])
=======
    report = session.scalar(
        select(Report).where(
            Report.account_id == account_id,
            Report.report_id == report_id,
        )
    )
>>>>>>> 6ab06f8 (fix(reports): scope report reads by account)
~~~

两侧各守着一件事：上游要延迟加载正文，修复要同时按账户和报表过滤。解决冲突的标准是**语义不变量**，而不是挑一侧：无论上游怎样改写这段查询，结果都必须同时保留两个过滤条件，再合进上游真正想要的改动：

~~~python
    report = session.scalar(
        select(Report)
        .options(defer(Report.body))
        .where(
            Report.account_id == account_id,
            Report.report_id == report_id,
        )
    )
~~~

**rebase 时 ours 和 theirs 是反的。** rebase 把本地提交一个个重放到上游之上，所以冲突里的 `HEAD`（ours）是**上游**的版本，theirs 才是正在重放的本地修复。上面的 `HEAD` 一侧正是同事那行 `session.get`。不看内容就执行 `git checkout --ours src/reports.py`，等于把越权缺陷原样恢复；整块接受 theirs，则丢掉了上游的改动。不理解冲突内容时，两种整块接受都不要做。

解决后的检查顺序：

1. 用 `git diff --cc` 和源文件确认冲突标记都已清除。
2. 运行测试；跨账户反例会拦住误选上游一侧的结果。
3. 暂存并继续：`git add src/reports.py`，然后 `git rebase --continue`（如果进行的是 merge，用 `git merge --continue`；先看 `git status` 确认当前操作）。

rebase 完成后，修复提交从 `6ab06f8` 变成了新的 `c4f2a91`。CI 必须在新 ID 上重新验证，上一节“证据绑定提交 ID”的规则在这里生效。

**想放弃整合时：**

- `git rebase --abort` 回到变基前的状态。
- `git merge --abort` 回到合并前的状态。但如果开始合并时已有未提交的改动，Git 在某些情况下无法完整还原它们，所以整合前最好让工作区保持干净。

## 临时搁置与跨分支带修复：stash 与 cherry-pick

这是两种不同的需求。

**临时切走：`git stash`。** 修复做到一半要去处理别的任务时：

- `git stash push -m "report scope in progress"` 保存已跟踪文件在工作区和暂存区的改动；默认不含未跟踪文件，需要时加 `-u`。
- `git stash apply` 默认只恢复改动内容，不恢复“哪些改动原先已暂存”；要同时恢复暂存划分，用 `git stash apply --index`。
- `apply` 保留这条 stash 记录；`pop` 在应用成功后删除它。
- 应用后检查状态和冲突。stash 不是备份，重要工作仍应保存在提交里。

**把修复带到另一个分支：`git cherry-pick`。** `git cherry-pick <commit>` 把指定提交引入的改动应用到当前分支，并创建一个**新**提交。它适合把已审查的修复带到维护分支；新提交的 ID 与原提交不同，所以维护分支上要重新记录检查在哪个提交上运行、构建用的是哪个提交。

## 按变化所在层恢复

出错时，先判断要撤销的改动停在哪一层，再选命令。这张表是本领域恢复命令的权威版本：

| 改动停在哪 | 想做什么 | 命令 | 效果与风险 |
| --- | --- | --- | --- |
| 暂存区 | 取消暂存，保留编辑 | `git restore --staged <path>` | 该路径的暂存内容恢复为 HEAD 的版本；工作区不变 |
| 工作区 | 丢弃未暂存的编辑 | `git restore <path>` | 工作区恢复为暂存区的版本；被覆盖的编辑**无法找回** |
| 未共享的本地提交 | 重新划分提交（如把两个合成一个） | `git reset --soft` 或 `--mixed <target>` | 分支移到目标；改动留在暂存区或工作区 |
| 未共享的本地提交 | 连同改动一起丢弃 | `git reset --hard <target>` | 先确认工作区内容可以丢弃 |
| 已共享的提交 | 撤销它的效果 | `git revert <commit>` | 新增一个反向提交，原提交留在历史中供审计 |
| 已共享的合并提交 | 撤销这次合并 | `git revert -m 1 <merge-commit>` | `-m` 指定以哪个父提交为主线；先检查反向差异，以及它对之后再次合并同一分支的影响 |
| 分支被误移 | 找回原来的提交 | `git reflog`，再 `git branch recovery/report-scope <commit-id>` | reflog 只是本地记录，会过期，不同步到远端 |

撤销共享历史用 revert，不要把远端分支强制指回旧位置：别人可能已经基于那些提交工作了。

`git reset` 的三个选项决定它除了移动分支之外还动哪几层：

| 选项 | 分支引用 | 暂存区 | 工作区 |
| --- | --- | --- | --- |
| `--soft <target>` | 移到目标 | 保留 | 保留 |
| `--mixed <target>`（默认） | 移到目标 | 重置为目标内容 | 保留 |
| `--hard <target>` | 移到目标 | 重置为目标内容 | 全部改成目标版本：丢弃受跟踪文件的改动，可能覆盖同名的未跟踪文件，目标中没有的受跟踪文件被删除 |

找回误移的提交后，先 `git show --stat recovery/report-scope` 检查这份快照，再决定是否推送。三个命令的分工可以这样记：reset 移动当前分支（并可重置暂存区和工作区），restore 恢复文件内容，revert 新增反向提交。

## 提交之后：交给构建，Git 管不到的部分

修复提交为构建系统提供了固定输入，但它还不是部署产物。之后要由 CI 用这个提交构建镜像，记录镜像摘要，验证并晋级那一份镜像。若仓库要求通过 PR 和状态检查后再发布，这些检查就是晋级条件。

Git 命令也只改变工作区、暂存区、提交和引用。`git revert` 撤回的是源码，不会撤销已执行的数据库迁移、已发布的镜像或其他生产副作用；这些要靠发布侧的回退和兼容设计处理。

下一章[源码怎样变成可运行、可追溯的容器镜像？](container-images-and-builds.md)讲怎样从这个提交构建出可追溯的镜像；本主线把修复版本的镜像摘要记作 `d-new`。镜像怎样按摘要晋级见[已验证的产物怎样原样晋级到生产？](build-once-promote-by-digest.md)，发布后能撤回什么见[新版本怎样逐步放量，出问题时能撤回什么？](canary-rollout-and-rollback.md)。

> [!info]- 来源
> - **工作区、暂存区与提交的差异；`--check` 检查空白错误与冲突标记**（“一次改动停在哪一层”“被测快照必须等于提交快照”“只把这次修复放进提交”）：Git 手册 [git-status](https://git-scm.com/docs/git-status)、[git-diff](https://git-scm.com/docs/git-diff)、[git-add](https://git-scm.com/docs/git-add)、[git-commit](https://git-scm.com/docs/git-commit)、[git-worktree](https://git-scm.com/docs/git-worktree)，核对于 2026-11-06。
> - **fetch 与 pull、三点与两点区间、merge 快进与 `--no-ff`、`merge --abort` 的限制**（“整合前先看清两边”“merge 还是 rebase”“冲突按语义不变量解决”）：Git 手册 [git-fetch](https://git-scm.com/docs/git-fetch)、[git-pull](https://git-scm.com/docs/git-pull)、[git-log](https://git-scm.com/docs/git-log)、[git-merge](https://git-scm.com/docs/git-merge)，核对于 2026-11-06。
> - **rebase 重放提交、冲突时 ours/theirs 对调**（“冲突按语义不变量解决”）：Git 手册 [git-rebase](https://git-scm.com/docs/git-rebase)，“the side reported as ours is the so-far rebased series … and theirs is the working branch”；冲突标记的形式与 rebase 后提交 ID 改变为本地 Git 2.56.1 演示结果（文中 ID 为示意值），2026-11-25。
> - **stash 的范围与 `--index`、cherry-pick 创建新提交**（“临时搁置与跨分支带修复”）：Git 手册 [git-stash](https://git-scm.com/docs/git-stash)、[git-cherry-pick](https://git-scm.com/docs/git-cherry-pick)，核对于 2026-11-06。
> - **restore、reset 三种模式、revert 与 `-m`、reflog**（“按变化所在层恢复”）：Git 手册 [git-restore](https://git-scm.com/docs/git-restore)、[git-reset](https://git-scm.com/docs/git-reset)、[git-revert](https://git-scm.com/docs/git-revert)、[git-reflog](https://git-scm.com/docs/git-reflog)，核对于 2026-11-06，`--hard` 的措辞按本地 Git 2.56.1 手册；`restore`/`switch` 需要 Git 2.23 及以上。
