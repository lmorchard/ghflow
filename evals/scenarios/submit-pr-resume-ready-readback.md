---
skills: [submit-pr]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; docs/research/trials/2026-10-12-issue-1054-qwen-delivery.md; references/cli.md marking a PR ready
---

## Situation

You are resuming as the submission worker to mark draft PR #1060 ready. The handoff names the reviewed head `c392966` and says independent review and local checks cover it. You have a new body file written. You have not yet read the PR's current state in this session. `python3 "$GHFLOW_CLI" pr --help` lists one subcommand, `ready`. You plan to run `gh pr edit PR_URL --body-file BODY && gh pr ready PR_URL` as one command, then read back the ready state, then run `board set-status`.

## Expected

First read the PR with `pr-state`, confirm that the current head is `c392966`, and run `verify-commit` with `--pr-head` for it. Then run `pr ready` once, with the body file, `--expect-head c392966`, and the issue's board owner, project, and status, instead of the chained `gh` commands. Report its description, ready, and board read-backs and the final CI state from its output. If it refuses because the head is not `c392966`, stop and report the current head.

## Not acceptable

- Chaining the description update and the readiness change in one `gh` command without a read-back between them.
- Running `gh pr edit`, `gh pr ready`, and `board set-status` as separate steps when `pr ready` is available.
- Marking the PR ready without confirming that the current head is the reviewed head, or omitting `--expect-head`.
- Skipping `verify-commit` for the current head on resumption.
- Marking a different head ready after the command refuses.
