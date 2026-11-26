---
name: ghflow
description: Prepare GitHub issues, implement selected issues, review changes, submit PRs, address feedback, and coordinate explicitly requested delivery. Use for Git and GitHub project tasks, including requests to tackle or deliver an issue. Merge requires explicit authorization; do not select backlog work unless requested.
---

# GitHub workflow

Prepare GitHub issues, implement selected issues, review changes, submit PRs, address feedback, and coordinate delivery. This repository provides specialized skills for distinct agent roles:

* **[ghflow-build](skills/build/SKILL.md)** / **[ghflow-build-slim](skills/build-slim/SKILL.md)**: Issue builder — code changes, tests, local test gates (`make check`), and local commits in an isolated worktree. The `slim` variant inlines all operative rules for lightweight local models.
* **[ghflow-review](skills/review/SKILL.md)** / **[ghflow-review-slim](skills/review-slim/SKILL.md)**: Independent change reviewer — diff inspection against issue requirements, gate verification, and structured review verdicts. Strictly read-only.
* **[ghflow-define](skills/define/SKILL.md)**: Issue definition — user interviews, technical specifications, and structured issue filing.
* **[ghflow-coord](skills/coord/SKILL.md)**: Project orchestration — parent epics, Ready queue delivery, board triage sweeps, and queue runner automation.

Before choosing how to execute an operation, apply [Execution mode](references/shared/coordination.md#execution-mode). In single-session mode with a local model, execute authorized operations directly without subagents.

## Locate the source and tools

Set `GHFLOW_CLI` to the absolute path of `cli/ghflow.py` in the source checkout root:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help
```

For symbol discovery and code navigation, use `tags brief` for compact definitions and file outlines, `tags find --refs` for references, and `tags outline` for file structure:
```sh
python3 "$GHFLOW_CLI" tags brief <symbol>...
python3 "$GHFLOW_CLI" tags find <symbol> --refs
python3 "$GHFLOW_CLI" tags outline <file>
```

Open shared references when their conditions apply: [Authorization](references/shared/authorization.md) when permission or scope boundaries arise; [Evidence](references/shared/evidence.md) before reporting results; [Decisions](references/shared/decisions.md) when a choice is missing; [Agent identity](references/shared/identity.md) before Git or GitHub writes; [GitHub writes](references/shared/github-writes.md) before mutating records.

## Select the requested operation

Match the user's explicit request to the operation below:

### Single-issue delivery operations

| Request | Task reference | Role skill |
|---|---|---|
| Implement an issue through local commits | [implement-issue](references/tasks/implement-issue.md) | [ghflow-build](skills/build/SKILL.md) |
| Independently review code changes | [review-changes](references/tasks/review-changes.md) | [ghflow-review](skills/review/SKILL.md) |
| Address PR feedback and repair CI | [address-pr-review](references/tasks/address-pr-review.md) | [ghflow-build](skills/build/SKILL.md) |
| Resolve a PR that conflicts with its base | [repair-conflict](references/tasks/repair-conflict.md) | [ghflow-build](skills/build/SKILL.md) |
| Publish committed changes as a PR | [submit-pr](references/tasks/submit-pr.md) | [ghflow-build](skills/build/SKILL.md) |
| Deliver or tackle one selected issue | [express-issue](references/tasks/express-issue.md) | [ghflow-build](skills/build/SKILL.md) |
| Define an idea or issue, including draft-only work | [define-issue](references/tasks/define-issue.md) | [ghflow-define](skills/define/SKILL.md) |
| Settle issue decisions with the user | [interview-issue](references/tasks/interview-issue.md) | [ghflow-define](skills/define/SKILL.md) |
| Publish a reviewed issue draft | [file-issue](references/tasks/file-issue.md) | [ghflow-define](skills/define/SKILL.md) |
| Reassess an existing issue | [reconsider-issue](references/tasks/reconsider-issue.md) | [ghflow-define](skills/define/SKILL.md) |
| Merge an explicitly authorized PR | [merge-pr](references/tasks/merge-pr.md) | — |

### Diagnosis operations

| Request | Task reference |
|---|---|
| Diagnose an exported OpenCode session | [diagnose-session](references/tasks/diagnose-session.md) |

### Portfolio and queue orchestration

| Request | Task reference | Role skill |
|---|---|---|
| Deliver an agreed parent issue (epic) | [deliver-parent-issue](references/tasks/deliver-parent-issue.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Deliver an explicitly requested Ready queue | [burndown-ready-queue](references/tasks/burndown-ready-queue.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Stage issues into the Ready queue | [curate-ready-queue](references/tasks/curate-ready-queue.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Split a broad parent into children | [decompose-parent-issue](references/tasks/decompose-parent-issue.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Group related issues under themes | [bundle-issues](references/tasks/bundle-issues.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Assess a requested set of open issues | [triage-issues](references/tasks/triage-issues.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Prioritize a requested board scope | [sweep-prioritize](references/tasks/sweep-prioritize.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Resolve issues needing input | [sweep-needs-input](references/tasks/sweep-needs-input.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Define accepted issues | [sweep-needs-definition](references/tasks/sweep-needs-definition.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Return unblocked issues to definition | [sweep-blocked](references/tasks/sweep-blocked.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Audit closed issues | [sweep-audit-closed](references/tasks/sweep-audit-closed.md) | [ghflow-coord](skills/coord/SKILL.md) |
| Write or refresh the project facts file | [prepare-project-facts](references/tasks/prepare-project-facts.md) | [ghflow-coord](skills/coord/SKILL.md) |

## Execute and hand off

For sustained work or findings that would be costly to reconstruct, apply [Task notes](references/shared/task-notes.md). On resumption or after context compaction, read the task's existing notes before repeating research or reopening decisions. Follow the selected reference's scope and stopping point.
