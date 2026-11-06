# Git 怎样把通过验收的报表改动变成可追溯提交？

修复 report 42 的租户条件并通过相关检查后，Git 能把已审查的源码快照变成可复查的提交。这个提交给构建系统提供固定输入，但它还不是部署产物：之后要记录由它构建出的镜像摘要，并验证、晋级那份镜像。Git 命令改变工作区、暂存区、提交或引用；它不撤销数据库迁移、已发布镜像或生产副作用。

branch（分支）是指向提交的可移动引用；working tree（工作区）保存文件，index（暂存区）保存下一次提交的快照，commit（提交）固定一棵树及父提交。区分这几层，才能选择正确的恢复动作。

创建分支只建立一个指向提交的引用，`git switch -c <name>` 也不会把未提交的工作区或暂存区改动保存成快照。要在切换任务前保护这类改动，应先提交或暂存保存，再核对恢复后的状态。

~~~mermaid
flowchart TD
    A[工作区：改了查询与测试] --> B[检查 diff 并选择文件]
    B --> C[暂存区：本次提交精确内容]
    C --> D[提交：固定源码树和父提交]
    D --> E[CI（持续集成）以提交号构建镜像]
    E --> F[镜像摘要与提交号形成可追溯映射]
    D --> G{哪里需要修复？}
    G -->|仅未共享的本地历史| H[reset / rebase]
    G -->|已经共享的提交| I[revert 新增反向提交]
~~~

## 把一个小修复明确放进暂存区

在示意仓库中，改动只包含 `src/reports.py` 的租户限定查询和 `tests/test_report_scope.py` 的非所有者断言。先查看仓库是否混有其他任务，再查看准确的差异：

~~~bash
git status --short
git diff -- src/reports.py tests/test_report_scope.py
~~~

逐文件暂存能避免把本地配置、调试输出或其他人的改动混进报告修复：

~~~bash
git add src/reports.py tests/test_report_scope.py
git diff --cached
git diff --cached --check
git status --short
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
| 多人已经基于该分支继续提交 | 先协调，通常不改写共享提交 | 改写会让其他人的父提交失效并要求重新整合 |
| 仓库需要显示集成节点 | merge | 合并提交可显式记录两条历史如何接合 |

例如仅有自己未推送的 `fix/report-tenant-scope` 分支，可以按团队约定 `git rebase origin/main`。若团队需要保留合并关系，则 `git merge origin/main`。两者都可能产生冲突；不要用某种分支模型替代仓库现行策略。

发生冲突时，先看带冲突标记的源文件及 `git diff --cc`。在 report42 的例子里，必须保留当前主体与报表 ID 两个条件，再解决与远端其他调整的真实冲突。检查文件、运行相应测试后暂存并继续：

~~~bash
git add src/reports.py
git rebase --continue
~~~

示例从干净工作区开始。合并未完成前可 `git merge --abort` 尝试重建合并前状态；如果开始合并时已有未提交改动，Git 在某些情况下无法完整恢复它们。变基未完成前可 `git rebase --abort`。不要把未理解的冲突整块接受为 ours 或 theirs。

## stash 与 cherry-pick 解决不同问题

临时切走时，`git stash push -m "report scope in progress"` 保存已跟踪文件的工作区和暂存区状态；默认不含未跟踪文件，需要时加 `-u`。`git stash apply` 默认重新应用改动但不保证恢复原先暂存状态；需要尽量恢复 index（暂存区）时用 `git stash apply --index`。`apply` 保留记录，`pop` 在应用成功后移除记录。应用后检查状态和冲突，不要把 stash 当成备份；重要工作还应保存在提交或其他持久位置。

`git cherry-pick <commit>`（挑选提交）把指定提交所引入的改动应用到当前分支，并创建一个新的提交。它适合把已审查的报表修复移到维护分支，但新提交 ID 不同，应记录实际运行的检查和部署构建对应的目标提交。

## 按变化所在层恢复

若只是暂存了不想提交的文件，用 `git restore --staged <path>` 保留工作区内容并移出 index；若只丢弃工作区的未暂存编辑，用 `git restore <path>`，该路径内容会被覆盖。对已经提交的共享修复，用 `git revert <commit>` 添加一个反向提交，保留原提交供历史审计。普通提交可直接指定；撤销 merge commit 时须选择主线父提交，例如 `git revert -m 1 <merge-commit>`，并先检查这个反向差异以及后续合并会受什么影响。回滚共享历史时通常用 revert，不要直接把远端分支强制指回旧位置。

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

变更经 PR 和状态检查进入共享分支后，CI 才能用这个确切的提交构建镜像。容器摘要和晋级过程见[Docker 如何把该提交构建成固定镜像？](../infrastructure/docker-operations.md)与[如何晋级已验证的报表服务产物？](../infrastructure/application-deployment-and-ci-cd.md)。

> [!info]- 来源
> - Git 官方手册：[status](https://git-scm.com/docs/git-status)、[diff](https://git-scm.com/docs/git-diff)、[add](https://git-scm.com/docs/git-add)、[commit](https://git-scm.com/docs/git-commit)，checked 2026-11-06：工作区、index 和提交差异。
> - Git 官方手册：[fetch](https://git-scm.com/docs/git-fetch)、[pull](https://git-scm.com/docs/git-pull)、[merge](https://git-scm.com/docs/git-merge)、[rebase](https://git-scm.com/docs/git-rebase)，checked 2026-11-06：远端跟踪、整合和历史重放。
> - Git 官方手册：[reset](https://git-scm.com/docs/git-reset)、[restore](https://git-scm.com/docs/git-restore)、[revert](https://git-scm.com/docs/git-revert)、[reflog](https://git-scm.com/docs/git-reflog)、[stash](https://git-scm.com/docs/git-stash)、[cherry-pick](https://git-scm.com/docs/git-cherry-pick)，checked 2026-11-06：各命令的状态影响和恢复范围；本机 Git 2.56.0。
