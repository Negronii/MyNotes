# Git 怎样把通过验收的报表改动变成可追溯提交？

**案例：** 报表服务读取报表时漏了租户条件：`tenant-b` 猜中 `tenant-a` 的报表 ID 42，也能读到内容。开发者修复了查询并补上测试，检查通过后，要用 Git 把这份已审查的源码快照变成可追溯的提交。提交为构建系统提供固定输入，但它还不是部署产物：之后还要记录由它构建出的镜像摘要，并对那份镜像做验证和晋级。另外，Git 命令只改变工作区、暂存区、提交和引用，不会撤销数据库迁移、已发布的镜像或其他生产副作用。

先区分 Git 的几层状态：working tree（工作区）是磁盘上正在编辑的文件；index（暂存区）是准备放进下一次提交的快照；commit（提交）记录一份完整的目录快照（tree）及其父提交；branch（分支）是指向某个提交的可移动引用。本章只讨论在分支上工作的常见情况：`HEAD` 指向当前分支，分支指向当前提交；提交成功后，分支移动到新提交。分清改动停在哪一层，后面才能选对恢复命令。

创建分支只是新建一个指向提交的引用：`git switch -c <name>` 不会把未提交的改动保存成快照，这些改动会跟着你留在工作区和暂存区。切换任务前若要保护它们，应先提交，或用 `git stash` 保存，之后再核对恢复结果。单独执行 `git add` 也不会形成独立的提交或 stash。

下面只追踪同一个文件的三个版本：`v0` 是原内容，`v1` 加上租户限定，`v2` 又补了错误处理。表中每格是该层保存的文件内容，并非提交号。

| 执行到哪一步 | Working tree | Index | HEAD 提交中的文件 |
| --- | --- | --- | --- |
| 编辑为 `v1` | `v1` | `v0` | `v0` |
| 执行 `git add` | `v1` | `v1` | `v0` |
| 再编辑为 `v2`，没有再次 add | `v2` | `v1` | `v0` |
| 执行 `git commit` | `v2` | `v1` | `v1` |

`git add` 复制的是执行那一刻的文件内容，之后继续编辑不会改变 index；所以最后一步只提交了租户限定，错误处理仍是未暂存的改动。`git diff` 对照工作区与 index，`git diff --cached` 对照 index 与 HEAD。提交前分别看两份差异，才能知道哪些改动会进入这次提交。测试通常读取 working tree 中的文件，因此 `v2` 通过测试，不能说明只含 `v1` 的提交也能通过。验收时要让被测内容与准备提交的快照一致；若工作区混有其他改动，可以把待提交快照放到隔离目录（例如另一个 `git worktree`）中测试。


## 把一个小修复明确放进暂存区

回到报表案例。在示意仓库中，本次修复只包含 `src/reports.py` 的租户限定查询和 `tests/test_report_scope.py` 的非所有者断言。先看仓库里是否混有其他任务的改动，再看这两个文件的准确差异：

~~~bash
git status --short
git diff -- src/reports.py tests/test_report_scope.py
~~~

按路径暂存可以只选本次修复的文件，但要注意两点：index 中原有的其他暂存改动不会被移除；所选文件当前的全部修改都会被暂存，包括与本次修复无关的部分。因此暂存后必须检查完整的 `git diff --cached`，确认其中只有属于本次修复的文件和代码块。

~~~bash
git add src/reports.py tests/test_report_scope.py
git diff --cached
git diff --cached --check
git status --short
~~~

`git diff --cached --check` 检查差异中的空白错误和遗留的冲突标记。先对准备提交的同一份内容跑完项目测试，再创建提交；若验收依赖提交后的 CI，就核对实际通过检查的是哪个提交 ID，之后才晋级产物。

~~~bash
git commit -m "fix(reports): enforce tenant-scoped reads"
git show --stat --oneline HEAD
git log --oneline --graph --decorate -8
~~~


commit message（提交说明）描述改了什么、改的对象是谁。`fix(reports): ...` 采用的是 Conventional Commits（约定式提交）格式，属于团队约定，不是 Git 的要求。仓库若规定 squash、merge commit 或签名提交，就按仓库策略执行。代码审查应看实际的 diff（差异）和测试覆盖范围；提交标题写得好不代表测试已通过。

## 先检查远端，再选择 merge 或 rebase

提交只存在于本地分支。推送或发起合并前，要先看远端 `main` 在此期间是否有了新提交。`git fetch`（获取）只更新 `origin/main` 这类远程跟踪引用，不改当前分支；`git pull`（拉取）则在获取后立即按配置执行合并或变基。更稳妥的做法是先获取、查看两边差异，再选择整合方式：

~~~bash
git fetch origin
git log --left-right --oneline --graph HEAD...origin/main
~~~

三点写法 `HEAD...origin/main` 配合 `--left-right`，会列出两边各自独有的提交：`<` 表示只能从当前 `HEAD` 到达，`>` 表示只能从 `origin/main` 到达。两点写法 `HEAD..origin/main` 只列远端独有的提交，单靠它看不出本地是否也有尚未推送的提交。

| 当前状态 | 常见做法 | 原因 |
|---|---|---|
| 更新尚未推送的本地分支 | 按仓库策略 rebase（变基）或 merge（合并） | 变基会重放提交并生成新的提交 ID；合并保留两侧历史，必要时生成合并提交 |
| 多人已经基于该分支继续提交 | 先协调，通常不改写共享提交 | 其他人的分支仍基于旧提交；改写后的提交 ID 不同，需要重新整合两条历史 |
| 仓库需要保留合并节点 | 需要整合时使用 `merge --no-ff` | 普通 merge 在可快进时只移动分支；`--no-ff` 会为这次合并创建节点 |

例如修复所在的 `fix/report-tenant-scope` 分支只有自己用过、还没推送，就可以按团队约定执行 `git rebase origin/main`。也可以用 `git merge origin/main` 整合；如果当前提交是远端提交的祖先（本地没有新提交），合并会 fast-forward（快进），直接移动分支而不新增合并提交。团队若要求这次整合留下合并节点，可用 `git merge --no-ff origin/main`；如果远端没有本地缺少的提交，则无需整合，也不会凭空生成合并节点。merge 和 rebase 都可能产生冲突；具体用哪种，以仓库现行策略为准，不要套用某个通用分支模型。

发生冲突时，先看带冲突标记的源文件和 `git diff --cc`。在报表案例中，无论远端怎样改写这段查询，解决后的代码都必须同时保留“按当前用户所属租户过滤”和“按报表 ID 过滤”两个条件，再处理与远端其他修改真正冲突的部分。检查解决冲突后的文件，运行相应测试，再暂存并继续当前操作。下面这段针对正在进行的 rebase：

~~~bash
git add src/reports.py
git rebase --continue
~~~

若正在进行的是 merge，解决并暂存冲突后用 `git merge --continue` 完成合并；先看 `git status` 确认当前操作。

若想放弃整合：合并未完成前可用 `git merge --abort` 回到合并前的状态。本例开始合并时工作区是干净的，所以能完整恢复；如果开始时已有未提交改动，Git 某些情况下无法完整还原它们。变基未完成前可用 `git rebase --abort` 回到变基前。不要在没弄懂冲突内容时整块接受 ours 或 theirs。

## stash 与 cherry-pick 解决不同问题

修复进行到一半时，可能要临时切去处理别的任务；修复完成后，也可能要把它带到另一个分支。这是两种不同的需求。临时切走时，`git stash push -m "report scope in progress"` 保存已跟踪文件的工作区和暂存区状态；默认不含未跟踪文件，需要时加 `-u`。`git stash apply` 默认只恢复改动内容，不恢复原先哪些改动已暂存；需要同时恢复 index 时用 `git stash apply --index`。`apply` 会保留这条 stash 记录，`pop` 则在应用成功后删除它。应用后要检查状态和冲突。stash 不是备份，重要工作仍应保存在提交或其他持久位置。

`git cherry-pick <commit>`（挑选提交）把指定提交引入的改动应用到当前分支，并创建一个新提交。它适合把已审查的报表修复带到维护分支；但新提交的 ID 与原提交不同，所以在维护分支上要重新记录：检查是在哪个提交上运行的，部署构建又用的是哪个提交。

## 按变化所在层恢复

出错时，先判断要撤销的改动停在哪一层（工作区、暂存区、本地提交还是已共享的提交），再选命令。若只是暂存了不想提交的修改，用 `git restore --staged <path>` 将该路径的 index 内容恢复为 HEAD 中的版本，工作区内容保留。若只丢弃工作区的未暂存编辑，用 `git restore <path>` 将工作区该路径恢复为 index 中的版本；这些未暂存编辑会被覆盖、无法找回。对已经共享的提交，用 `git revert <commit>` 添加一个反向提交，原提交留在历史中供审计。普通提交直接指定即可；撤销 merge commit 时必须用 `-m` 指定以哪个父提交为主线，例如 `git revert -m 1 <merge-commit>`，并事先检查生成的反向差异，以及它会怎样影响之后再次合并同一分支。撤销共享历史通常用 revert，不要把远端分支强制指回旧位置。

`git reset` 则移动当前分支，并按选项决定是否同时重置暂存区和工作区：

| reset 方式 | branch 引用 | 暂存区 | 工作区 |
|---|---|---|---|
| `--soft <target>` | 移到目标 | 保留 | 保留 |
| `--mixed <target>` | 移到目标 | 重置为目标内容 | 保留 |
| `--hard <target>` | 移到目标 | 重置为目标内容 | 丢弃受跟踪文件的改动；挡在路径上的未跟踪文件也会被删除 |

`git reset --hard <target>` 只应用于未共享的本地提交，并且要先确认工作区内容可以丢弃。若只是想重新划分提交（例如把两个提交合成一个），`--soft` 或 `--mixed` 更合适。若误把分支移走了，可以用 `git reflog` 找到原来的提交，再新建分支指向它：

~~~bash
git reflog
git branch recovery/report-scope <commit-id>
git show --stat recovery/report-scope
~~~

reflog 只是本地的引用移动记录，旧条目会过期，也不会同步到远端，不能当备份。把找回的内容推送到共享仓库前，先检查这份快照。总结三条命令的分工：reset 移动当前分支（并可重置 index 和工作区），restore 恢复文件内容，revert 新增反向提交。

修复提交完成后就进入构建和发布。CI 可以在开发分支、PR 或共享分支上运行；发布流程应记录实际用于构建的那个提交。若仓库要求通过 PR 和状态检查后再发布，就把这些检查作为晋级条件。容器摘要和晋级过程见[Docker 如何把该提交构建成固定镜像？](../infrastructure/docker-operations.md)与[如何晋级已验证的报表服务产物？](../infrastructure/application-deployment-and-ci-cd.md)。

> [!info]- 来源
> - Git 官方手册：[status](https://git-scm.com/docs/git-status)、[diff](https://git-scm.com/docs/git-diff)、[add](https://git-scm.com/docs/git-add)、[commit](https://git-scm.com/docs/git-commit)，checked 2026-11-06：工作区、index 和提交差异。
> - Git 官方手册：[fetch](https://git-scm.com/docs/git-fetch)、[pull](https://git-scm.com/docs/git-pull)、[merge](https://git-scm.com/docs/git-merge)、[rebase](https://git-scm.com/docs/git-rebase)，checked 2026-11-06：远端跟踪、整合和历史重放。
> - Git 官方手册：[reset](https://git-scm.com/docs/git-reset)、[restore](https://git-scm.com/docs/git-restore)、[revert](https://git-scm.com/docs/git-revert)、[reflog](https://git-scm.com/docs/git-reflog)、[stash](https://git-scm.com/docs/git-stash)、[cherry-pick](https://git-scm.com/docs/git-cherry-pick)，checked 2026-11-06：各命令的状态影响和恢复范围；本机 Git 2.56.0。
