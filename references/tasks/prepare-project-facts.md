# Prepare the project facts

Write or refresh the project facts file, `.ghflow/project.md`, in the subject repository: one screen of stable facts that workers otherwise rediscover in every session. The file holds only what `ghflow facts` cannot read. This task ends with the file written and committed in a worktree, and published only when the flow authorizes it. It does not implement issues or change other files.

Apply [Authorization](../shared/authorization.md) before you write to the subject repository, and [Evidence](../shared/evidence.md) to every fact you record. When project conventions conflict or a fact needs the user's choice, apply [Decisions](../shared/decisions.md).

## Decide whether the file needs work

Run `python3 "$GHFLOW_CLI" facts` from the subject checkout, as [CLI results](../cli.md#reading-project-facts) describes. If `project_facts.present` is false, write the file. If `stale_sources` is not empty, refresh the sections drawn from those sources and update their hashes. When a changed source alters no fact, update its hash alone and say so. If the file is present and no source is stale, report that and stop; a new session alone is no reason to rewrite it.

A queue coordinator dispatches this task under [Check the project facts](burndown-ready-queue.md#check-the-project-facts) when `facts` reports stale sources before a burndown. That handoff authorizes the refresh and a ready PR for it. Publish the PR ready, not as a draft, with the publication steps in [submit-pr](submit-pr.md). The facts file needs no independent agent review: the user reviews it in the PR, so submit-pr's review conditions do not apply, and you do not request or wait for a review. Do not merge it, and return the worktree path of the refreshed file so the coordinator can point every worker at it.

## Read the sources

Read the instruction files that `facts` lists, the Makefile or task runner, the CI workflows, the test configuration such as `conftest.py` files and `pyproject.toml` or `package.json` scripts, and the environment example file. Record each source path that supplies a fact, for the frontmatter.

## Write one screen of stable facts

Keep the file under about 40 lines. Use these sections, and omit a section that does not apply:

- **Worktree setup**: the exact commands to prepare a worktree for this project, such as the dependency install, the environment file copy, and a port or data-directory setting.
- **Gates**: the format, lint, type, test, and full-check commands, in the order the project runs them, and how long a full suite takes when the instructions say or you measured it.
- **Generated files**: each generated file, its source of truth, the regenerate command, and the drift check that fails on a hand edit.
- **Test layout**: where shared fixtures live, how to run one test or one file, and markers or suites to avoid in a worktree.
- **Session notes**: the notes directory convention and whether notes are committed.
- **Never run**: dev servers, deploys, migrations, or other commands the instructions forbid in a worktree.
- **Commits and PRs**: the subject style, the PR template path if any, and how closing references are used.
- **Board**: the project board owner and number and the Status names the flow uses, when the instructions name them.

Write facts, not procedures that ghflow already owns. Leave live state out: the default branch head, local or remote branches, open PRs, board status of an issue, worktrees, and identity readiness change between sessions, and `ghflow facts --issue ISSUE_URL` reads them on demand. End the file with that command as the way to get live state.

Start the file with this frontmatter. Use `git hash-object PATH` for each hash:

```text
---
ghflow_project_facts: 1
written: YYYY-MM-DD
sources:
  - AGENTS.md BLOB_HASH
  - Makefile BLOB_HASH
---
```

`facts` later compares these hashes with the current files and reports the changed ones as stale, so list every file that supplied a fact.

## Check the file

Make sure that each fact comes from a source you read or a command you ran, and that a quoted command exists in the project. Run `python3 "$GHFLOW_CLI" facts` again and confirm `present` is true, `sources` matches the list, and `stale_sources` is empty. Commit the file in the worktree following the project's commit conventions.

## Return

Return the file path in the worktree and its line count, the sources recorded, the sections changed or the hashes updated alone, the facts you could not establish and why, the PR URL when published, and the next action. If the project has an instructions file, propose one line in it that points to the facts file, and leave that edit to the user unless the flow authorizes it.
