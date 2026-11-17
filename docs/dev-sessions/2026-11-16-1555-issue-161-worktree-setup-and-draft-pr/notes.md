# issue-161-worktree-setup-and-draft-pr

## Resume here

- Issue: https://github.com/lmorchard/ghflow/issues/161
- Worktree: /Users/lmorchard/devel/mine/gh-project-workflow/.claude/worktrees/issue-161-worktree-setup-and-draft-pr
- Branch: issue-161-worktree-setup-and-draft-pr
- Base: origin/main at ecb43cffbeb5bf1c6475c6056c542ef0cf727582
- Next action: implement the facts-file `worktree:` declaration, then the runner's draft publication.

## Scope

Issue #161 has two mechanics that a session still performs:

1. Worktree setup: a machine-readable declaration in `.ghflow/project.md` that `worktree create` applies. The prose stays as the human explanation.
2. Publication: the runner pushes a branch that the session committed to but did not publish, and opens the draft PR.

Acceptance: identical setup for every child in a run; committed work is never invisible; a project with no declaration keeps today's behavior.

## Decisions

- The declaration lives in the existing frontmatter as a `worktree:` mapping with `copy:` and `setup:` lists. The file already uses frontmatter for `written` and `sources`, so this adds no second format.
- `worktree create` reads the declaration from the primary checkout and applies it. A caller's explicit `--copy` or `--setup` replaces the declaration, so a direct caller keeps control.
- A malformed declaration refuses the worktree write and reports the error; silently skipping it would produce the varying setup the issue describes.
- The runner owns publication. After an implementation session it pushes committed work and opens a draft PR when the issue has no open PR. The session keeps its content role.
- `pr create` is a CLI write like the other PR commands: it confirms identity, refuses an existing open PR for the head branch, and reads back the URL, draft state, head, base, title, and body.

## Checks

- Baseline `make check` at `ecb43cf`: green, 129 tests.
- `make check` after the implementation: green. `cli/test_ghflow.py` and `scripts/test_run_queue.py` cover the declaration parser, the facts output, the worktree application and refusal paths, `pr create`, and the runner publication path.

## Log

- `parse_facts_worktree` reads the `worktree:` frontmatter mapping. `facts` reports `project_facts.worktree` and `worktree_errors`.
- `worktree create` applies the declaration when the caller gives no `--copy`/`--setup`, reports `worktree_setup`, and refuses a malformed declaration with exit 2 before writing anything. The runner logs the applied declaration and tells the session not to repeat it.
- `pr create` confirms identity, refuses an existing open PR for the head branch with exit 3, creates the PR, and reads back the URL, draft state, head and base branches, title, body, and the expected head.
- `publish_committed` runs after each implementation session. It counts commits against the PR base (the preceding branch for a stacked PR), pushes the branch, and opens a draft PR with the commit list. A session that published its own PR keeps it.
