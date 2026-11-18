---
name: ghflow
description: Implement, test, review, and address feedback for a single assigned GitHub issue in an isolated worktree. Use when tackling, implementing, or reviewing an assigned issue. Merge requires explicit authorization.
---

# GitHub issue delivery

Implement, review, address feedback, and prepare pull requests for an assigned GitHub issue or pull request. The worker operates in an isolated worktree, focuses strictly on the code changes and test gates (`make check`) required for the issue, and creates local commits. It does not manage boards, reschedule tasks, or close epics.

Before choosing how to execute an operation, apply [Execution mode](references/shared/coordination.md#execution-mode). In single-session mode with a local model, execute authorized operations directly without subagents.

## Locate the source and tools

Set `GHFLOW_CLI` to the absolute path of `cli/ghflow.py` in the source checkout root:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help
```

For symbol discovery and code navigation, use `tags find` and `tags outline` for instant definition lookups across git-tracked source files:

```sh
python3 "$GHFLOW_CLI" tags find <symbol>
python3 "$GHFLOW_CLI" tags outline <file>
```

Open shared references when their conditions apply: [Authorization](references/shared/authorization.md) when permission or scope boundaries arise; [Evidence](references/shared/evidence.md) before reporting results; [Decisions](references/shared/decisions.md) when a choice is missing; [Agent identity](references/shared/identity.md) before Git or GitHub writes; [GitHub writes](references/shared/github-writes.md) before mutating records.

## Select the delivery operation

Match the assigned task to the single-issue delivery operation below:

| Request | Task reference |
|---|---|
| Implement an issue through local commits | [implement-issue](references/tasks/implement-issue.md) |
| Independently review code changes | [review-changes](references/tasks/review-changes.md) |
| Address PR feedback and repair CI | [address-pr-review](references/tasks/address-pr-review.md) |
| Publish committed changes as a PR | [submit-pr](references/tasks/submit-pr.md) |
| Deliver or tackle one selected issue | [express-issue](references/tasks/express-issue.md) |
| Define an idea or issue, including draft-only work | [define-issue](references/tasks/define-issue.md) |
| Settle issue decisions with the user | [interview-issue](references/tasks/interview-issue.md) |
| Publish a reviewed issue draft | [file-issue](references/tasks/file-issue.md) |
| Reassess an existing issue | [reconsider-issue](references/tasks/reconsider-issue.md) |
| Merge an explicitly authorized PR | [merge-pr](references/tasks/merge-pr.md) |

For multi-issue roadmaps, parent epics, triage sweeps, queue management, or automated queue burndowns, use the companion orchestration skill [ghflow-coord](coord/SKILL.md).

## Execute and hand off

Work exclusively inside the assigned worktree. Preserve unrelated changes, run the required project checks (`make check`), and commit under the configured agent identity.

For sustained work or findings that would be costly to reconstruct, apply [Task notes](references/shared/task-notes.md). Return the committed head SHA, test results with their commits, evidence limits, and remaining work.
