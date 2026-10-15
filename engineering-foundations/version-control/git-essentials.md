# Git Essentials / Git日常基础

Git records project snapshots and lets branches point to different lines of history. **工作区 / working tree**, **暂存区 / index**, **提交 / commit**, **分支 / branch**, **远端 / remote**, **合并 / merge**, and **变基 / rebase** are the core terms used below. Branches are movable references to commits. Inspect status before changing or discarding work.

Git用提交保存项目快照，分支是指向提交的可移动引用；合并、变基和撤销应按历史是否共享及工作区状态选择，改写或丢弃内容前先检查并保护本地改动。

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

### `git reset` vs. `git revert`

In its commit form, `git reset` moves the current branch reference and optionally resets the index and working tree. The mode controls which state changes:

| Mode | Branch reference | Index | Tracked working-tree changes |
|---|---|---|---|
| `--soft` | Moves to target | Kept | Kept |
| `--mixed` (default) | Moves to target | Reset to target | Kept |
| `--hard` | Moves to target | Reset to target | Reset to target; conflicting tracked edits are discarded |

~~~bash
git reset --soft HEAD~1
git reset --mixed HEAD~1
git reset --hard HEAD~1
~~~

Use reset to adjust local history or staging when that is the intended scope. `--hard` replaces the working tree and index with the target state and may overwrite untracked files; check `git status` and preserve needed work first. It does not mean “delete every untracked file.”

`git revert <commit>` creates a new commit that applies the inverse of an earlier commit. It is often a better fit for undoing changes already shared in a branch, although conflicts may still need resolution. Reverting a merge commit requires selecting a mainline parent.

### `git reflog`

The reflog records recent local updates to references such as `HEAD` and branch tips. It can help locate a commit after an accidental reset or branch deletion while the commit remains available.

~~~bash
git reflog
git branch recovery <commit>
~~~

Creating a branch preserves the recovered commit under a name; checking out a raw commit instead leaves HEAD detached. Reflogs are local and expire, so they are not a backup.

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
