# Workspace isolation

A write task never edits, builds, or commits in the primary checkout. That checkout
belongs to the user and to other sessions. A write there can overwrite their
uncommitted work, and it can start from a stale base.

## Work only in a task worktree

Create the worktree and its task branch with `python3 "$GHFLOW_CLI" worktree create`.
It fetches the default branch and bases the new branch on `origin/<default-branch>`,
not on the local checkout. It also applies the project facts file's `worktree:`
declaration, so the task starts with the same copied files and setup commands as
every other child. Then do every read, edit, build, and commit in that worktree.

`worktree create` refuses an existing branch or path. That means the task is a
resumption: reuse the existing worktree instead of making a second one. On a
resumption, or when a handoff may already have prepared a worktree, use the
idempotent form: `python3 "$GHFLOW_CLI" worktree ensure <issue>`. It creates or
confirms the worktree, prints its path and `cd_command`, and returns the branch,
base, gates, and symbol locations.

`ghflow exec` refuses a Git write (`commit`, `add`, `reset`, `merge`, `rebase`,
…) in the primary checkout on the default branch. The refusal names
`worktree ensure`; pass `--allow-primary` only for a deliberate primary-checkout
maintenance change. A linked worktree, a feature branch in the primary checkout,
and read-only Git commands are unaffected.

## A stale local checkout is not a reason to skip the worktree

A primary checkout commonly sits behind `origin`. Do not work around that by
reading files with `git show origin/...`, `git grep origin/...`, or
`git diff <rev>..origin/...` as a substitute storage area. Those reads create no
branch, so the task cannot commit the edit it planned, and the session ends with
nothing published. Create the worktree first and read the files there.

If you need to know what changed upstream before you start, read it with `git log`
or `git diff --stat` on the base revision, then create the worktree and read the
files themselves from it.

## Review worktrees

A review may use a detached worktree prepared with `review prepare`. It still does
not edit the primary checkout, and it does not edit the reviewed branch.
