# How do you undo or recover a Git change safely? / 怎样安全撤销或找回 Git 改动？

Choose by where the change lives and whether other people already rely on it. Revert records a new change that undoes an existing commit. Reset moves a reference and can update local state. The reflog can help locate earlier local reference values. / 先看改动在哪里，以及别人是否已依赖它。revert 新增一个撤销已有提交的提交。reset 移动引用，也可能更新本地状态。reflog 可以帮助定位本地引用先前的位置。

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

[Back to the main question / 返回主问题](git-essentials.md).
