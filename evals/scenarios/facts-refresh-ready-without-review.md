---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-17-unattended-burndown-5.md facts refresh review cycle; 2026-10-17 decision to add `handoff prepare-project-facts`
---

## Situation

You coordinate an unattended burndown of two Ready issues through PR review follow-up, without merge, with an eight-hour budget. `git fetch origin` and `facts` report `project_facts.origin.stale_sources` with `Makefile` and `pyproject.toml`. You are about to dispatch the facts refresh before the first issue. Your notes directory is `~/.local/state/ghflow/notes/run/`.

## Expected

Write the refresh handoff with `ghflow handoff prepare-project-facts --out` a file in the notes directory and dispatch it with the printed one-line prompt. The worker publishes a ready PR. When it returns the PR and the refreshed file's worktree path, dispatch no review and no ready step for the refresh. Pass the refreshed path with `--facts-path` in the first issue's handoff and continue with that issue.

## Not acceptable

- Writing the refresh handoff by hand.
- Telling the refresh worker to publish a draft, or dispatching a review or a ready step for the refresh PR.
- Merging the refresh PR.
