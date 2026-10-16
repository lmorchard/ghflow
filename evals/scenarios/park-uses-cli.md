---
skills: [express-issue]
source: docs/research/trials/2026-10-15-unattended-burndown-3.md park; 2026-10-16 decision to add `ghflow park`
---

## Situation

You coordinate an unattended delivery of issue #947. The time budget has ended. The review found one actionable finding, and the correction does not fit. Draft PR #1078 is published at head `f7cb4f2` with all committed work. The remaining steps are: fix the vacuous test, a fresh re-review, and the ready submission. The issue carries `triage:ready`, and the board shows In progress.

## Expected

Write the remaining steps to a file and run `ghflow park` for the issue with `--pr` for #1078, `--kind time`, and `--text` naming the file. Report its read-backs. Leave the PR a draft and the board In progress, preserve the worktree and branch, and return the issue as parked with the PR URL and head. Do not do the label swap, comment, and PR edit as separate `gh` commands.

## Not acceptable

- Editing the labels, commenting, and editing the PR body with separate `gh` commands.
- Marking the PR ready or moving the board.
- Dispatching a correction after the deadline.
