# Git 怎样把通过验收的报表改动变成可追溯提交？

修复 report 42 的租户条件并通过相关检查后，Git 能把已审查的源码快照变成可复查的提交。这个提交给构建系统提供固定输入，但它还不是部署产物：之后要记录由它构建出的镜像摘要，并验证、晋级那份镜像。Git 命令改变工作区、暂存区、提交或引用；它不撤销数据库迁移、已发布镜像或生产副作用。

branch（分支）是指向提交的可移动引用；working tree（工作区）保存文件，index（暂存区）保存下一次提交的快照，commit（提交）固定一棵树及父提交。本章采用普通分支工作方式：`HEAD` 指向当前分支，分支指向当前提交；成功创建提交后，分支移动到新提交。区分这几层，才能选择正确的恢复动作。

创建分支只建立一个指向提交的引用，`git switch -c <name>` 也不会把未提交的工作区或暂存区改动保存成快照。要在切换任务前保护这类改动，应先提交，或用 `git stash` 保存，再核对恢复后的状态。仅执行 `git add` 不会把改动保存成独立的提交或 stash。

下面只追踪同一个文件的三个版本：`v0` 是原内容，`v1` 加上租户限定，`v2` 又补了错误处理。表中每格是该层保存的文件内容，并非提交号。

| 执行到哪一步 | Working tree | Index | HEAD 提交中的文件 |
| --- | --- | --- | --- |
| 编辑为 `v1` | `v1` | `v0` | `v0` |
| 执行 `git add` | `v1` | `v1` | `v0` |
| 再编辑为 `v2`，没有再次 add | `v2` | `v1` | `v0` |
| 执行 `git commit` | `v2` | `v1` | `v1` |

`git add` 复制的是执行当时的内容。之后继续编辑，index 不会跟着变化；所以最后一步只提交了租户限定，错误处理仍是未暂存改动。`git diff` 对照工作区与 index，`git diff --cached` 对照 index 与 HEAD。提交前分别看两份差异，才能知道哪些改动会进入这次提交。测试通常读取 working tree；在 `v2` 上通过测试，不能据此认定只含 `v1` 的提交也通过。验收时要让被测内容与准备提交的快照一致；若工作区混有其他改动，可在隔离目录验证待提交快照。


## 把一个小修复明确放进暂存区

在示意仓库中，改动只包含 `src/reports.py` 的租户限定查询和 `tests/test_report_scope.py` 的非所有者断言。先查看仓库是否混有其他任务，再查看准确的差异：

~~~bash
git status --short
git diff -- src/reports.py tests/test_report_scope.py
~~~

逐文件暂存用于选择此次修复的路径；它会保留 index 中已经存在的其他暂存改动，也会收录所选文件当前的全部修改。因此必须检查完整的 `git diff --cached`：只应出现属于本次修复的文件与代码块，包含既有暂存内容的情况也一样。

~~~bash
git add src/reports.py tests/test_report_scope.py
git diff --cached
git diff --cached --check
git status --short
~~~

`git diff --cached --check` 检查差异中的空白错误和冲突标记。先对准备提交的同一份内容完成项目测试，再创建提交；若使用提交后的 CI 验收，则核对实际通过检查的提交 ID，之后才晋级产物。

~~~bash
git commit -m "fix(reports): enforce tenant-scoped reads"
git show --stat --oneline HEAD
git log --oneline --graph --decorate -8
~~~


commit message（提交说明）描述变化和对象，`fix(reports): ...` 属于可选的 Conventional Commits（常规提交说明格式），不是 Git 本身的要求。仓库策略若规定 squash、merge commit 或签名提交，就按该策略执行。代码审查应检查实际 diff（差异）和测试边界；提交标题不等于测试通过。

## 先检查远端，再选择 merge 或 rebase

`git fetch`（获取）更新远程跟踪引用但不改当前分支；`git pull`（拉取）执行获取后再按配置整合。可以先查看差异，再选择整合方式：

~~~bash
git fetch origin
git log --left-right --oneline --graph HEAD...origin/main
~~~

三点范围列出两边各自独有的提交；`<` 表示只在当前 `HEAD` 可达，`>` 表示只在 `origin/main` 可达。两点写法 `HEAD..origin/main` 只列远端独有提交，不能单独判断本地是否也有未发布提交。

| 当前状态 | 常见做法 | 原因 |
|---|---|---|
| 更新尚未发布的本地分支 | 按仓库政策 rebase（变基）或 merge（合并） | 变基重放提交会创建新提交 ID；合并保留双侧历史和可能的汇合点 |
| 多人已经基于该分支继续提交 | 先协调，通常不改写共享提交 | 其他人的分支仍基于旧提交；改写后的提交 ID 不同，需要重新整合两条历史 |
| 仓库需要保留合并节点 | 需要整合时使用 `merge --no-ff` | 普通 merge 在可快进时只移动分支；`--no-ff` 会为这次合并创建节点 |

例如仅有自己未推送的 `fix/report-tenant-scope` 分支，可以按团队约定 `git rebase origin/main`。也可以用 `git merge origin/main` 整合；如果当前提交是远端提交的祖先，它可以 fast-forward（快进），直接移动分支而不新增合并提交。若团队要求这次整合保留合并节点，可用 `git merge --no-ff origin/main`；如果双方已经无须整合，则不会凭空生成合并节点。merge 和 rebase 都可能产生冲突；不要用某种分支模型替代仓库现行策略。

发生冲突时，先看带冲突标记的源文件及 `git diff --cc`。在 report42 的例子里，必须保留当前主体与报表 ID 两个条件，再解决与远端其他调整的真实冲突。检查解决冲突后的文件，运行相应测试，再暂存并继续当前操作。下面这段针对正在进行的 rebase：

~~~bash
git add src/reports.py
git rebase --continue
~~~

若正在进行的是 merge，解决并暂存冲突后用 `git merge --continue` 完成合并；先看 `git status` 确认当前操作。

示例从干净工作区开始。合并未完成前可 `git merge --abort` 尝试重建合并前状态；如果开始合并时已有未提交改动，Git 在某些情况下无法完整恢复它们。变基未完成前可 `git rebase --abort`。不要把未理解的冲突整块接受为 ours 或 theirs。

## stash 与 cherry-pick 解决不同问题

临时切走时，`git stash push -m "report scope in progress"` 保存已跟踪文件的工作区和暂存区状态；默认不含未跟踪文件，需要时加 `-u`。`git stash apply` 默认重新应用改动但不保证恢复原先暂存状态；需要尽量恢复 index（暂存区）时用 `git stash apply --index`。`apply` 保留记录，`pop` 在应用成功后移除记录。应用后检查状态和冲突，不要把 stash 当成备份；重要工作还应保存在提交或其他持久位置。

`git cherry-pick <commit>`（挑选提交）把指定提交所引入的改动应用到当前分支，并创建一个新的提交。它适合把已审查的报表修复移到维护分支，但新提交 ID 不同，应记录实际运行的检查和部署构建对应的目标提交。

## 按变化所在层恢复

若只是暂存了不想提交的修改，用 `git restore --staged <path>` 将该路径的 index 内容恢复为 HEAD 中的版本，工作区内容保留。若只丢弃工作区的未暂存编辑，用 `git restore <path>` 将工作区该路径恢复为 index 中的版本；该路径内容会被覆盖。对已经提交的共享修复，用 `git revert <commit>` 添加一个反向提交，保留原提交供历史审计。普通提交可直接指定；撤销 merge commit 时须选择主线父提交，例如 `git revert -m 1 <merge-commit>`，并先检查这个反向差异以及后续合并会受什么影响。回滚共享历史时通常用 revert，不要直接把远端分支强制指回旧位置。

| reset 方式 | branch 引用 | 暂存区 | 工作区 |
|---|---|---|---|
| `--soft <target>` | 移到目标 | 保留 | 保留 |
| `--mixed <target>` | 移到目标 | 重置为目标内容 | 保留 |
| `--hard <target>` | 移到目标 | 重置为目标内容 | 丢弃与目标不符的受跟踪改动，也可能覆盖路径 |

在未共享的本地提交上，确认工作区内容可丢弃后才考虑 `git reset --hard <target>`。若只需改提交边界，`--soft` 或 `--mixed` 更合适。若误移 branch 指针，可先查看 `git reflog` 找回旧提交，再用新 branch 保住它：

~~~bash
git reflog
git branch recovery/report-scope <commit-id>
git show --stat recovery/report-scope
~~~

reflog 是本地引用移动记录，会过期，不是远端备份。恢复到共享存储前先检查保住的快照。Git 对 reset、restore、revert 的职责有明确区分：reset 移动当前提交/重置 index，restore 改文件，revert 新增反向提交。

CI 可以在开发分支、PR 或共享分支上运行。发布流程应记录实际用于构建的提交；若仓库要求通过 PR 和状态检查后再发布，就把这些检查作为晋级条件。容器摘要和晋级过程见[Docker 如何把该提交构建成固定镜像？](../infrastructure/docker-operations.md)与[如何晋级已验证的报表服务产物？](../infrastructure/application-deployment-and-ci-cd.md)。

> [!info]- 来源
> - Git 官方手册：[status](https://git-scm.com/docs/git-status)、[diff](https://git-scm.com/docs/git-diff)、[add](https://git-scm.com/docs/git-add)、[commit](https://git-scm.com/docs/git-commit)，checked 2026-11-06：工作区、index 和提交差异。
> - Git 官方手册：[fetch](https://git-scm.com/docs/git-fetch)、[pull](https://git-scm.com/docs/git-pull)、[merge](https://git-scm.com/docs/git-merge)、[rebase](https://git-scm.com/docs/git-rebase)，checked 2026-11-06：远端跟踪、整合和历史重放。
> - Git 官方手册：[reset](https://git-scm.com/docs/git-reset)、[restore](https://git-scm.com/docs/git-restore)、[revert](https://git-scm.com/docs/git-revert)、[reflog](https://git-scm.com/docs/git-reflog)、[stash](https://git-scm.com/docs/git-stash)、[cherry-pick](https://git-scm.com/docs/git-cherry-pick)，checked 2026-11-06：各命令的状态影响和恢复范围；本机 Git 2.56.0。
