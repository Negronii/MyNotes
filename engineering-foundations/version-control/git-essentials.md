# How do you integrate, revise, or recover Git history without losing work? / 如何在不丢失工作的前提下集成、修改或恢复 Git 历史？

Git stores snapshots behind movable branch references, while the working tree and index hold changes not yet committed. Choose merge or rebase based on whether others rely on the commits, and choose reset, revert, or reflog recovery according to which local or shared history state must change. These commands repair repository history and files; they do not roll back a deployed application, database migration, or external side effect. / Git 用提交保存快照，分支是可移动引用；工作区和暂存区保存尚未提交的修改。根据提交是否已被他人依赖选择合并或变基，再根据需要改变的是哪部分本地或共享历史选择 reset、revert 或 reflog 恢复。这些命令修复的是仓库历史和文件，不会回滚已部署应用、数据库迁移或外部副作用；生产恢复见[应用部署与持续交付](../infrastructure/application-deployment-and-ci-cd.md)。

## Core commands

| Command | Purpose |
|---|---|
| `git init` | Create an empty repository in the current directory |
| `git clone <url>` | Copy a repository and its history |
| `git status` | Show branch and working-tree state |
| `git add <path>` | Stage changes for the next commit |
| `git diff` | Show unstaged changes; use `--staged` for staged changes |
| `git commit -m "message"` | Record the staged snapshot |
| `git log --oneline --graph --decorate` | Inspect recent history and branch references |

Stage deliberately. `git add .` stages changes under the current directory; `git add -A` stages additions, modifications, and deletions in the repository. Review `git diff --staged` before committing.

## Remote operations

~~~bash
git remote add origin <url>
git fetch origin
git push -u origin main
git pull
~~~

`git fetch` updates remote-tracking references without integrating them into the current branch. `git pull` fetches and then integrates the selected upstream using the configured or requested fast-forward, merge, or rebase behavior; inspect its options when the result matters. Fetch first when you want to review incoming commits before integrating them.

## Branching

~~~bash
git branch feature/login       # create a branch
git switch feature/login       # switch branches
git switch -c feature/login    # create and switch
git branch -d feature/login    # delete only when Git considers it merged
git branch -D feature/login    # force-delete the branch reference
~~~

A feature branch is one collaboration approach. A team can instead integrate small changes directly or use a release-branch strategy. Git Flow adds long-lived branches such as `develop`; it can suit scheduled releases but adds merging and coordination. Choose according to release and integration needs rather than treating one strategy as universal.

## Merge vs. rebase

### `git merge`

Merge integrates another branch into the current branch. If possible, Git may fast-forward the current branch reference; otherwise it creates a merge commit that records both parent histories.

~~~bash
git switch main
git merge feature/login
~~~

~~~
A---B---C---M  main
     \     /
      D---E    feature/login
~~~

### `git rebase`

Rebase replays commits onto a new base. The replayed commits have new IDs because their parent history changes.

~~~bash
git switch feature/login
git rebase main
~~~

~~~
A---B---C              main
         \
          D'---E'      feature/login
~~~

| Situation | A common choice | Why |
|---|---|---|
| Integrating work while keeping both branch histories visible | Merge | Records the integration point when a merge commit is created |
| Updating an unpublished local branch | Rebase | Replays local commits on the updated base |
| Commits others have already based work on | Coordinate before rebasing | Rebase changes commit IDs and requires collaborators to reconcile history |

A rebase can be useful on a shared branch only when the team coordinates the history rewrite and remote update. The practical rule is to avoid rewriting commits others may rely on.

## Resolving conflicts

When Git cannot combine edits automatically, it marks the affected file:

~~~
<<<<<<< HEAD
const timeout = 3000;
=======
const timeout = 5000;
>>>>>>> feature/login
~~~

1. Inspect the conflict and decide how the changes should combine.
2. Remove the conflict markers and edit the final content.
3. Stage the resolved path with `git add <path>`.
4. Finish with `git commit` after a merge, or `git rebase --continue` during a rebase.

Use `git merge --abort` or `git rebase --abort` to stop an integration that is still in progress.

## Useful commands

### `git stash`

Save tracked working-tree changes temporarily when switching tasks or branches.

~~~bash
git stash push -m "work in progress"
git stash list
git stash apply       # keep the stash entry
git stash pop         # apply and remove the stash entry if successful
git stash drop        # discard a stash entry
~~~

Untracked files are not included by default; use `-u` when they should be included.

### `git cherry-pick`

Apply the change introduced by a selected commit to the current branch, creating a new commit.

~~~bash
git cherry-pick <commit>
~~~

## Undo or recover by state layer / 按状态层撤销与找回

First ask whether the change lives in the working tree, index, or commit history, and whether others already rely on the commit. For example, if a bad change is already on a shared branch, `git revert <commit>` records a new inverse change. It preserves the published commit identity. Reverting a merge commit requires choosing the mainline parent. Resolve conflicts and verify what the inverse change actually does.

For an unshared local commit, `git reset <target>` can move the current branch. Choose what else should change.

| Reset mode | Branch | Index | Working tree |
| --- | --- | --- | --- |
| `--soft` | Move to target | Keep | Keep |
| `--mixed` | Move to target | Set to target | Keep |
| `--hard` | Move to target | Set to target | Set to target, discarding tracked local edits that differ from the target and possibly overwriting untracked paths |

Use `git status` and save any edits you need before a hard reset. If a local branch moved by mistake, inspect `git reflog`, find the prior commit, and make it reachable again with `git branch recovery <commit>`. Inspect that new branch before applying or restoring anything. Reflogs are local and expire, so use another durable copy for backup. / 共享提交通常用 revert 产生新的撤销记录。只调整本地分支时，按需要保留的暂存区与工作区选择 reset 模式。误移动后可从 reflog 找旧提交并先用新分支保留。 [Git reset](https://git-scm.com/docs/git-reset) · [Git reflog](https://git-scm.com/docs/git-reflog)

## Pull request and code review workflow

A common workflow is to branch from the repository's integration branch, commit focused changes, push, open a pull request, review and revise, then merge using the repository's chosen method. The exact branch name and merge policy vary by project.

For commits, concise messages that describe the change help future readers. **Conventional Commits** is one optional convention, often paired with tooling that reads its prefixes:

~~~
feat(auth): refresh access tokens
fix(api): handle missing user
refactor(utils): extract date formatting
docs(readme): clarify setup
~~~

**See also:** [Agile and Scrum](../teamwork/agile-and-scrum.md) for team-process context, and [Frontend Testing](../../frontend/testing/frontend-testing.md) for CI checks in a pull request.

Sources: [Git pull](https://git-scm.com/docs/git-pull), [Git merge](https://git-scm.com/docs/git-merge), [Git rebase](https://git-scm.com/docs/git-rebase), [Git reset](https://git-scm.com/docs/git-reset), [Git revert](https://git-scm.com/docs/git-revert), [Git reflog](https://git-scm.com/docs/git-reflog), [Git stash](https://git-scm.com/docs/git-stash), and [Git cherry-pick](https://git-scm.com/docs/git-cherry-pick). Git manuals checked 2026-10-15.
